#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import Blueprint

from steamcommerce_api.api import creditrequest

from inputs import store_inputs
from utils import route_decorators

ajax_creditrequest = Blueprint('ajax.store.creditrequest', __name__)


@ajax_creditrequest.route('/generate/', methods=['POST'])
@route_decorators.as_json
def ajax_creditrequest_generate():
    user_id = 1
    email = 'admin@extremegaming-arg.com.ar'
    form = store_inputs.CreditRequestInput(request)

    if not form.validate():
        return ({'success': False, 'status': 0}, 422)

    amount = float(request.form.get('amount'))

    if amount < 5 or amount > 5000:
        return ({'success': False, 'status': 1}, 500)

    invoice = creditrequest.CreditRequest().generate(
        user_id,
        email,
        amount
    )

    if not invoice.get('success'):
        if invoice.get('status') == 0:
            return ({'success': False, 'status': 2}, 500)

        if invoice.get('status') == 1:
            return ({'success': False, 'status': 3}, 500)

    return invoice
