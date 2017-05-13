#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import session
from flask import request
from flask import Blueprint

from steamcommerce_api.api import user
from steamcommerce_api.api import history
from steamcommerce_api.api import creditrequest

from inputs import store_inputs
from utils import route_decorators

import constants

ajax_creditrequest = Blueprint('ajax.store.creditrequest', __name__)


@ajax_creditrequest.route('/generate/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.as_json
def ajax_creditrequest_generate():
    # return ({'success': False, 'status': 10}, 500)
    curr_user = user.User().get_by_id(session.get('user'))
    form = store_inputs.CreditRequestInput(request)

    if not form.validate():
        return ({'success': False, 'status': 0}, 422)

    amount = float(request.form.get('amount'))

    if amount < 5 or amount > 5000:
        return ({'success': False, 'status': 1}, 500)

    invoice = creditrequest.CreditRequest().generate(
        curr_user['id'],
        curr_user['email'],
        amount
    )

    if not invoice.get('success'):
        if invoice.get('status') == 0:
            return ({'success': False, 'status': 2}, 500)

        if invoice.get('status') == 1:
            return ({'success': False, 'status': 3}, 500)

    history.History().push(
        constants.HISTORY_GENERATED_STATE,
        invoice['creditrequest'],
        constants.HISTORY_CREDITREQUEST_TYPE
    )

    return invoice
