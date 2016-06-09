#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import request
from flask import session
from flask import Blueprint

from inputs import store_inputs
from utils import route_decorators

from steamcommerce_api import config

from steamcommerce_api.api import user
from steamcommerce_api.api import cart
from steamcommerce_api.api import message
from steamcommerce_api.api import history
from steamcommerce_api.api import product
from steamcommerce_api.api import productcode
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import testimonial
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import notification

import datetime
import constants

ajax_paidrequest = Blueprint('ajax.store.paidrequest', __name__)


@ajax_paidrequest.route('/generate/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.as_json
def ajax_paidrequest_generate():
    user_id = session.get('user')
    form = store_inputs.PaidRequestInput(request)

    if not form.validate():
        return ({'success': False, 'status': 0}, 422)

    product_id = int(request.form.get('product_id'))
    product_data = product.Product().get_product_by_id(product_id)

    if product_data is None:
        return ({'success': False, 'status': 1}, 500)

    if not product_data.get('visible'):
        return ({'success': False, 'status': 2}, 500)

    if not product_data.get('price'):
        return ({'success': False, 'status': 3}, 500)

    price = product_data.get('price').get('price')
    user_data = user.User().get_by_id(user_id)

    if (user_data.money + user_data.wallet) < price:
        return ({'success': False, 'status': 4}, 500)

    if product_data.get('run_stock') and product_data.get('stock') == 0:
        return ({'success': False, 'status': 5}, 500)

    if user_data.money >= price:
        commerce_id = config.CUENTADIGITAL_EMILIANO_ID
    else:
        commerce_id = config.CUENTADIGITAL_NIN_ID

    invoice = paidrequest.PaidRequest().generate(
        user_id,
        price,
        [product_id],
        commerce_id
    )

    # TODO: Move functionality to API.

    request_id = invoice.get('paidrequest')

    if not invoice.get('success'):
        return (invoice, 500)

    if user_data.money >= price:
        user.User().decrease_money(user_id, price)
    elif user_data.money > 0:
        user.User().decrease_money(user_id, user_data.money)
        user.User().decrease_wallet(user_id, price - user_data.money)
    else:
        user.User().decrease_wallet(user_id, price)

    history.History().push(
        constants.HISTORY_GENERATED_STATE,
        request_id,
        constants.HISTORY_PAIDREQUEST_TYPE
    )

    notification.Notification().push(
        user_id,
        constants.NOTIFICATION_PAIDREQUEST_DONE,
        **{
            'product': product_id,
            'paidrequest': request_id,
        }
    )

    if (
        product_data.get('product_type') == 2
        and len(product_data.get('codes')) > 0
    ):
        code = product_data.get('codes')[0]

        productcode.ProductCode().update(**{
            'id': code.get('id'),
            'paidrequest': request_id,
            'sent': True
        })

        message_content = constants.DEFAULT_REQUEST_MESSAGE + code.get('code')

        message.Message().push(**{
            'user': code.get('user_owner'),
            'to_user': user_id,
            'has_code': True,
            'paidrequest': request_id,
            'content': message_content
        })

        adminlog.AdminLog().push(
            constants.ADMINLOG_CODE_DELIVERED, **{
                'paidrequest': request_id
            }
        )

        notification.Notification().push(
            user_id,
            constants.NOTIFICATION_MESSAGE_RECEIVED,
            **{
                'paidrequest': invoice.get('paidrequest')
            })

        paidrequest.PaidRequest().accept_paidrequest(
            request_id, user_id=code.get('user_owner')
        )

        history.History().push(
            constants.HISTORY_ACCEPTED_STATE,
            request_id,
            constants.HISTORY_PAIDREQUEST_TYPE
        )

        adminlog.AdminLog().push(
            constants.ADMINLOG_PAIDREQUEST_ACCEPTED, **{
                'paidrequest': request_id,
                'user': user_id
            }
        )

        notification.Notification().push(
            user_id,
            constants.NOTIFICATION_PAIDREQUEST_ACCEPTED,
            **{'paidrequest': request_id}
        )

        testimonial.Testimonial().create(**{
            'user': user_id,
            'paidrequest': request_id,
            'date': datetime.datetime.now()
        })

        if len(product_data.get('codes')) == 1:
            product.Product().update(**{
                'id': product_id,
                'product_type': 1
            })

        invoice.update({'instant': True, 'message': message_content})

    return invoice


@ajax_paidrequest.route('/cart/generate/', methods=['POST'])
@route_decorators.ajax_is_logged_in
@route_decorators.as_json
def ajax_paidrequest_cart_generate():
    user_id = session.get('user')

    cart.Cart().process_cart(user_id)

    user_cart = cart.Cart().get_user_cart(user_id)
    user_data = user.User().get_by_id(user_id)

    if len(user_cart.get('items')) == 0:
        return ({'success': False, 'status': 0}, 500)

    if not user_cart.get('prices').get('credit'):
        return ({'success': False, 'status': 1}, 500)

    price = user_cart.get('prices').get('credit')

    if (user_data.money + user_data.wallet) < price:
        return ({'success': False, 'status': 2}, 500)

    if user_data.money >= price:
        commerce_id = config.CUENTADIGITAL_EMILIANO_ID
    else:
        commerce_id = config.CUENTADIGITAL_NIN_ID

    invoice = paidrequest.PaidRequest().generate(
        user_id,
        price,
        [x.get('product').get('id') for x in user_cart.get('items')],
        commerce_id
    )

    if not invoice.get('success'):
        return (invoice, 500)

    if user_data.money >= price:
        user.User().decrease_money(user_id, price)
    elif user_data.money > 0:
        user.User().decrease_money(user_id, user_data.money)
        user.User().decrease_wallet(user_id, price - user_data.money)
    else:
        user.User().decrease_wallet(user_id, price)

    cart.Cart().empty_user_cart(user_id)

    history.History().push(
        constants.HISTORY_GENERATED_STATE,
        invoice.get('paidrequest'),
        constants.HISTORY_PAIDREQUEST_TYPE
    )

    for item in user_cart.get('items'):
        notification.Notification().push(
            user_id,
            constants.NOTIFICATION_PAIDREQUEST_DONE,
            **{
                'product': item.get('product').get('id'),
                'paidrequest': invoice['paidrequest']
            }
        )

    return invoice
