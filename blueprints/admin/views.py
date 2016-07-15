#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import flash
from flask import session
from flask import request
from flask import url_for
from flask import redirect
from flask import Blueprint
from flask import render_template

from steamcommerce_tasks.tasks import product as product_task

from steamcommerce_api import config

from steamcommerce_api.api import user
from steamcommerce_api.api import product
from steamcommerce_api.api import message
from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import notification
from steamcommerce_api.api import cuentadigital
from steamcommerce_api.api import creditrequest
from steamcommerce_api.api import requests_tools

import constants

import json
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


@admin_view.route('/resumen', methods=['GET', 'POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_resume():
    user_id = session.get('user')
    user_data = user.User().get_by_id(user_id)

    params = {
        'user': user_data,
        'now_date': datetime.datetime.now(),
    }

    if request.method == 'GET':
        form = admin.ResumeForm()
        params.update({'form': form})
    elif request.method == 'POST':
        form = admin.ResumeForm(request.form)

        if not form.validate():
            params.update({'form': form})
            return render_template('admin/views/resumes.html', **params)

        userrequests = []
        paidrequests = []

        if form.userrequests.data:
            _userrequests = userrequest.UserRequest().\
                _get_accepted_between_dates(
                    user_id,
                    form.start_date.data,
                    form.end_date.data,
                    config.CUENTADIGITAL_NIN_ID
                )

            for userrequest_obj in _userrequests:
                fee = cuentadigital.CuentaDigital().calc_fee(
                    userrequest_obj.price
                )

                userrequest_data = {
                    'fee': fee,
                    'price': userrequest_obj.price,
                    'request': userrequest_obj
                }

                userrequests.append(userrequest_data)

        if form.paidrequests.data:
            _paidrequests = paidrequest.PaidRequest().\
                _get_accepted_between_dates(
                    user_id,
                    form.start_date.data,
                    form.end_date.data,
                    config.CUENTADIGITAL_NIN_ID
                )

            for paidrequest_obj in _paidrequests:
                fee = cuentadigital.CuentaDigital().calc_fee(
                    paidrequest_obj.price
                )

                paidrequest_data = {
                    'fee': fee,
                    'price': paidrequest_obj.price,
                    'request': paidrequest_obj
                }

                paidrequests.append(paidrequest_data)

        total_income = sum([x['price'] for x in userrequests])
        total_income += sum([x['price'] for x in paidrequests])

        fees = sum([x['fee'] for x in userrequests])
        fees += sum([x['fee'] for x in paidrequests])

        params.update({
            'form': form,
            'fees': fees,
            'total_income': total_income,
            'userrequests': userrequests,
            'paidrequests': paidrequests,
        })

    return render_template('admin/views/resumes.html', **params)


@admin_view.route('/pedidos')
@admin_view.route('/pedidos/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_requests():
    user_id = int(request.args.get('user', 0)) or session.get('user')

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

    cart_json = []
    inventory_json = {}

    assigned_userrequests = []
    assigned_paidrequests = []

    for userrequest_data in userrequests:
        if (
            not userrequest_data.get('assigned') or
            userrequest_data.get('assigned').get('id') != user_id
        ):
            continue

        assigned_userrequests.append(userrequest_data)

        inventory_json['A-{}'.format(userrequest_data.get('id'))] = {
            'relations': []
        }

        relations = inventory_json[
            'A-{}'.format(userrequest_data.get('id'))
        ].get(
            'relations'
        )

        for relation in userrequest_data.get('relations'):
            relations.append(
                {
                    'app': relation.get('product').get('app_id'),
                    'sub': relation.get('product').get('sub_id')
                }
            )

            if relation.get('product').get('store_sub_id'):
                cart_json.append({
                    'subid': relation.get('product').get('store_sub_id'),
                    'from_app': relation.get('product').get('app_id'),
                    'name': relation.get('product').get('title')
                })

    for paidrequest_data in paidrequests:
        if (
            not paidrequest_data.get('assigned') or
            paidrequest_data.get('assigned').get('id') != user_id
        ):
            continue

        assigned_paidrequests.append(paidrequest_data)

        inventory_json['C-{0}'.format(paidrequest_data.get('id'))] = {
            'relations': []
        }

        relations = inventory_json[
            'C-{}'.format(paidrequest_data.get('id'))
        ].get(
            'relations'
        )

        for relation in paidrequest_data.get('relations'):
            relations.append(
                {
                    'app': relation.get('product').get('app_id'),
                    'sub': relation.get('product').get('sub_id')
                }
            )

            if relation.get('product').get('store_sub_id'):
                cart_json.append({
                    'subid': relation.get('product').get('store_sub_id'),
                    'from_app': relation.get('product').get('app_id'),
                    'name': relation.get('product').get('title')
                })

    cart_json = json.dumps(cart_json)
    inventory_json = json.dumps(inventory_json)

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
        'cart_json': cart_json,
        'resumes_all': resumes_all,
        'inventory_json': inventory_json,
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

    notification_params = data
    notification_params.pop('date')
    notification_params.pop('user')

    notification.Notification().push(
        owner_id,
        constants.NOTIFICATION_MESSAGE_RECEIVED,
        **notification_params
    )

    return redirect(redirect_url)


@admin_view.route('/queue/price/add/<int:product_id>/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def queue_price_add(product_id):
    product_task.product_price_queue.delay(product_id)
    product_data = product.Product().get_product_by_id(product_id)

    flash(u'Producto añadido a la cola de precios')

    app_id = product_data.get('app_id') or product_data.get('sub_id')

    return redirect(
        url_for(
            'views.store.store_app_id', app_id=app_id
        )
    )


@admin_view.route('/queue/assets/add/<int:product_id>/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def queue_assets_add(product_id):
    product_task.get_product_assets.delay(product_id)
    product_data = product.Product().get_product_by_id(product_id)

    flash(u'Producto añadido a la cola de recursos')

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

            product_task.add_product_to_store.delay(app_id=form.app_id.data)

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

            product_task.add_product_to_store.delay(sub_id=form.sub_id.data)

            flash(u'SubID añadido a la cola de adición de productos')

            return render_template(
                'admin/panel/generic-form.html', form=new_form
            )

        flash(u'Se requiere AppID o SubID')

        return render_template(
            'admin/panel/generic-form.html', form=new_form
        )
