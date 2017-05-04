#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import g
from flask import flash
from flask import request
from flask import session
from flask import url_for
from flask import redirect
from flask import Blueprint
from flask import render_template

import os
import json

'''
Internal imports
'''

import config
from utils import route_decorators

from steamcommerce_api.api import user
from steamcommerce_api.api import slider
from steamcommerce_api.api import section
from steamcommerce_api.api import product
from steamcommerce_api.api import question
from steamcommerce_api.api import announce
from steamcommerce_api.api import testimonial
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import storepromotion

from inputs import store_inputs
from forms import user as user_form

import datetime


store = Blueprint('views.store', __name__)


@store.route('/comprar')
@store.route('/comprar/')
def store_old_route():
    return redirect('/')


@store.route('/faqs')
@store.route('/faqs/')
@store.route('/preguntas-frecuentes')
def store_faqs():
    questions = question.Question().get_active()

    return render_template(
        'views/store/faqs.html',
        questions=questions
    )


@store.route('/')
def store_catalog():
    return render_template('views/store/disabled.html')

    sliders = slider.Slider().get_active()
    sections = section.Section().get_active()
    products = product.Product().get_by_section(sections[0]['id'], 1)
    promotions = storepromotion.StorePromotion().get_active()
    promotion_products = []
    promotion_products_ids = []
    announces = announce.Announce().get_active()

    if len(promotions) > 0:
        promotion_products_ids = storepromotion.StorePromotion().get_products(
            promotions[0]['id'], 1
        )

    for promotion_product_id in promotion_products_ids:
        promotion_products.append(
            product.Product().get_id(
                promotion_product_id,
                excludes=[
                    'section',
                    'product_codes',
                    'product_tags',
                    'product_specs'
                ]
            )
        )

    user_id = session.get('user')

    pending_testimonials = []
    pending_requests_ids = []

    if user_id:
        pending_testimonials = testimonial.Testimonial().get_unsubmited(
            user_id,
            excludes=['all']
        )

        pending_requests_ids = userrequest.UserRequest().\
            _get_uninformed_by_user_id(
                user_id
            )

    template_params = {
        'page': 1,
        'section_id': sections[0]['id'],
        'sliders': sliders,
        'products': products,
        'announces': announces,
        'sections': sections,
        'promotions': promotions,
        'active_section': 'catalog',
        'show_sections': True,
        'pending_requests_ids': pending_requests_ids,
        'promotion_products': promotion_products,
        'pending_testimonials': pending_testimonials
    }

    return render_template(
        'views/store/catalog.html',
        **template_params
    )


@store.route('/products/', methods=['POST'])
def store_products():
    form = store_inputs.ProductsInput(request)

    if not form.validate():
        return 'Form does not validate. You piece of shit.'

    section_id = int(request.form.get('section'))
    page = int(request.form.get('page'))

    if not request.form.get('offers'):
        products = product.Product().get_by_section(section_id, page)

        if len(products) < 1:
            return json.dumps({'success': False}), 500

        params = {
            'page': page,
            'products': products,
            'section_id': section_id
        }

    else:
        promotion_products_ids = storepromotion.StorePromotion().get_products(
            section_id,
            page
        )

        if len(promotion_products_ids) < 1:
            return json.dumps({'success': False}), 500

        promotion_products = []

        for promotion_product_id in promotion_products_ids:
            promotion_products.append(
                product.Product().get_id(
                    promotion_product_id,
                    excludes=[
                        'section',
                        'product_codes',
                        'product_tags',
                        'product_specs'
                    ]
                )
            )

        params = {
            'page': page,
            'section_id': section_id,
            'products': promotion_products,
        }

    return render_template('views/store/products.html', **params)


@store.route('/ofertas')
def store_offers():
    spromotion = storepromotion.StorePromotion()
    sliders = slider.Slider().get_active()
    promotions = spromotion.get_active()
    announces = announce.Announce().get_active()

    if len(promotions) < 1:
        return redirect(url_for('views.store.store_catalog'))

    promotion_products = []
    promotion_products_ids = []

    if len(promotions) > 0:
        promotion_products_ids = spromotion.get_products(
            promotions[0]['id'],
            1
        )

    for promotion_product_id in promotion_products_ids:
        promotion_products.append(
            product.Product().get_id(
                promotion_product_id
            )
        )

    pending_testimonials = []
    pending_requests_ids = []

    user_id = session.get('user')

    if user_id:
        pending_testimonials = testimonial.Testimonial().get_unsubmited(
            user_id,
            excludes=['all']
        )

        pending_requests_ids = userrequest.UserRequest().\
            _get_uninformed_by_user_id(
                user_id
            )

    template_params = {
        'page': 1,
        'section_id': promotions[0]['id'],
        'sections': promotions,
        'promotions': promotions,
        'active_section': 'offers',
        'show_sections': True,
        'sliders': sliders,
        'announces': announces,
        'products': promotion_products,
        'pending_requests_ids': pending_requests_ids,
        'pending_testimonials': pending_testimonials
    }

    return render_template('views/store/catalog.html', **template_params)


