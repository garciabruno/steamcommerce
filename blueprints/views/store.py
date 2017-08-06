#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import redirect
from flask import Blueprint
from flask import render_template

'''
Internal imports
'''


from utils import route_decorators


store = Blueprint('views.store', __name__)


@store.route('/comprar')
@store.route('/comprar/')
def store_old_route():
    return redirect('/')


@store.route('/faqs')
@store.route('/faqs/')
@store.route('/preguntas-frecuentes')
def store_faqs():
    return redirect('/')


@store.route('/')
def store_catalog():
    return render_template('views/closed.html')


@store.route('/ofertas')
def store_offers():
    return redirect('/')


@store.route('/liquidacion')
def store_sale():
    return redirect('/')


@store.route('/comprar/<app_id>')
@store.route('/comprar/<app_id>/')
@store.route('/app/<app_id>')
@store.route('/app/<app_id>/')
def store_app_id(app_id):
    return redirect('/')


@store.route('/sub/<sub_id>')
@store.route('/sub/<sub_id>/')
def store_sub_id(sub_id):
    return redirect('/')


@store.route('/buscar')
@store.route('/buscador')
def store_search():
    return redirect('/')


@store.route('/soporte')
def store_support():
    return redirect('/')


@store.route('/reservas', methods=['GET', 'POST'])
@store.route('/reservas/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
def store_reservations():
    return redirect('/')


@store.route('/app/<int:app_id>/comprar')
@route_decorators.is_logged_in
def app_checkout(app_id):
    return redirect('/')
