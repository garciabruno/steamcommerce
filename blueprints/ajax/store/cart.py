#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import Blueprint

from steamcommerce_api.api import cart
from steamcommerce_api.api import product

from inputs import store_inputs

import json


ajax_cart = Blueprint('ajax.store.cart', __name__)


@ajax_cart.route('/add/', methods=['POST'])
def ajax_cart_add():
    user_id = 1
    form = store_inputs.AddCartInput(request)

    if not form.validate():
        return json.dumps({'success': False, 'errors': form.errors}), 422

    product_id = int(request.form.get('product_id'))
    form_product = product.Product().get_product_by_id(product_id)

    if not form_product.get('visible') or not form_product.get('price', None):
        return json.dumps(
            {'success': False, 'errors': 'product_not_available'}
        ), 500

    user_cart = cart.Cart().get_user_cart(user_id, trim=True)

    if len(user_cart.get('items')) >= 10:
        return json.dumps(
            {'success': False, 'errors': 'cart_full'}
        ), 500

    success = cart.Cart().add_to_user_cart(user_id, product_id)

    if success:
        return json.dumps(
            {'success': True, 'cart': len(user_cart.get('items')) + 1}
        )

    return json.dumps(
        {'success': False, 'errors': 'unknown'}, 500
    )


@ajax_cart.route('/remove/', methods=['POST'])
def ajax_cart_remove():
    user_id = 1
    form = store_inputs.RemoveCartInput(request)

    if not form.validate():
        return json.dumps({'success': True, 'errors': form.errors})

    relation_id = int(request.form.get('relation_id'))
    success = cart.Cart().remove_from_user_cart(user_id, relation_id)

    return json.dumps({'success': bool(success)})