@store.route('/liquidacion')
def store_sale():
    sections = []

    sliders = slider.Slider().get_active()
    announces = announce.Announce().get_active()
    products = product.Product().get_products_on_sale()

    template_params = {
        'page': 1,
        'products': products,
        'sections': sections,
        'sliders': sliders,
        'announces': announces,
        'section_id': 1,
        'show_sections': False,
        'active_section': 'on-sale',
    }

    return render_template('views/store/catalog.html', **template_params)


@store.route('/ofertas/<short_url>')
@store.route('/oferta/<short_url>')
def store_promotion_short_url(short_url):
    spromotion = storepromotion.StorePromotion()

    sliders = slider.Slider().get_active()
    announces = announce.Announce().get_active()
    promotions = spromotion.get_active()

    promotion_products = []
    promotion_products_ids = []

    promotion = spromotion.get_by_short_url(short_url)

    if not promotion:
        return redirect(url_for('views.store.store_catalog'))

    if (
        promotion['visibility_state'] == 1 and
        promotion['enabled'] and
        promotion['ending_date'] > datetime.datetime.now()
    ):
        promotion_products_ids = spromotion.get_products(promotion['id'], 1)

    for promotion_product_id in promotion_products_ids:
        promotion_products.append(
            product.Product().get_id(
                promotion_product_id
            )
        )

    pending_testimonials = []
    pending_requests_ids = []

    user_id = session.get('user')

    if user_id:
        pending_testimonials = testimonial.Testimonial().get_unsubmited(
            user_id,
            excludes=['all']
        )

        pending_requests_ids = userrequest.UserRequest().\
            _get_uninformed_by_user_id(
                user_id
            )

    template_params = {
        'page': 1,
        'selected_section': promotion['title'],
        'section_id': promotion['id'],
        'sections': promotions,
        'promotions': promotions,
        'active_section': 'offers',
        'sliders': sliders,
        'announces': announces,
        'products': promotion_products,
        'pending_requests_ids': pending_requests_ids,
        'pending_testimonials': pending_testimonials,
    }

    return render_template('views/store/catalog.html', **template_params)


@store.route('/comprar/<app_id>')
@store.route('/comprar/<app_id>/')
@store.route('/app/<app_id>')
@store.route('/app/<app_id>/')
def store_app_id(app_id):
    try:
        store_product = product.Product().get_app_id(app_id)
    except:
        store_product = None

    if store_product is None:
        error = {
            'title': 'Producto inexistente',
            'content': 'Este producto no existe en nuestra Base de Datos'
        }

        return render_template('views/error.html', **error)

    if not store_product.get('visible') and not session.get('admin'):
        error = {
            'title': 'Producto no disponible',
            'content': 'Este producto no se encuentra disponible temporalmente'
        }

        return render_template('views/error.html', **error)

    if (
        store_product.get('run_stock') and
        store_product.get('stock') == 0
        and not session.get('admin')
    ):
        error = {
            'title': 'Producto fuera de stock',
            'content': 'Este producto ha agotado su stock.'
        }

        return render_template('views/error.html', **error)

    params = {
        'product': store_product
    }

    if session.get('user'):
        spent_incomes = user.User().get_user_spent_incomes(session.get('user'))

        register_delta = datetime.datetime.now() - (
            g.user.get('register_date') or
            datetime.datetime(year=2012, month=8, day=1)
        )

        params.update({
            'spent_incomes': spent_incomes,
            'register_delta': register_delta
        })

    if store_product.get('product_type') == 3:
        return render_template('views/store/3dproduct.html', **params)

    return render_template('views/store/product.html', **params)


@store.route('/sub/<sub_id>')
@store.route('/sub/<sub_id>/')
def store_sub_id(sub_id):
    try:
        store_product = product.Product().get_sub_id(sub_id)
    except:
        store_product = None

    if store_product is None:
        error = {
            'title': 'Producto inexistente',
            'content': 'Este producto no existe en nuestra Base de Datos'
        }

        return render_template('views/error.html', **error)

    if not store_product.get('visible') and not session.get('admin'):
        error = {
            'title': 'Producto no disponible',
            'content': 'Este producto no se encuentra disponible temporalmente'
        }

        return render_template('views/error.html', **error)

    if (
        store_product.get('run_stock') and
        store_product.get('stock') == 0
        and not session.get('admin')
    ):
        error = {
            'title': 'Producto fuera de stock',
            'content': 'Este producto ha agotado su stock.'
        }

        return render_template('views/error.html', **error)

    params = {
        'product': store_product
    }

    if session.get('user'):
        spent_incomes = user.User().get_user_spent_incomes(session.get('user'))

        register_delta = datetime.datetime.now() - (
            g.user.get('register_date') or
            datetime.datetime(year=2012, month=8, day=1)
        )

        params.update({
            'spent_incomes': spent_incomes,
            'register_delta': register_delta
        })

    if store_product.get('product_type') == 3:
        return render_template('views/store/3dproduct.html', **params)

    return render_template('views/store/product.html', **params)


