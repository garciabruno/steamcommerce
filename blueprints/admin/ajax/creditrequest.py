#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import session
from flask import Blueprint

from inputs import admin_inputs
from utils import route_decorators

from steamcommerce_api.api import user
from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import creditrequest

import constants

admin_ajax_creditrequest = Blueprint('admin.ajax.creditrequest', __name__)


@admin_ajax_creditrequest.route('/accept/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_creditrequest_accept():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))

    creditrequest_data = creditrequest.CreditRequest().get_creditrequest_by_id(
        request_id
    )

    if creditrequest_data['accepted']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')
    to_user_id = creditrequest_data['user']['id']

    creditrequest.CreditRequest().accept_creditrequest(
        request_id, user_id=user_id
    )

    user.User().increase_wallet(to_user_id, creditrequest_data['amount'])

    history.History().push(
        constants.HISTORY_ACCEPTED_STATE,
        request_id,
        constants.HISTORY_CREDITREQUEST_TYPE
    )

    adminlog.AdminLog().push(
        constants.ADMINLOG_CREDITREQUEST_ACCEPTED, **{
            'creditrequest': request_id,
            'user': user_id
        }
    )

    return {'success': True}


@admin_ajax_creditrequest.route('/set/paid/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_set_paid():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))

    creditrequest_data = creditrequest.CreditRequest().get_creditrequest_by_id(
        request_id
    )

    if creditrequest_data['paid']:
        return ({'success': False, 'status': 0}, 500)

    creditrequest.CreditRequest().set_paid(request_id)

    history.History().push(
        constants.HISTORY_PAID_STATE,
        request_id,
        constants.HISTORY_CREDITREQUEST_TYPE
    )

    return {'success': True}
