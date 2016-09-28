#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import Blueprint
from flask import render_template

from steamcommerce_tasks.tasks import product as product_task

from steamcommerce_api.api import user
from steamcommerce_api.api import cart
from steamcommerce_api.api import crawler
from steamcommerce_api.api import steam
from steamcommerce_api.api import product
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import testimonial
from steamcommerce_api.api import notification
from steamcommerce_api.api import creditrequest

import re
import config
import datetime

from oid import oid
from forms import user as user_form
from utils import route_decorators


user_view = Blueprint('views.user', __name__)


@user_view.route('/user/<username>')
@route_decorators.is_logged_in
@route_decorators.is_admin
def user_admin_profile(username):
    try:
        user_data = user.User().get_by_username(username)
    except user.User().model.DoesNotExist:
        error = {
            'title': 'Usuario inexistente',
            'content': 'El usuario no existe :('
        }

        return render_template('views/error.html', **error)

    notifications = notification.Notification().get_for_user(user_data['id'])

    userrequests = userrequest.UserRequest().get_by_user_id(
        user_data['id']
    )

    creditrequests = creditrequest.CreditRequest().get_by_user_id(
        user_data['id']
    )

    paidrequests = paidrequest.PaidRequest().get_by_user_id(
        user_data['id']
    )

    form = user_form.ProfileForm(obj=user_data)

    params = {
        'form': form,
        'user': user_data,
        'userrequests': userrequests,
        'paidrequests': paidrequests,
        'notifications': notifications,
        'creditrequests': creditrequests
    }

    return render_template('views/user/profile.html', **params)


@user_view.route('/login')
@user_view.route('/login/')
@route_decorators.not_logged_in
@oid.loginhandler
def user_login():
    return oid.try_login(config.STEAM_OPENID_URL)


