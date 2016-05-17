#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import session
from flask import request
from flask import Blueprint

from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import userrequest

from utils import route_decorators
from inputs import admin_inputs

import constants

admin_ajax_userrequest = Blueprint('admin.ajax.userrequest', __name__)


@admin_ajax_userrequest.route('/accept/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_accept():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    userrequest_data = userrequest.UserRequest().get_userrequest_by_id(
        request_id
    )

    if userrequest_data['accepted']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')

    userrequest.UserRequest().accept_userrequest(request_id, user_id=user_id)

    history.History().push(
        constants.HISTORY_ACCEPTED_STATE,
        request_id,
        constants.HISTORY_USERREQUEST_TYPE
    )

    adminlog.AdminLog().push(
        constants.ADMINLOG_USERREQUEST_ACCEPTED, **{
            'userrequest': request_id,
            'user': user_id
        }
    )

    return {'success': True}


@admin_ajax_userrequest.route('/deny/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_deny():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    userrequest_data = userrequest.UserRequest().get_userrequest_by_id(
        request_id
    )

    if not userrequest_data['visible']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')
    reason = request.form.get('reason', '')

    userrequest.UserRequest().deny_userrequest(request_id, reason)

    history.History().push(
        constants.HISTORY_DENIED_STATE,
        request_id,
        constants.HISTORY_USERREQUEST_TYPE
    )

    adminlog.AdminLog().push(
        constants.ADMINLOG_USERREQUEST_DENIED, **{
            'userrequest': request_id,
            'user': user_id
        }
    )

    return {'success': True}


@admin_ajax_userrequest.route('/assign/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_assign():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    userrequest_data = userrequest.UserRequest().get_userrequest_by_id(
        request_id
    )

    if userrequest_data['assigned']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')

    userrequest.UserRequest().assign(request_id, user_id)

    return {'success': True}


@admin_ajax_userrequest.route('/deassign/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_deassign():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    userrequest_data = userrequest.UserRequest().get_userrequest_by_id(
        request_id
    )

    if not userrequest_data['assigned']:
        return ({'success': False, 'status': 0}, 500)

    userrequest.UserRequest().assign(request_id, None)

    return {'success': True}


@admin_ajax_userrequest.route('/assign/to/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_assign_to():
    form = admin_inputs.RequestAssignInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    assign_to_id = int(request.form.get('user_id'))

    userrequest.UserRequest().assign(request_id, assign_to_id)

    return {'success': True}


@admin_ajax_userrequest.route('/set/paid/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_userrequest_set_paid():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    user_id = session.get('user')
    userrequest_data = userrequest.UserRequest().get_userrequest_by_id(
        request_id
    )

    if userrequest_data['paid']:
        return ({'success': False, 'status': 0}, 500)

    userrequest.UserRequest().set_paid(request_id)

    history.History().push(
        constants.HISTORY_PAID_STATE,
        request_id,
        constants.HISTORY_USERREQUEST_TYPE
    )

    adminlog.AdminLog().push(
        constants.ADMINLOG_USERREQUEST_PAID, **{
            'userrequest': request_id,
            'user': user_id
        }
    )

    return {'success': True}
