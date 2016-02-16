#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import Blueprint

import json

from inputs import store_inputs

from steamcommerce_api import config

from steamcommerce_api.api import user
from steamcommerce_api.api import cart
from steamcommerce_api.api import product
from steamcommerce_api.api import paidrequest

ajax_paidrequest = Blueprint('ajax.store.paidrequest', __name__)


@ajax_paidrequest.route('/generate/', methods=['POST'])
def ajax_paidrequest_generate():
    user_id = 1
    form = store_inputs.PaidRequestInput(request)

    if not form.validate():
        return json.dumps({'success': False, 'status': 0}), 422

    product_id = int(request.form.get('product_id'))
    product_data = product.Product().get_product_by_id(product_id)

    if product_data is None:
        return json.dumps({'success': False, 'status': 1}), 500

    if not product_data.get('visible'):
        return json.dumps({'success': False, 'status': 2}), 500

    if not product_data.get('price'):
        return json.dumps({'success': False, 'status': 3}), 500

    price = product_data.get('price').get('price')
    user_data = user.User().get_by_id(user_id)

    if not (user_data.money + user_data.wallet) >= price:
        return json.dumps({'success': False, 'status': 4}), 500

    if product_data.get('run_stock') and product_data.get('stock') == 0:
        return json.dumps({'success': False, 'status': 5}), 500

    if user_data.money >= price:
        commerce_id = config.CUENTADIGITAL_EMILIANO_ID
    else:
        commerce_id = config.CUENTADIGITAL_NIN_ID

    invoice = paidrequest.PaidRequest().generate(
        user_id,
        price,
        [product_id],
        commerce_id
    )

    if invoice.get('success'):
        if user_data.money >= price:
            user.User().decrease_money(user_id, price)
        elif user_data.money > 0:
            user.User().decrease_money(user_id, user_data.money)
            user.User().decrease_wallet(user_id, price - user_data.money)
        else:
            user.User().decrease_wallet(user_id, price)

        return json.dumps(invoice)

    return json.dumps(invoice), 500


@ajax_paidrequest.route('/cart/generate/', methods=['POST'])
def ajax_paidrequest_cart_generate():
    user_id = 1

    cart.Cart().process_cart(user_id)
    user_cart = cart.Cart().get_user_cart(user_id)

    user_data = user.User().get_by_id(user_id)

    if len(user_cart.get('items')) == 0:
        return json.dumps({'success': False, 'status': 0}), 500

    if not user_cart.get('prices').get('credit'):
        return json.dumps({'success': False, 'status': 1}), 500

    price = user_cart.get('prices').get('credit')

    if not (user_data.money + user_data.wallet) >= price:
        return json.dumps({'success': False, 'status': 2}), 500

    if user_data.money >= price:
        commerce_id = config.CUENTADIGITAL_EMILIANO_ID
    else:
        commerce_id = config.CUENTADIGITAL_NIN_ID

    invoice = paidrequest.PaidRequest().generate(
        user_id,
        price,
        [x.get('product').get('id') for x in user_cart.get('items')],
        commerce_id
    )

    if invoice.get('success'):
        if user_data.money >= price:
            user.User().decrease_money(user_id, price)
        elif user_data.money > 0:
            user.User().decrease_money(user_id, user_data.money)
            user.User().decrease_wallet(user_id, price - user_data.money)
        else:
            user.User().decrease_wallet(user_id, price)

        cart.Cart().empty_user_cart(user_id)

        return json.dumps(invoice)

    return json.dumps(invoice), 500
