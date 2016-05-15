#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import user
from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import requests_tools

from utils import route_decorators

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

    if request_type == u'A':
        request = userrequest.UserRequest().get_userrequest_by_id(request_id)
        history_items = history.History().get_request_history(request['id'], 1)
    elif request_type == u'C':
        request = paidrequest.PaidRequest().get_paidrequest_by_id(request_id)
        history_items = history.History().get_request_history(request['id'], 3)

    admins = user.User().get_admins()

    params = {
        'request': request,
        'admins': admins,
        'request_type': request_type,
        'history_items': history_items
    }

    return render_template('admin/views/history.html', **params)
