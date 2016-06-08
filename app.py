#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import g
from flask import Flask
from flask import session
from flask import request
from flask import url_for
from flask import redirect
from flask import render_template

from werkzeug.routing import BaseConverter
from flask_bootstrap import Bootstrap

from steamcommerce_api.utils import json_util

from steamcommerce_api.api import cart
from steamcommerce_api.api import notification
from steamcommerce_api.api import userrequest

import datetime

'''
Internal imports
'''

import config

# Blueprints imports

from blueprints.views.store import store
from blueprints.views.user import user_view
from blueprints.views.testimonials import testimonials
from blueprints.admin.views import admin_view

from blueprints.ajax.store.cart import ajax_cart
from blueprints.ajax.store.search import ajax_search
from blueprints.ajax.store.products import ajax_products
from blueprints.ajax.store.userrequest import ajax_userrequest
from blueprints.ajax.store.paidrequest import ajax_paidrequest
from blueprints.ajax.store.creditrequest import ajax_creditrequest

from blueprints.admin.ajax.userrequest import admin_ajax_userrequest
from blueprints.admin.ajax.paidrequest import admin_ajax_paidrequest

from blueprints.admin.panel import admin_panel

from steamcommerce_api.api import user
from steamcommerce_api.core import models

BLUEPRINTS = [
    store,
    user_view,
    admin_view,
    admin_panel,
    testimonials,
    ajax_cart,
    ajax_search,
    ajax_products,
    ajax_userrequest,
    ajax_paidrequest,
    ajax_creditrequest,
    admin_ajax_userrequest,
    admin_ajax_paidrequest
]

app = Flask(__name__)

app.config.from_object(config)
app.logger.addHandler(config.LOG_HANDLER)

Bootstrap(app)

app.logger.info('Staring steamcommerce')


'''
Custom url_map
'''


class CustomIDConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(CustomIDConverter, self).__init__(url_map)
        self.regex = '[A-C]-[0-9]+'

    def to_python(self, value):
        id_type, id_number = value.split('-')
        return {'type': id_type, 'number': id_number}


app.jinja_env.add_extension('jinja2.ext.do')
app.url_map.converters['custom_id'] = CustomIDConverter


'''
Blueprint registration
'''

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
    if request.path[:7] == '/static':
        return

    g.db = models.database
    g.db.connect()

    session.permanent = True

    if session.get('user'):
        try:
            curr_user = user.User().get_by_id(session.get('user'))
        except user.User().model.DoesNotExist:
            # user had a value but was incorrect
            # highly unlikely (!)

            session.pop('user')

        if not curr_user.email or len(curr_user.email) < 1:
            register_url = url_for('views.user.user_register')

            if request.url_rule and request.url_rule.rule != register_url:
                return redirect(register_url)

        if curr_user.is_banned:
            session.pop('user')

            return render_template('views/user/banned.html', user=curr_user)

        if session.get('admin') and curr_user:
            if not curr_user.admin:
                # User had admin session but was not admin
                # on the database. Kick the session

                # TODO: Log event

                session.pop('user')
                session.pop('admin')

                curr_user = None

        user_id = session.get('user')

        cart.Cart().process_cart(user_id)
        user_cart = cart.Cart().get_user_cart(user_id)
        notifications = notification.Notification().get_for_user(user_id)

        g.user = curr_user
        g.user_cart = user_cart

        g.notification_counter = 0

        for user_notification in notifications:
            if not user_notification.seen:
                g.notification_counter += 1

        g.notifications = notifications[:10]

        g.pending_requests = userrequest.UserRequest().\
            get_user_not_informed_userrequests(
                user_id, lazy=True
            )


@app.after_request
def after_request(response):
    try:
        getattr(g, 'db')
    except AttributeError:
        return response

    g.db.close()

    return response


@app.template_filter()
def price_format(price):
    return '%.2f' % price


@app.template_filter()
def date_format(date):
    return date.strftime('%d/%m/%Y %H:%M')


@app.template_filter()
def css_file(filepath):
    return u'<link rel="stylesheet" type="text/css" href="{0}?{1}"/>'.format(
        filepath, config.CACHE_BREAK_RAND
    )


@app.template_filter()
def js_file(filepath):
    JAVASCRIPT_FMT = u'<script type="text/javascript" src="{0}?{1}">\
    </script>'

    return JAVASCRIPT_FMT.format(
        filepath, config.CACHE_BREAK_RAND
    )


def real_timesince(dt, default=u'hace momentos'):
    now = datetime.datetime.now()

    if type(dt) is int or type(dt) is float:
        diff = now - datetime.datetime.fromtimestamp(dt)
    else:
        diff = now - dt

    periods = (
        (diff.days / 365, u'año', u'años'),
        (diff.days / 30, u'mes', u'meses'),
        (diff.days / 7, u'semana', u'semanas'),
        (diff.days, u'día', u'días'),
        (diff.seconds / 3600, u'hora', u'horas'),
        (diff.seconds / 60, u'minuto', u'minutos'),
        (diff.seconds, u'segundo', u'segundos'),
    )

    for period, singular, plural in periods:
        if period:
            return u'hace %d %s' \
                   % (period, singular if period == 1 else plural)

    return default


@app.template_filter()
def timesince(dt):
    return real_timesince(dt)


@app.template_filter()
def as_json(data):
    return json_util.dumps(data)
