#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import flash
from flask import session
from flask import request
from flask import url_for
from flask import redirect
from flask import Blueprint
from flask import render_template

from steamcommerce_tasks import app

from steamcommerce_api.api import user
from steamcommerce_api.api import product
from steamcommerce_api.api import message
from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import notification
from steamcommerce_api.api import creditrequest
from steamcommerce_api.api import requests_tools

import constants

from forms import admin
from utils import route_decorators
from forms import request_message

import datetime

admin_view = Blueprint('admin.views', __name__)


@admin_view.route('/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_root():
    logs = adminlog.AdminLog().get_logs(1)

    params = {
        'logs': logs
    }

    return render_template('admin/views/dashboard.html', **params)


@admin_view.route('/pedidos')
@admin_view.route('/pedidos/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_requests():
    user_id = int(request.args.get('user')) or session.get('user')

    userrequests = userrequest.UserRequest().get_paid_userrequests()
    paidrequests = paidrequest.PaidRequest().get_paid_paidrequests()
    informed = userrequest.UserRequest().get_informed_userrequests()

    resumes_all = requests_tools.RequestsTools().resume_all(
        userrequests,
        paidrequests
    )

    resumes_informed = requests_tools.RequestsTools().resume_all(
        informed,
        []
    )

    assigned_userrequests = []
    assigned_paidrequests = []

    for userrequest_data in userrequests:
        if (
            userrequest_data.get('assigned') and
            userrequest_data.get('assigned').get('id') == user_id
        ):
            assigned_userrequests.append(userrequest_data)

    for paidrequest_data in paidrequests:
        if (
            paidrequest_data.get('assigned') and
            paidrequest_data.get('assigned').get('id') == user_id
        ):
            assigned_paidrequests.append(paidrequest_data)

    resumes_assigned = requests_tools.RequestsTools().resume_all(
        assigned_userrequests,
        assigned_paidrequests
    )

    counters = {
        'userrequests': len(userrequests),
        'paidrequests': len(paidrequests),
        'informed': len(informed)
    }

    date_now = datetime.datetime.now()

    params = {
        'userrequests': userrequests,
        'paidrequests': paidrequests,
        'resumes_informed': resumes_informed,
        'resumes_assigned': resumes_assigned,
        'informed': informed,
        'counters': counters,
        'date_now': date_now,
        'resumes_all': resumes_all
    }

    return render_template('admin/views/requests.html', **params)


@admin_view.route('/historial/<custom_id:history_identifier>')
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_request(history_identifier):
    request_id = int(history_identifier['number'])
    request_type = history_identifier['type']
    message_form = request_message.MessageForm()

    if request_type == u'A':
        try:
            history_request = userrequest.UserRequest().get_userrequest_by_id(
                request_id
            )
        except:
            return redirect(url_for('admin.views.admin_requests'))

        history_items = history.History().get_request_history(
            history_request['id'], 1
        )

        messages = message.Message().get_messages_by_userrequest(
            history_request['id']
        )
    elif request_type == u'B':
        try:
            history_request = creditrequest.CreditRequest().\
                get_creditrequest_by_id(
                    request_id
                )
        except:
            return redirect(url_for('admin.views.admin_requests'))

        history_items = history.History().get_request_history(
            history_request['id'], 2
        )

        messages = message.Message().get_messages_by_creditrequest(
            history_request['id']
        )

    elif request_type == u'C':
        try:
            history_request = paidrequest.PaidRequest().get_paidrequest_by_id(
                request_id
            )
        except:
            return redirect(url_for('admin.views.admin_requests'))

        history_items = history.History().get_request_history(
            history_request['id'], 3
        )

        messages = message.Message().get_messages_by_paidrequest(
            history_request['id']
        )

    admins = user.User().get_admins()

    message_form.request_id.data = history_request['id']
    message_form.request_type.data = request_type
    message_form.to_user.data = history_request['user']['id']

    params = {
        'admins': admins,
        'messages': messages,
        'request': history_request,
        'message_form': message_form,
        'request_type': request_type,
        'history_items': history_items,
    }

    return render_template('admin/views/history.html', **params)


@admin_view.route('/message/add/', methods=['POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_message_add():
    form = request_message.MessageForm(request.form)

    redirect_url = url_for(
        'admin.views.admin_request',
        history_identifier=('{0}-{1}').format(
            form.request_type.data,
            form.request_id.data
        )
    )

    if not form.validate():
        return redirect(redirect_url)

    data = {
        'user': session.get('user'),
        'date': datetime.datetime.now()
    }

    request_id = int(form.request_id.data)

    if form.request_type.data == 'A':
        userrequest_data = userrequest.UserRequest().get_id(request_id)
        owner_id = userrequest_data.user.id

        data.update({'userrequest': form.request_id.data})
    elif form.request_type.data == 'B':
        creditrequest_data = creditrequest.CreditRequest().get_id(request_id)
        owner_id = creditrequest_data.user.id

        data.update({'creditrequest': form.request_id.data})
    elif form.request_type.data == 'C':
        paidrequest_data = paidrequest.PaidRequest().get_id(request_id)
        owner_id = paidrequest_data.user.id

        data.update({'paidrequest': form.request_id.data})

    data.update(**form.data)

    message.Message().push(**data)

    notififcation_params = data
    notififcation_params.pop('date')

    notification.Notification().push(
        owner_id,
        constants.NOTIFICATION_MESSAGE_RECEIVED,
        **notififcation_params
    )

    return redirect(redirect_url)


@admin_view.route('/queue/price/add/<int:product_id>/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def queue_price_add(product_id):
    app.calc_product_price.delay(product_id)
    product_data = product.Product().get_product_by_id(product_id)

    flash(u'Producto añadido a la cola de precios')

    app_id = product_data.get('app_id') or product_data.get('sub_id')

    return redirect(
        url_for(
            'views.store.store_app_id', app_id=app_id
        )
    )


@admin_view.route('/steam/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def queue_product_add():
    if request.method == 'GET':
        form = admin.SteamProduct()

        return render_template('admin/panel/generic-form.html', form=form)
    elif request.method == 'POST':
        form = admin.SteamProduct(request.form)

        if not form.validate():
            return render_template('admin/panel/generic-form.html', form=form)

        new_form = admin.SteamProduct()

        if form.app_id.data:
            try:
                product.Product().get_app_id(form.app_id.data)

                flash(u'La AppID ya existe en la base de datos')

                return render_template(
                    'admin/panel/generic-form.html', form=new_form
                )
            except:
                pass

            app.add_product_to_store.delay(app_id=form.app_id.data)

            flash(u'AppID añadido a la cola de adición de productos')

            return render_template(
                'admin/panel/generic-form.html', form=new_form
            )
        elif form.sub_id.data:
            try:
                product.Product().get_sub_id(form.sub_id.data)

                flash(u'La SubID ya existe en la base de datos')

                return render_template(
                    'admin/panel/generic-form.html', form=new_form
                )
            except:
                pass

            app.add_product_to_store.delay(sub_id=form.sub_id.data)

            flash(u'SubID añadido a la cola de adición de productos')

            return render_template(
                'admin/panel/generic-form.html', form=new_form
            )

        flash(u'Se requiere AppID o SubID')

        return render_template(
            'admin/panel/generic-form.html', form=new_form
        )