@user_view.route('/registro', methods=['GET', 'POST'])
@user_view.route('/registro/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
@route_decorators.has_no_email
def user_register():
    user_id = session.get('user')
    curr_user = user.User().get_by_id(user_id)

    if request.method == 'GET':
        form = user_form.RegisterForm()

        return render_template(
            'views/user/register.html',
            user=curr_user,
            form=form
        )
    elif request.method == 'POST':
        form = user_form.RegisterForm(request.form)

        if not form.validate():
            return render_template(
                'views/user/register.html',
                user=curr_user,
                form=form
            )

        user.User().set_email(user_id, None, form.email.data)
        session['email'] = form.email.data

        return redirect(url_for('views.store.store_catalog'))


@user_view.route('/logout')
@user_view.route('/logout/')
@route_decorators.is_logged_in
def user_logout():
    try:
        session.pop('user')
    except:
        pass

    try:
        session.pop('admin')
    except:
        pass

    return redirect(url_for('views.store.store_catalog'))


@user_view.route('/perfil', methods=['GET', 'POST'])
@route_decorators.is_logged_in
def user_profile():
    user_id = session.get('user')
    user_data = user.User().get_by_id(user_id)

    notifications = notification.Notification().get_user_top_notifications(
        user_id
    )

    userrequests = userrequest.UserRequest().get_by_user_id(user_id)
    creditrequests = creditrequest.CreditRequest().get_by_user_id(user_id)
    paidrequests = paidrequest.PaidRequest().get_by_user_id(user_id)

    params = {
        'user': user_data,
        'userrequests': userrequests,
        'paidrequests': paidrequests,
        'notifications': notifications,
        'creditrequests': creditrequests
    }

    if request.method == 'GET':
        form = user_form.ProfileForm(obj=user_data)
        params.update({'form': form})

    elif request.method == 'POST':
        form = user_form.ProfileForm(request.form)
        params.update({'form': form})

        if form.validate():
            if user_data['email'] != form.email.data:
                user.User().set_email(
                    user_id,
                    user_data['email'],
                    form.email.data
                )

            name = form.name.data
            last_name = form.last_name.data

            if (
                user_data['name'] != name or
                user_data['last_name'] != last_name
            ):
                user.User().set_name(user_id, name, last_name)

    return render_template('views/user/profile.html', **params)


@user_view.route('/historial/<custom_id:history_identifier>')
@route_decorators.is_logged_in
def user_history(history_identifier):
    user_id = session.get('user')

    request_type = history_identifier['type']
    request_id = int(history_identifier['number'])

    incorrect_request = {
        'title': 'El pedido no corresponde a este usuario',
        'content': u'El pedido no está asociado a esta cuenta'
    }

    if request_type == 'A':
        try:
            userrequest_data = userrequest.UserRequest().get_id(request_id)
        except userrequest.UserRequest().model.DoesNotExist:
            return render_template('views/error.html', **incorrect_request)

        if userrequest_data['user']['id'] != user_id:
            return render_template('views/error.html', **incorrect_request)

        params = {
            'request_type': request_type,
            'request_id': request_id,
            'userrequest': userrequest_data
        }

        return render_template(
            'views/user/user-history.html',
            **params
        )
    elif request_type == 'B':
        try:
            creditrequest_data = creditrequest.CreditRequest().get_id(
                request_id
            )
        except creditrequest.CreditRequest().model.DoesNotExist:
            return render_template('views/error.html', **incorrect_request)

        if creditrequest_data['user']['id'] != user_id:
            return render_template('views/error.html', **incorrect_request)

        params = {
            'request_type': request_type,
            'request_id': request_id,
            'creditrequest': creditrequest_data
        }

        return render_template(
            'views/user/user-history.html',
            **params
        )
    elif request_type == 'C':
        try:
            paidrequest_data = paidrequest.PaidRequest().get_id(request_id)
        except paidrequest.PaidRequest.DoesNotExist:
            return render_template('views/error.html', **incorrect_request)

        if paidrequest_data['user']['id'] != user_id:
            return render_template('views/error.html', **incorrect_request)

        params = {
            'request_type': request_type,
            'request_id': request_id,
            'paidrequest': paidrequest_data
        }

        return render_template(
            'views/user/user-history.html',
            **params
        )


@user_view.route('/notifications/seen/')
@route_decorators.is_logged_in
@route_decorators.as_json
def user_notifications_seen():
    user_id = session.get('user')
    notification.Notification().update_seen(user_id)

    return {'success': True}


@user_view.route('/testimonios/nuevo')
@route_decorators.is_logged_in
def user_testimonials_new():
    user_id = session.get('user')
    pending_testimonials = testimonial.Testimonial().get_unsubmited(user_id)

    return render_template(
        'views/store/new_testimonials.html',
        pending_testimonials=pending_testimonials
    )


@user_view.route('/testimonial/skip/', methods=['POST'])
@route_decorators.is_logged_in
@route_decorators.as_json
def user_testimonial_skip():
    user_id = session.get('user')
    testimonial_id = request.form.get('testimonial_id')

    if not testimonial_id:
        return ({'success': False}, 500)

    pending_testimonials = testimonial.Testimonial().get_unsubmited(
        user_id,
        excludes=['all']
    )

    testimonial_id = int(testimonial_id)

    if testimonial_id not in [x['id'] for x in pending_testimonials]:
        return ({'success': False}, 500)

    testimonial.Testimonial().update(**{
        'id': testimonial_id,
        'visible': False
    })

    return {'success': True}


@user_view.route('/testimonial/submit/', methods=['POST'])
@route_decorators.is_logged_in
@route_decorators.as_json
def user_testimonial_submit():
    user_id = session.get('user')
    testimonial_id = request.form.get('testimonial_id')
    content = request.form.get('content')

    if not testimonial_id or not content or len(content) < 10:
        return ({'success': False, 'status': 1}, 500)

    pending_testimonials = testimonial.Testimonial().get_unsubmited(
        user_id,
        excludes=['all']
    )

    testimonial_id = int(testimonial_id)

    if testimonial_id not in [x['id'] for x in pending_testimonials]:
        return ({'success': False, 'status': 2}, 500)

    testimonial.Testimonial().update(**{
        'id': testimonial_id,
        'submited': True,
        'content': content,
        'date': datetime.datetime.now()
    })

    return {'success': True}


@user_view.route('/wishlist')
@route_decorators.is_logged_in
def user_wishlist():
    user_id = session.get('user')
    curr_user = user.User().get_by_id(user_id)

    wishlist = crawler.SteamCrawler().get_user_wishlist(curr_user['steam'])

    if len(wishlist) > 0:
        if wishlist[0] is False:
            if wishlist[1] == 1:
                params = {
                    'title': 'Lista de deseados no disponible',
                    'content': 'Tu lista de deseados es privada en Steam \
<br><a target="_blank" href="http://steamcommunity.com/id/me/edit/settings">\
Editar privacidad en Steam</a><br>\
 <a href="/wishlist/retry">Refrescar lista de deseados</a>'
                }
            elif wishlist[1] == 2:
                params = {
                    'title': 'Lista de deseados no disponible',
                    'content': u'No pudimos extraer tu lista de deseados en\
Steam. ¿Contactá un administrador? \
<a target="_blank" href="https://facebook.com/ExtremeGamingSTEAM">\
Facebook ExtremeGaming</a>'
                }

            return render_template('views/error.html', **params)

    products = []

    for app_id in wishlist[:100]:
        try:
            products.append(product.Product().get_app_id(
                app_id, excludes=[
                    'product_codes',
                    'product_tags',
                    'product_specs'
                ])
            )
        except product.Product().model.DoesNotExist:
            product_task.add_product_to_store(
                app_id=app_id
            )

    params = {
        'page': 1,
        'section': 'wishlist',
        'products': products,
    }

    return render_template('views/user/wishlist.html', **params)


@user_view.route('/wishlist/retry')
@route_decorators.is_logged_in
def user_wishlist_retry():
    user_id = session.get('user')

    retries = user.User().get_wishlist_retries(user_id)

    if retries >= 5:
        params = {
            'title': u'Re-intentos excedidos',
            'content': u'Has llegado a tu limite de re-intentos de\
 lista de deseados, intentalo nuevo en unas horas'
        }

        return render_template('views/error.html', **params)

    user.User().purge_user_wishlist(user_id)

    return redirect(url_for('views.user.user_wishlist'))


@user_view.route('/user/cart/')
@route_decorators.is_logged_in
def user_cart():
    user_id = session.get('user')

    cart.Cart().process_cart(user_id)
    user_cart = cart.Cart().get_user_cart(user_id)

    params = {
        'user_cart': user_cart
    }

    return render_template('views/cart/view.html', **params)


@user_view.route('/user/notifications/')
@route_decorators.is_logged_in
def user_notifications():
    user_id = session.get('user')

    notifications = notification.Notification().get_user_top_notifications(
        user_id,
        excludes=[
            'all',
        ]
    )

    params = {
        'notifications': notifications
    }

    return render_template(
        'views/user/nav-notifications.html',
        **params
    )


@oid.after_login
def steam_after_login(resp):
    user_steam_id = re.findall(
        config.STEAM_IDENTITY_URL_REGEX,
        resp.identity_url,
        re.DOTALL
    )

    if len(user_steam_id) < 1:
        # TODO: Log event

        return redirect(url_for('views.store.store_catalog'))

    try:
        steam_user = user.User().get_by_steam64(user_steam_id[0])
    except user.User().model.DoesNotExist:
        ip_address = request.headers.get(
            'CF-Connecting-IP',
            request.remote_addr
        )

        user_id = user.User().register(user_steam_id[0], ip_address)

        session['user'] = user_id
        session['email'] = None

        return redirect(url_for('views.user.user_register'))

    if not steam_user.email or len(steam_user.email) < 1:
        session['user'] = steam_user.id
        session['email'] = None

        return redirect(url_for('views.user.user_register'))

    if steam_user.is_banned:
        return render_template(
            'views/user/banned.html',
            user=steam_user
        )

    session['user'] = steam_user.id
    session['email'] = steam_user.email

    if steam_user.admin:
        session['admin'] = True

    player_info = steam.Steam().get_player_summaries(user_steam_id[0])

    if player_info:
        user.User().update(**{
            'id': steam_user.id,
            'avatar_url': player_info.get('avatarfull')
        })

    return redirect(
        request.args.get(
            'next',
            url_for('views.store.store_catalog')
        )
    )
