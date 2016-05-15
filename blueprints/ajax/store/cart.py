#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import cart
from steamcommerce_api.api import user
from steamcommerce_api.api import product

from utils import route_decorators
from inputs import store_inputs


ajax_cart = Blueprint('ajax.store.cart', __name__)


@ajax_cart.route('/add/', methods=['POST'])
@route_decorators.as_json
def ajax_cart_add():
    user_id = 1
    form = store_inputs.AddCartInput(request)

    if not form.validate():
        return ({'success': False, 'status': 0}, 422)

    product_id = int(request.form.get('product_id'))
    form_product = product.Product().get_product_by_id(product_id)

    if not form_product.get('visible'):
        return ({'success': False, 'status': 1}, 500)

    if not form_product.get('price'):
        return ({'success': False, 'status': 2}, 500)

    if form_product.get('product_type') == 2:
        return ({'success': False, 'status': 3}, 500)

    user_cart = cart.Cart().get_user_cart(user_id, trim=True)

    if len(user_cart.get('items')) >= 10:
        return ({'success': False, 'status': 4}, 500)

    success = cart.Cart().add_to_user_cart(user_id, product_id)

    if not success:
        return ({'success': False, 'status': 5}, 500)

    cart_items_count = len(user_cart.get('items'))
    return {'success': True, 'cart': cart_items_count + 1}


@ajax_cart.route('/remove/', methods=['POST'])
@route_decorators.as_json
def ajax_cart_remove():
    user_id = 1
    form = store_inputs.RemoveCartInput(request)

    if not form.validate():
        return ({'success': True, 'errors': form.errors}, 422)

    relation_id = int(request.form.get('relation_id'))
    success = cart.Cart().remove_from_user_cart(user_id, relation_id)

    cart.Cart().process_cart(user_id)

    user_data = user.User().get_by_id(user_id)
    user_cart = cart.Cart().get_user_cart(user_id)

    template_params = {
        'user': user_data,
        'user_cart': user_cart
    }

    hud = render_template('views/cart/hud.html', **template_params)

    return {'success': bool(success), 'hud': hud}
