#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import session
from flask import request
from flask import Blueprint

from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import notification

from utils import route_decorators
from inputs import admin_inputs

import constants

admin_ajax_paidrequest = Blueprint('admin.ajax.paidrequest', __name__)


@admin_ajax_paidrequest.route('/accept/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_accept():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    paidrequest_data = paidrequest.PaidRequest().get_id(
        request_id,
        excludes=['all']
    )

    if paidrequest_data['accepted']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')

    paidrequest.PaidRequest().accept_paidrequest(request_id, user_id=user_id)

    return {'success': True}


@admin_ajax_paidrequest.route('/deny/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_deny():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))

    paidrequest_data = paidrequest.PaidRequest().get_id(
        request_id,
        excludes=[
            'accepted_by',
            'paidrequest_relations',
            'paidrequest_messages'
        ]
    )

    if not paidrequest_data['visible']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')
    reason = request.form.get('reason', '')

    paidrequest.PaidRequest().deny_paidrequest(request_id, reason)

    history.History().push(
        constants.HISTORY_DENIED_STATE,
        request_id,
        constants.HISTORY_PAIDREQUEST_TYPE
    )

    adminlog.AdminLog().push(
        constants.ADMINLOG_PAIDREQUEST_DENIED, **{
            'paidrequest': request_id,
            'user': user_id
        }
    )

    notification.Notification().push(
        paidrequest_data['user']['id'],
        constants.NOTIFICATION_PAIDREQUEST_DENIED,
        **{'paidrequest': paidrequest_data['id']}
    )

    return {'success': True}


@admin_ajax_paidrequest.route('/assign/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_assign():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))

    paidrequest_data = paidrequest.PaidRequest().get_id(
        request_id,
        excludes=['all']
    )

    if paidrequest_data['assigned']:
        return ({'success': False, 'status': 0}, 500)

    user_id = session.get('user')
    paidrequest.PaidRequest().assign(request_id, user_id)

    return {'success': True}


@admin_ajax_paidrequest.route('/deassign/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_deassign():
    form = admin_inputs.RequestIDInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))

    paidrequest_data = paidrequest.PaidRequest().get_id(
        request_id,
        excludes=['all']
    )

    if not paidrequest_data['assigned']:
        return ({'success': False, 'status': 0}, 500)

    paidrequest.PaidRequest().assign(request_id, None)

    return {'success': True}


@admin_ajax_paidrequest.route('/assign/to/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_assign_to():
    form = admin_inputs.RequestAssignInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    request_id = int(request.form.get('request_id'))
    assign_to_id = int(request.form.get('user_id'))

    paidrequest.PaidRequest().assign(request_id, assign_to_id)

    return {'success': True}


@admin_ajax_paidrequest.route('/set/sent/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_set_sent():
    relation_id = int(request.form.get('relation_id'))

    paidrequest.PaidRequest().set_sent(relation_id)

    return {'success': True}


@admin_ajax_paidrequest.route('/set/unsent/', methods=['POST'])
@route_decorators.ajax_is_admin
@route_decorators.as_json
def ajax_paidrequest_set_unsent():
    relation_id = int(request.form.get('relation_id'))

    paidrequest.PaidRequest().set_sent(relation_id, sent=False)

    return {'success': True}
