#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import g
from flask import Flask

'''
Internal imports
'''

import config

# Blueprints imports

from blueprints.views.store import store
from blueprints.views.user import user_view
from blueprints.views.cart import cart_view

from blueprints.ajax.store.cart import ajax_cart
from blueprints.ajax.store.search import ajax_search
from blueprints.ajax.store.products import ajax_products
from blueprints.ajax.store.userrequest import ajax_userrequest
from blueprints.ajax.store.paidrequest import ajax_paidrequest
from blueprints.ajax.store.creditrequest import ajax_creditrequest

from steamcommerce_api.core import models

BLUEPRINTS = [
    store,
    cart_view,
    user_view,
    ajax_cart,
    ajax_search,
    ajax_products,
    ajax_userrequest,
    ajax_paidrequest,
    ajax_creditrequest
]

app = Flask(__name__)

app.config.from_object(config)
app.logger.addHandler(config.LOG_HANDLER)

app.logger.info('Staring steamcommerce')


for blueprint in BLUEPRINTS:
    try:
        blueprint_enabled = config.ENABLED_BLUEPRINTS[blueprint.name]
    except KeyError:
        blueprint_enabled = False

    if blueprint_enabled:
        app.register_blueprint(
            blueprint,
            url_prefix=config.BLUEPRINTS_ENDPOINTS[blueprint.name]
        )

'''
(Temporary) Template filter registration
'''


@app.before_request
def before_request():
    g.db = models.database
    g.db.connect()


@app.after_request
def after_request(response):
    g.db.close()

    return response


@app.template_filter()
def price_format(price):
    return '%.2f' % price


@app.template_filter()
def date_format(date):
    return date.strftime('%d/%m/%Y %H:%M')
