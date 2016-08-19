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
from flask import Request

from werkzeug.routing import BaseConverter
from flask_bootstrap import Bootstrap

import os
import rollbar
import rollbar.contrib.flask

from flask import got_request_exception

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
from blueprints.admin.ajax.creditrequest import admin_ajax_creditrequest
from blueprints.admin.ajax.paidrequest import admin_ajax_paidrequest

from blueprints.admin.panel import admin_panel

from steamcommerce_api.api import user
from steamcommerce_api.api import notification

from steamcommerce_api.core import models
from steamcommerce_api.utils import json_util


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
    admin_ajax_paidrequest,
    admin_ajax_creditrequest
]

app = Flask(__name__)

app.config.from_object(config)
app.secret_key = config.SECRET_KEY
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


if not config.DEBUG:
    @app.before_first_request
    def init_rollbar():
        """init rollbar module"""

        rollbar.init(
            config.ROLLBAR_TOKEN,
            'env',
            root=os.path.dirname(os.path.realpath(__file__)),
            allow_logging_basic_config=False
        )

        # send exceptions from `app` to rollbar, using flask's signal system.

        got_request_exception.connect(
            rollbar.contrib.flask.report_exception,
            app
        )


class CustomRequest(Request):
    @property
    def rollbar_person(self):
        return {
            'id': session.get('user')
        }

app.request_class = CustomRequest


@app.before_request
def before_request():
    session.permanent = True

    if request.path[:7] == '/static':
        return

    g.db = models.database
    g.db.connect()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return

    if session.get('user'):
        if not session.get('email'):
            register_url = url_for('views.user.user_register')

            if request.url_rule and request.url_rule.rule != register_url:
                return redirect(register_url)

        user_id = session.get('user')

        g.notification_counter = notification.Notification().\
            get_user_unseen_notifications(user_id)

        user_data = user.User().get_by_id(user_id)
        g.user = user_data

        avatar_url = user.User().get_user_avatar_url(user_data['steam'])

        if user_data['avatar_url'] != avatar_url:
            user.User().update(**{
                'id': user_id,
                'avatar_url': avatar_url
            })

            user_data['avatar_url'] = avatar_url


@app.after_request
def after_request(response):
    try:
        getattr(g, 'db')
    except AttributeError:
        return response

    if not g.db.is_closed():
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
    JAVASCRIPT_FMT = u'<script type="text/javascript" src="{0}?{1}"></script>'

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


@app.template_filter()
def timeuntil(dt):
    return real_timeuntil(dt)


def real_timeuntil(dt, default='en momentos'):
    now = datetime.datetime.now()
    diff = dt - now

    if now > dt:
        return real_timesince(dt)

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
            return u'%d %s' \
                   % (period, singular if period == 1 else plural)

    return default


def parse_plural(value, (singular, plural)):
    if value == 1:
        return singular
    else:
        return plural


def filter_periods(periods):
    result = []

    for period, singular, plural in periods:
        if period > 0:
            result.append((period, singular, plural))

    return result


@app.template_filter()
def hour_format(date, default=u'menos de un segundo'):
    days = date.days
    hours = date.seconds / 3600
    minutes = (date.seconds / 60) - (hours * 60)
    seconds = date.seconds - (minutes * 60) - (hours * 60 * 60)

    periods = (
        (days, u'día', u'días'),
        (hours, u'hora', u'horas'),
        (minutes, u'minuto', u'minutos'),
        (seconds, u'segundo', u'segundos'),
    )

    result = None

    for period, singular, plural in periods:
        if period > 0 and not result:
            word = parse_plural(period, (singular, plural))
            result = '%d %s' % (period, word)

    if result is not None:
        return result

    return default
