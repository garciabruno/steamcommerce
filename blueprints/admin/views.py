#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import session
from flask import request
from flask import url_for
from flask import redirect
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import user
from steamcommerce_api.api import message
from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import notification
from steamcommerce_api.api import creditrequest
from steamcommerce_api.api import requests_tools

import constants

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
    userrequests = userrequest.UserRequest().get_paid_userrequests()
    paidrequests = paidrequest.PaidRequest().get_paid_paidrequests()
    informed = userrequest.UserRequest().get_informed_userrequests()

    resumes_all = requests_tools.RequestsTools().resume_all(
        userrequests,
        paidrequests
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
        creditrequest_data = userrequest.CreditRequest().get_id(request_id)
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
