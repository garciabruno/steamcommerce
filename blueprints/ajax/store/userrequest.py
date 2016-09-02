#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import session
from flask import Blueprint

from steamcommerce_api.api import user
from steamcommerce_api.api import cart
from steamcommerce_api.api import product
from steamcommerce_api.api import history
from steamcommerce_api.api import userrequest

from inputs import store_inputs
from utils import route_decorators

import datetime
import config
import constants


ajax_userrequest = Blueprint('ajax.store.userrequest', __name__)


@ajax_userrequest.route('/generate/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.as_json
def ajax_userrequest_generate():
    curr_user = user.User().get_by_id(session.get('user'))
    form = store_inputs.UserRequestInput(request)

    if not form.validate():
        return ({'success': False, 'status': 0}, 422)

    product_id = int(request.form.get('product_id'))
    product_data = product.Product().get_id(product_id, excludes=['all'])

    if product_data is None:
        return ({'success': False, 'status': 1}, 500)

    if not product_data.get('visible'):
        return ({'success': False, 'status': 2}, 500)

    if (
        not product_data.get('price_active') or
        not product_data.get('price_value')
    ):
        return ({'success': False, 'status': 3}, 500)

    if product_data.get('price_type') != 1:
        return ({'success': False, 'status': 4}, 500)

    if product_data.get('has_anticheat'):
        incomes = user.User().get_user_spent_incomes(curr_user['id'])

        if incomes < config.MIN_SPENT_INCOMES_VAC_GAMES:
            return ({'success': False, 'status': 7}, 500)

        register_date = (
            curr_user['register_date'] or datetime.datetime(
                year=2012,
                day=15,
                month=10,
                hour=20,
                minute=0
            )
        )

        delta = datetime.datetime.now() - register_date

        if delta < config.VAC_GAMES_TIME_DELTA:
            return ({'success': False, 'status': 8}, 500)

    price = product_data.get('price_value')
    promotion = None

    if product_data.get('promotion'):
        if product_data.get('promotion').get('ending_date'):
            promotion = product_data.get('promotion').get('id')

    invoice = userrequest.UserRequest().generate(
        curr_user['id'],
        price,
        curr_user['email'],
        [product_data.get('id')],
        promotion=promotion
    )

    if not invoice.get('success'):
        # TODO: Delete UserRequest generated from user

        if invoice.get('status') == 0:
            return ({'success': False, 'status': 6}, 500)

        if invoice.get('status') == 1:
            return ({'success': False, 'status': 5}, 500)

    history.History().push(
        constants.HISTORY_GENERATED_STATE,
        invoice.get('userrequest'),
        constants.HISTORY_USERREQUEST_TYPE
    )

    invoice.update({'promotional': promotion is not None})

    return invoice


@ajax_userrequest.route('/cart/generate/')
@route_decorators.ajax_is_logged_in
@route_decorators.as_json
def ajax_userrequest_cart_generate():
    curr_user = user.User().get_by_id(session.get('user'))

    cart.Cart().process_cart(curr_user['id'])
    user_cart = cart.Cart().get_user_cart(curr_user['id'])

    if len(user_cart.get('items')) == 0:
        return ({'success': False, 'status': 0}, 500)

    if not user_cart.get('prices').get('normal'):
        return ({'success': False, 'status': 1}, 500)

    cart_items = user_cart.get('items')

    promotion = None
    user_is_register_restricted = False
    user_is_income_restricted = False

    for cart_item in cart_items:
        cart_item_product = cart_item.get('product')
        product_promotion = cart_item_product.get('promotion')

        if cart_item_product.get('has_anticheat'):
            incomes = user.User().get_user_spent_incomes(curr_user['id'])

            if incomes < config.MIN_SPENT_INCOMES_VAC_GAMES:
                user_is_income_restricted = True

                break

            register_date = (
                curr_user['register_date'] or datetime.datetime(
                    year=2012,
                    day=15,
                    month=10,
                    hour=20,
                    minute=0
                )
            )

            delta = datetime.datetime.now() - register_date

            if delta < config.VAC_GAMES_TIME_DELTA:
                user_is_register_restricted = True

                break

        if product_promotion:
            if product_promotion.get('ending_date'):
                promotion = product_promotion.get('id')

                break

    if user_is_income_restricted:
        return ({'success': False, 'status': 5}, 500)

    if user_is_register_restricted:
        return ({'success': False, 'status': 6}, 500)

    invoice = userrequest.UserRequest().generate(
        curr_user['id'],
        user_cart.get('prices').get('normal'),
        curr_user['email'],
        [x.get('product').get('id') for x in cart_items],
        promotion=promotion
    )

    if not invoice.get('success'):
        # TODO: Delete UserRequest generated from user

        if invoice.get('status') == 0:
            return ({'success': False, 'status': 3}, 500)

        if invoice.get('status') == 1:
            return ({'success': False, 'status': 4}, 500)

    cart.Cart().empty_user_cart(curr_user['id'])
    invoice.update({'promotional': promotion is not None})

    return invoice
