#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import user
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
    notifications = notification.Notification().get_for_user(user_id)

    userrequests = userrequest.UserRequest().get_user_userrequests(user_id)
    creditrequests = creditrequest.CreditRequest().get_user_creditrequests(
        user_id
    )
    paidrequests = paidrequest.PaidRequest().get_user_paidrequests(user_id)

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
            if user_data.email != form.email.data:
                user.User().set_email(
                    user_id,
                    user_data.email,
                    form.email.data
                )

            name = form.name.data
            last_name = form.last_name.data

            if user_data.name != name or user_data.last_name != last_name:
                user.User().set_name(user_id, name, last_name)

    return render_template('views/user/profile.html', **params)


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
    pending_testimonials = testimonial.Testimonial().\
        get_user_pending_testimonials(user_id)

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
        user_id, lazy=True
    )

    testimonial_id = int(testimonial_id)

    if testimonial_id not in [x for x in pending_testimonials]:
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
        return ({'success': False}, 500)

    pending_testimonials = testimonial.Testimonial().get_unsubmited(
        user_id, lazy=True
    )

    testimonial_id = int(testimonial_id)

    if testimonial_id not in [x for x in pending_testimonials]:
        return ({'success': False}, 500)

    testimonial.Testimonial().update(**{
        'id': testimonial_id,
        'submited': True,
        'content': content,
        'date': datetime.datetime.now()
    })

    return {'success': True}


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

        return redirect(url_for('views.user.user_register'))

    if not steam_user.email or len(steam_user.email) < 1:
        session['user'] = steam_user.id

        return redirect(url_for('views.user.user_register'))

    if steam_user.is_banned:
        return render_template('views/user/banned.html', user=steam_user)

    session['user'] = steam_user.id

    if steam_user.admin:
        session['admin'] = True

    return redirect(
        request.args.get(
            'next',
            url_for('views.store.store_catalog')
        )
    )
