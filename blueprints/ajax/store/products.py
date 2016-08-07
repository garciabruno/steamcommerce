#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import abort
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import product

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
