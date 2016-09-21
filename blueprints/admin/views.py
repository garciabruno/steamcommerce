#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import os

from flask import flash
from flask import session
from flask import request
from flask import url_for
from flask import redirect
from flask import Blueprint
from flask import render_template

from steamcommerce_tasks.tasks import product as product_task
from steamcommerce_tasks.tasks import sales as sales_tasks

from steamcommerce import config as app_config
from steamcommerce_api import config

from steamcommerce_api.controllers import bot

from steamcommerce_api.api import user
from steamcommerce_api.api import slider
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

from forms import admin
from utils import route_decorators
from forms import request_message

import json
import datetime

admin_view = Blueprint('admin.views', __name__)


@admin_view.route('/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_root():
    logs = adminlog.AdminLog().get_logs(1, excludes=['product_codes'])

    params = {
        'logs': logs
    }

    return render_template('admin/views/dashboard.html', **params)


@admin_view.route('/activity/load/', methods=['POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_load_activity():
    page = int(request.form.get('page'))

    logs = adminlog.AdminLog().get_logs(page)

    params = {
        'logs': logs
    }

    return render_template('admin/views/activity.html', **params)


@admin_view.route('/resumen', methods=['GET', 'POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_resume():
    params = {
        'now_date': datetime.datetime.now(),
    }

    if request.method == 'GET':
        form = admin.ResumeForm()
        params.update({'form': form})
    elif request.method == 'POST':
        form = admin.ResumeForm(request.form)

        if not form.validate():
            params.update({'form': form})
            return render_template(
                'admin/views/resumes.html',
                **params
            )

        userrequests = []
        paidrequests = []

        user_id = form.user_id.data

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

    userrequests = userrequest.UserRequest().get_paid()
    paidrequests = paidrequest.PaidRequest().get_paid()
    informed = userrequest.UserRequest().get_informed()

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

    for _userrequest in userrequests:
        if (
            _userrequest.get('assigned') and
            _userrequest.get('assigned').get('id') == user_id
        ):
            assigned_userrequests.append(_userrequest)

    for _paidrequest in paidrequests:
        if (
            _paidrequest.get('assigned') and
            _paidrequest.get('assigned').get('id') == user_id
        ):
            assigned_paidrequests.append(_paidrequest)

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
            history_request = userrequest.UserRequest().get_id(
                request_id
            )
        except:
            return redirect(url_for('admin.views.admin_requests'))

        history_items = history.History().get_request_history(
            history_request['id'], 1
        )
    elif request_type == u'B':
        try:
            history_request = creditrequest.CreditRequest().get_id(
                request_id
            )
        except:
            return redirect(url_for('admin.views.admin_requests'))

        history_items = history.History().get_request_history(
            history_request['id'], 2
        )

    elif request_type == u'C':
        try:
            history_request = paidrequest.PaidRequest().get_id(
                request_id
            )
        except:
            return redirect(url_for('admin.views.admin_requests'))

        history_items = history.History().get_request_history(
            history_request['id'], 3
        )

    admins = user.User().get_admins()

    message_form.request_id.data = history_request['id']
    message_form.request_type.data = request_type
    message_form.to_user.data = history_request['user']['id']

    params = {
        'admins': admins,
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
        owner_id = userrequest_data['user']['id']

        data.update({'userrequest': form.request_id.data})
    elif form.request_type.data == 'B':
        creditrequest_data = creditrequest.CreditRequest().get_id(request_id)
        owner_id = creditrequest_data['user']['id']

        data.update({'creditrequest': form.request_id.data})
    elif form.request_type.data == 'C':
        paidrequest_data = paidrequest.PaidRequest().get_id(request_id)
        owner_id = paidrequest_data['user']['id']

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
    product_data = product.Product().get_id(product_id, excludes=['all'])

    flash(('success', u'Producto añadido a la cola de precios'))

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
    product_data = product.Product().get_id(product_id, excludes=['all'])

    flash(('success', u'Producto añadido a la cola de recursos'))

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

        return render_template(
            'admin/panel/generic-form.html',
            form=form
        )
    elif request.method == 'POST':
        form = admin.SteamProduct(request.form)

        if not form.validate():
            return render_template(
                'admin/panel/generic-form.html',
                form=form
            )

        new_form = admin.SteamProduct()

        if form.app_id.data:
            try:
                product.Product().get_app_id(form.app_id.data)

                flash(u'La AppID ya existe en la base de datos')

                return render_template(
                    'admin/panel/generic-form.html',
                    form=new_form
                )
            except:
                pass

            product_task.add_product_to_store.delay(app_id=form.app_id.data)

            flash(u'AppID añadido a la cola de adición de productos')

            return render_template(
                'admin/panel/generic-form.html',
                form=new_form
            )
        elif form.sub_id.data:
            try:
                product.Product().get_sub_id(form.sub_id.data)

                flash(u'La SubID ya existe en la base de datos')

                return render_template(
                    'admin/panel/generic-form.html',
                    form=new_form
                )
            except:
                pass

            product_task.add_product_to_store.delay(sub_id=form.sub_id.data)

            flash(u'SubID añadido a la cola de adición de productos')

            return render_template(
                'admin/panel/generic-form.html',
                form=new_form
            )

        flash(u'Se requiere AppID o SubID')

        return render_template(
            'admin/panel/generic-form.html',
            form=new_form
        )


@admin_view.route('/sales/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def queue_sale_add():
    if request.method == 'GET':
        form = admin.SaleForm()

        return render_template(
            'admin/panel/generic-form.html',
            form=form
        )
    elif request.method == 'POST':
        form = admin.SaleForm(request.form)

        if not form.validate():
            return render_template(
                'admin/panel/generic-form.html',
                form=form
            )

        sales_tasks.load_sale_from_crawler.delay(
            exclusive_title=form.title.data,
            end_time_delta=form.end_time_delta.data or 24
        )

        flash(
            (
                u'success',
                u'Añadido "{0}" a la cola de sales'.format(form.title.data)
            )
        )

        return render_template(
            'admin/panel/generic-form.html',
            form=form
        )


@admin_view.route('/bots/')
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_bots_dashboard():
    if session.get('user') != 1:
        return redirect('views.admin.admin_root')

    return render_template('admin/bots/dashboard.html')


@admin_view.route('/bots/get/ids/', methods=['POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_get_bot_ids():
    ids = request.form.get('bots')
    bots = bot.Bot().get_bot_ids(json.loads(ids))

    return render_template('admin/bots/bots.html', bots=bots)


@admin_view.route('/tools/sliders/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
@route_decorators.is_admin
def admin_sliders_view():
    if request.method == 'GET':
        form = admin.SliderForm()

        return render_template(
            'admin/panel/file-form.html',
            form=form
        )
    elif request.method == 'POST':
        form = admin.SliderForm(request.form)

        if not form.validate():
            return render_template(
                'admin/panel/file-form.html',
                form=form
            )

        if not request.files.get(form.image.name):
            flash(('danger', u'No se encontró una imagen en el formulario'))

            return render_template(
                'admin/panel/file-form.html',
                form=form
            )

        image_data = request.files.get(form.image.name).stream.read()

        if not len(image_data):
            flash(('danger', u'La imagen se encontraba vacía'))

            return render_template(
                'admin/panel/file-form.html',
                form=form
            )

        extension = request.files.get(form.image.name).filename.rsplit('.')[-1]

        slider_id = slider.Slider().create(**{
            'extension': extension,
            'title': form.title.data,
            'content': form.content.data,
            'position': form.position.data
        })

        slider_path = os.path.join(
            app_config.UPLOAD_DIRECTORY,
            'img',
            'slider',
            '%d' % slider_id
        )

        if not os.path.isfile(slider_path) and not os.path.isdir(slider_path):
            os.makedirs(slider_path)

        f = open(
            os.path.join(slider_path, '%d.%s' % (slider_id, extension)),
            'wb+'
        )

        f.write(image_data)
        f.close()

        flash(('success', 'Slider creado satisfactoriamente'))
        form = admin.SliderForm()

        return render_template(
            'admin/panel/file-form.html',
            form=form
        )