@store.route('/buscar')
@store.route('/buscador')
def store_search():
    sliders = slider.Slider().get_active()

    params = {
        'sliders': sliders,
        'active_section': 'search'
    }

    return render_template('views/store/search.html', **params)


@store.route('/soporte')
def store_support():
    return render_template('views/store/support.html')


@store.route('/reservas', methods=['GET', 'POST'])
@store.route('/reservas/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
def store_reservations():
    if request.method == 'GET':
        pending_requests = userrequest.UserRequest().get_uninformed_by_user_id(
            session.get('user'), excludes=['userrequest_messages']
        )

        params = {
            'pending_requests': pending_requests,
            'active_section': 'reservations'
        }

        return render_template('views/store/reservations.html', **params)
    elif request.method == 'POST':
        form = user_form.ReservationForm(request.form, csrf_enabled=False)

        if not form.validate():
            return redirect(url_for('views.store.store_reservations'))

        request_id = int(form.request_id.data)

        pending_requests_ids = userrequest.UserRequest().\
            _get_uninformed_by_user_id(
                session.get('user')
            )

        if not request_id in pending_requests_ids:
            return redirect(url_for('views.store.store_reservations'))

        if not request.files.get('image'):
            flash(
                ('danger', u'El formulario no contiene una imagen adjuntada')
            )

            return render_template('views/store/reservations.html')

        stream = request.files.get('image').stream.read()

        if len(stream) > config.MAX_IMAGE_BYTES_SIZE:
            flash(('danger', u'El archivo adjuntado supera los 5 MB'))

            return render_template('views/store/reservations.html')

        if request.files.get('image').mimetype not in config.ALLOWED_MIMETYPES:
            flash(('danger', u'El formato de la imagen no está permitido'))

            return render_template('views/store/reservations.html')

        image = request.files['image']
        filename = '{0}.{1}'.format(request_id, image.filename.split('.')[-1])

        UPLOAD_PATH = os.path.join(
            config.UPLOAD_DIRECTORY, 'userrequests', filename
        )

        f = open(UPLOAD_PATH, 'wb')
        f.write(stream)
        f.close()

        userrequest.UserRequest().set_informed(request_id, filename)

        pending_requests = userrequest.UserRequest().get_uninformed_by_user_id(
            session.get('user'), excludes=['userrequest_messages']
        )

        flash(
            (
                'success',
                u'Pedido #A-{0} reservado exitosamente'.format(
                    request_id
                )
            )
        )

        params = {
            'pending_requests': pending_requests,
            'active_section': 'reservations'
        }

        return render_template('views/store/reservations.html', **params)


@store.route('/reservas/cancelar', methods=['GET', 'POST'])
@route_decorators.is_logged_in
def store_cancel_reservations():
    if request.method == 'GET':
        pending_requests = userrequest.UserRequest().get_uninformed_by_user_id(
            session.get('user'), excludes=['userrequest_messages']
        )

        params = {
            'pending_requests': pending_requests,
            'active_section': 'cancel_reservations'
        }

        return render_template(
            'views/store/cancel_reservations.html',
            **params
        )
    elif request.method == 'POST':
        form = user_form.ReservationForm(request.form, csrf_enabled=False)

        if not form.validate():
            return redirect(url_for('views.store.store_cancel_reservations'))

        request_id = int(form.request_id.data)

        pending_requests_ids = userrequest.UserRequest().\
            _get_uninformed_by_user_id(
                session.get('user')
            )

        if not request_id in pending_requests_ids:
            return redirect(url_for('views.store.store_cancel_reservations'))

        userrequest.UserRequest().set_cancelled(request_id)

        pending_requests = userrequest.UserRequest().get_uninformed_by_user_id(
            session.get('user'), excludes=['userrequest_messages']
        )

        flash(
            (
                'success',
                u'Pedido #A-{0} cancelado exitosamente'.format(
                    request_id
                )
            )
        )

        params = {
            'pending_requests': pending_requests,
            'active_section': 'cancel_reservations'
        }

        return render_template(
            'views/store/cancel_reservations.html',
            **params
        )


@store.route('/app/<int:app_id>/comprar')
@route_decorators.is_logged_in
def app_checkout(app_id):
    try:
        store_product = product.Product().get_app_id(app_id)
    except:
        store_product = None

    params = {
        'product': store_product
    }

    return render_template('views/store/checkout.html', **params)
