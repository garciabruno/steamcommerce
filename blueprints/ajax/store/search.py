#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import product

from inputs import store_inputs
from utils import route_decorators

ajax_search = Blueprint('ajax.store.search', __name__)


@ajax_search.route('/products/', methods=['POST'])
@route_decorators.as_json
def ajax_search_products():
    form = store_inputs.SearchInput(request)

    if not form.validate():
        return ({'success': False, 'errors': form.errors}, 422)

    matches = product.Product().search_by_title(request.form.get('title'))

    if len(matches) == 0:
        return ({'success': False, 'status': 0}, 500)

    return render_template('views/store/products.html', products=matches)
