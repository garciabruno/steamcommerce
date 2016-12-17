#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import abort
from flask import request
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import product
from steamcommerce_api.core import models

import config
from utils import route_decorators

ajax_products = Blueprint('ajax.store.products', __name__)


@ajax_products.route('/page/<int:section>/<int:page_id>')
def ajax_store_products_page(section, page_id):
    products = product.Product().get_by_section(section, page_id)

    if len(products) > 0:
        return render_template(
            'views/store/products.html',
            products=products
        )
    else:
        return abort(404)


@ajax_products.route('/cities/', methods=['POST'])
@route_decorators.as_json
def ajax_store_cities():
    letter = request.form.get('letter')

    if not letter or not len(letter):
        return []

    cities = models.City.select().where(
        models.City.province_letter == letter
    ).order_by(
        models.City.name.asc()
    )

    return [
        {'internal_id': x.internal_id, 'name': x.name} for x in cities
    ]


@ajax_products.route('/shipping/price/', methods=['POST'])
@route_decorators.as_json
def ajax_shipping_price():
    city_id = request.form.get('city_id')
    province_letter = request.form.get('province_letter')

    if not province_letter or not city_id:
        return ({'success': False, 'status': 0}, 500)

    try:
        city_id = int(city_id)
    except:
        return ({'success': False, 'status': 0}, 500)

    try:
        models.Province.get(letter=province_letter)
    except:
        return ({'success': False, 'status': 1}, 500)

    try:
        models.City.get(internal_id=city_id)
    except:
        return ({'success': False, 'status': 2}, 500)

    if province_letter == 'X' and city_id == 26120:
        if request.form.get('pickup'):
            return {'success': True, 'price': config.SHIPPING_TIER_0}
        else:
            return {'success': True, 'price': config.SHIPPING_TIER_1}

    return {'success': True, 'price': config.SHIPPING_TIER_2}
