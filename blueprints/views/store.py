#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import user
from steamcommerce_api.api import slider
from steamcommerce_api.api import section
from steamcommerce_api.api import product
from steamcommerce_api.api import storepromotion

store = Blueprint('views.store', __name__)


@store.route('/')
def store_root():
    return render_template('views/store/landing.html')


@store.route('/tienda/')
@store.route('/catalogo/')
@store.route('/comprar/')
@store.route('/tienda/pagina/<int:page_id>')
@store.route('/catalogo/pagina/<int:page_id>')
@store.route('/comprar/pagina/<int:page_id>')
def store_catalog(page_id=1):
    sliders = slider.Slider().get_active()
    sections = section.Section().get_active()
    products = product.Product().get_by_section(sections[0].id, page_id)
    promotions = storepromotion.StorePromotion().get_active_promotions()
    promotion_products = []

    if len(promotions) > 0:
        promotion_products = storepromotion.StorePromotion().\
            get_promotion_products(promotions[0].id, 1)

    template_params = {
        'sliders': sliders,
        'products': products,
        'sections': sections,
        'promotions': promotions,
        'promotion_products': promotion_products
    }

    return render_template('views/store/catalog.html', **template_params)


@store.route('/tienda/<app_id>')
@store.route('/catalogo/<app_id>')
@store.route('/comprar/<app_id>/')
def store_app_id(app_id):
    app_product = product.Product().get_by_app_id(app_id)

    user_id = 1
    user_data = user.User().get_by_id(user_id)

    if app_product is None:
        return 'Woops! Product does not exist!'

    if not app_product.get('visible'):
        return 'Woops! Product not currently available'

    if app_product.get('run_stock') and app_product.get('stock') == 0:
        return 'Woops! Out of stock'

    params = {
        'user': user_data,
        'product': app_product
    }

    return render_template('views/store/product.html', **params)
