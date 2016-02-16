#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import cart
from steamcommerce_api.api import user

cart_view = Blueprint('views.cart', __name__)


@cart_view.route('/')
def cart_root():
    user_id = 1

    cart.Cart().process_cart(user_id)
    user_cart = cart.Cart().get_user_cart(user_id)

    user_data = user.User().get_by_id(user_id)

    params = {
        'user': user_data,
        'user_cart': user_cart
    }

    return render_template('views/cart/view.html', **params)
