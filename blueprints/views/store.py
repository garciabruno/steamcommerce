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

import sys
import os
import json
import logging

'''
Internal imports
'''

import config
from utils import route_decorators

from steamcommerce_api.api import slider
from steamcommerce_api.api import section
from steamcommerce_api.api import product
from steamcommerce_api.api import question
from steamcommerce_api.api import announce
from steamcommerce_api.api import testimonial
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import configuration
from steamcommerce_api.api import storepromotion

from inputs import store_inputs
from forms import user as user_form

log = logging.getLogger('[Store]')

log.setLevel(logging.DEBUG)
format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

ch = logging.StreamHandler(sys.stdout)
fh = logging.FileHandler(
    os.path.join(
        config.LOG_PATH,
        'store.log'
    )
)

ch.setFormatter(format)
fh.setFormatter(format)

log.addHandler(ch)
log.addHandler(fh)


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
    return render_template('views/store/faqs.html', questions=questions)


@store.route('/catalogo')
def store_catalog():
    sliders = slider.Slider().get_active()
    sections = section.Section().get_active()
    products = product.Product().get_by_section(sections[0].id, 1)
    promotions = storepromotion.StorePromotion().get_active_promotions()
    promotion_products = []
    promotion_products_ids = []
    announces = announce.Announce().get_active()

    if len(promotions) > 0:
        promotion_products_ids = storepromotion.StorePromotion().\
            get_promotion_products(promotions[0].id, 1)

    for promotion_product_id in promotion_products_ids:
        promotion_products.append(
            product.Product().get_product_by_id(
                promotion_product_id
            )
        )

    user_id = session.get('user')

    pending_testimonials = []

    if user_id:
        pending_testimonials = testimonial.Testimonial().get_unsubmited(
            user_id, lazy=True
        )

    template_params = {
        'page': 1,
        'section_id': sections[0].id,
        'sliders': sliders,
        'products': products,
        'announces': announces,
        'sections': sections,
        'promotions': promotions,
        'active_section': 'catalog',
        'promotion_products': promotion_products,
        'pending_testimonials': pending_testimonials
    }

    return render_template('views/store/catalog.html', **template_params)


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
        promotion_products_ids = storepromotion.StorePromotion().\
            get_promotion_products(
                section_id, page
            )

        if len(promotion_products_ids) < 1:
            return json.dumps({'success': False}), 500

        promotion_products = []

        for promotion_product_id in promotion_products_ids:
            promotion_products.append(
                product.Product().get_product_by_id(promotion_product_id)
            )

        params = {
            'page': page,
            'section_id': section_id,
            'products': promotion_products,
        }

    return render_template('views/store/products.html', **params)


#@store.route('/ofertas')
@store.route('/')
def store_offers():
    spromotion = storepromotion.StorePromotion()
    sliders = slider.Slider().get_active()
    promotions = spromotion.get_active_promotions()

    if len(promotions) < 1:
        return redirect(url_for('views.store.store_catalog'))

    promotion_products = []
    promotion_products_ids = []

    if len(promotions) > 0:
        promotion_products_ids = spromotion.get_promotion_products(
            promotions[0].id,
            1
        )

    for promotion_product_id in promotion_products_ids:
        promotion_products.append(
            product.Product().get_product_by_id(
                promotion_product_id
            )
        )

    pending_testimonials = []
    user_id = session.get('user')

    if user_id:
        pending_testimonials = testimonial.Testimonial().get_unsubmited(
            user_id, lazy=True
        )

    template_params = {
        'page': 1,
        'section_id': promotions[0].id,
        'sections': promotions,
        'promotions': promotions,
        'active_section': 'offers',
        'sliders': sliders,
        'products': promotion_products,
        'pending_testimonials': pending_testimonials
    }

    return render_template('views/store/catalog.html', **template_params)


@store.route('/tienda/<app_id>')
@store.route('/catalogo/<app_id>')
@store.route('/comprar/<app_id>/')
def store_app_id(app_id):
    app_product = product.Product().get_by_app_id(app_id)

    if app_product is None:
        app_product = product.Product().get_by_sub_id(app_id)

    if app_product is None:
        error = {
            'title': 'Producto inexistente',
            'content': 'Este producto no existe :( Solicitalo?\
             https://facebook.com/ExtremeGamingSTEAM'
        }

        return render_template('views/error.html', **error)

    if not app_product.get('visible'):
        error = {
            'title': 'Producto no disponible',
            'content': 'Este producto no se encuentra disponible temporalmente'
        }

        return render_template('views/error.html', **error)

    if app_product.get('run_stock') and app_product.get('stock') == 0:
        error = {
            'title': 'Producto fuera de stock',
            'content': 'Este producto ha agotado su stock. \
            Disculpe las molestias.'
        }

        return render_template('views/error.html', **error)

    params = {
        'product': app_product
    }

    return render_template('views/store/product.html', **params)


@store.route('/buscar')
@store.route('/buscador')
def store_search():
    params = {
        'active_section': 'search'
    }

    return render_template('views/store/search.html', **params)


@store.route('/reservas', methods=['GET', 'POST'])
@store.route('/reservas/', methods=['GET', 'POST'])
@route_decorators.is_logged_in
def store_reservations():
    if request.method == 'GET':
        return render_template('views/store/reservations.html')
    elif request.method == 'POST':
        form = user_form.ReservationForm(request.form, csrf_enabled=False)

        if not form.validate():
            return redirect(url_for('views.store.store_reservations'))

        request_id = int(form.request_id.data)

        if not request_id in [x.get('id') for x in g.pending_requests]:
            return redirect(url_for('views.store.store_reservations'))

        if not request.files.get('image'):
            flash('El formulario no contiene una imagen adjuntada')
            return render_template('views/store/reservations.html')

        upload_count = configuration.Configuration().get_config(
            'reservations/uploads/{}'.format(session.get('user'))
        )

        if upload_count and upload_count > 10:
            flash('Has superado el limite de reservas. Intenta mas tarde')
            return render_template('views/store/reservations.html')

        stream = request.files.get('image').stream.read()

        if len(stream) > config.MAX_IMAGE_BYTES_SIZE:
            configuration.Configuration().set_config(
                'reservations/uploads/{}'.format(session.get('user')),
                (upload_count or 0) + 1,
                timeout=1 * 60 * 60
            )

            flash('El archivo adjuntado supera los 5MB')
            return render_template('views/store/reservations.html')

        if request.files.get('image').mimetype not in config.ALLOWED_MIMETYPES:
            flash(u'El formato de la imagen no está permitido')
            return render_template('views/store/reservations.html')

        configuration.Configuration().set_config(
            'reservations/uploads/{}'.format(session.get('user')),
            (upload_count or 0) + 1,
            timeout=1 * 60 * 60
        )

        image = request.files['image']
        filename = '{0}.{1}'.format(request_id, image.filename.split('.')[1])

        UPLOAD_PATH = os.path.join(
            config.UPLOAD_DIRECTORY, 'userrequests', filename
        )

        f = open(UPLOAD_PATH, 'wb')
        f.write(stream)
        f.close()

        userrequest.UserRequest().set_informed(request_id, filename)
        g.pending_requests = userrequest.UserRequest().\
            get_user_not_informed_userrequests(
                session.get('user'), lazy=True
            )

        flash('Pedido reservado satisfactoriamente')
        return render_template('views/store/reservations.html')
