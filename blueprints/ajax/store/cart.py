#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import g
from flask import request
from flask import session
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import cart
from steamcommerce_api.api import product

from utils import route_decorators
from inputs import store_inputs

import json

ajax_cart = Blueprint('ajax.store.cart', __name__)


@ajax_cart.route('/add/', methods=['POST'])
@route_decorators.ajax_is_logged_in
def ajax_cart_add():
    user_id = session.get('user')
    form = store_inputs.AddCartInput(request)

    if not form.validate():
        return ({'success': False, 'status': 0}, 422)

    product_id = int(request.form.get('product_id'))
    form_product = product.Product().get_id(product_id, excludes=['all'])

    if not form_product.get('visible'):
        return json.dumps({'success': False, 'status': 1}), 500

    if (
        not form_product.get('price_active') or
        not form_product.get('price_value')
    ):
        return json.dumps({'success': False, 'status': 2}), 500

    if form_product.get('product_type') == 2:
        return json.dumps({'success': False, 'status': 3}), 500

    user_cart = cart.Cart().get_user_cart(user_id, trim=True)

    if len(user_cart.get('items')) >= 25:
        return json.dumps({'success': False, 'status': 4}), 500

    success = cart.Cart().add_to_user_cart(user_id, product_id)

    if not success:
        return json.dumps({'success': False, 'status': 5}), 500

    user_cart = cart.Cart().get_user_cart(session.get('user'))

    params = {
        'user_cart': user_cart
    }

    return render_template('views/cart/view.html', **params)


@ajax_cart.route('/remove/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.as_json
def ajax_cart_remove():
    user_id = session.get('user')
    form = store_inputs.RemoveCartInput(request)

    if not form.validate():
        return ({'success': True, 'errors': form.errors}, 422)

    relation_id = int(request.form.get('relation_id'))

    cart.Cart().remove_from_user_cart(user_id, relation_id)
    user_cart = cart.Cart().get_user_cart(session.get('user'))

    params = {
        'user_cart': user_cart
    }

    return render_template('views/cart/hud.html', **params)
