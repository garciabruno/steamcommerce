#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import Blueprint

from inputs import store_inputs

import json

from steamcommerce_api.api import cart
from steamcommerce_api.api import product
from steamcommerce_api.api import userrequest

ajax_userrequest = Blueprint('ajax.store.userrequest', __name__)


@ajax_userrequest.route('/generate/', methods=['POST'])
def ajax_userrequest_generate():
    user_id = 1
    email = 'admin@extremegaming-arg.com.ar'

    form = store_inputs.UserRequestInput(request)

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
    promotion = True if product_data.get('promotion') else False

    invoice = userrequest.UserRequest().generate(
        user_id,
        price,
        email,
        [product_data.get('id')],
        promotion=promotion
    )

    if not invoice.get('success'):
        # TODO: Delete UserRequest generated from user

        if invoice.get('status') == 0:
            return json.dumps({'success': False, 'status': 5}), 500

        if invoice.get('status') == 1:
            return json.dumps({'success': False, 'status': 4}), 500

    return json.dumps(invoice)


@ajax_userrequest.route('/cart/generate/')
def ajax_userrequest_cart_generate():
    user_id = 1
    email = 'admin@extremegaming-arg.com.ar'

    cart.Cart().process_cart(user_id)
    user_cart = cart.Cart().get_user_cart(user_id)

    if len(user_cart.get('items')) == 0:
        return json.dumps({'success': False, 'status': 0}), 500

    if not user_cart.get('prices').get('normal'):
        return json.dumps({'success': False, 'status': 1}), 500

    cart_items = user_cart.get('items')

    promotion = any(
        [x.get('product').get('is_promotional') for x in cart_items]
    )

    invoice = userrequest.UserRequest().generate(
        user_id,
        user_cart.get('prices').get('normal'),
        email,
        [x.get('product').get('id') for x in cart_items],
        promotion=promotion
    )

    if not invoice.get('success'):
        # TODO: Delete UserRequest generated from user

        if invoice.get('status') == 0:
            return json.dumps({'success': False, 'status': 3}), 500

        if invoice.get('status') == 1:
            return json.dumps({'success': False, 'status': 4}), 500

    cart.Cart().empty_user_cart(user_id)
    invoice.update({'promotional': promotion})

    return json.dumps(invoice)
