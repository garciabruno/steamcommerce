#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import flash
from flask import url_for
from flask import request
from flask import session
from flask import redirect
from flask import Blueprint
from flask import render_template

from forms import admin
from steamcommerce_api.core import models

from steamcommerce_api.api import product
from steamcommerce_api.api import message
from steamcommerce_api.api import history
from steamcommerce_api.api import adminlog
from steamcommerce_api.api import testimonial
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import productcode
from steamcommerce_api.api import notification

import constants

from wtforms.validators import DataRequired

import wtforms
from wtfpeewee.orm import model_form
from utils import route_decorators

import datetime

admin_panel = Blueprint('admin.panel', __name__)


def do_nothing():
    return ''


@admin_panel.route('/')
@route_decorators.is_admin
def admin_root():
    params = {
        'models': models.models_list
    }

    return render_template('admin/panel/dashboard.html', **params)


@admin_panel.route('/model/<model_name>')
@route_decorators.is_admin
def admin_model_view(model_name):
    if model_name not in [x.__name__ for x in models.models_list]:
        flash('Modelo inexistente')
        return redirect(url_for('admin.panel.admin_root'))

    page = request.args.get('page', 1)

    try:
        page = int(page)
        page = max(1, page)
    except ValueError:
        page = 1

    model = models.models_dict[model_name]

    query = model.select().paginate(page, 25).order_by(model.id.asc())

    raw_form = model_form(model, exclude=model.Admin.excludes)
    form = raw_form(obj=model())

    params = {
        'page': page,
        'form': form,
        'query': query,
        'model': model,
        'model_name': model_name,
        'models': models.models_list
    }

    return render_template('admin/panel/model-view.html', **params)


@admin_panel.route('/model/add/<model_name>', methods=['GET', 'POST'])
@route_decorators.is_admin
def admin_model_add(model_name):
    if model_name not in [x.__name__ for x in models.models_list]:
        flash('Modelo inexistente')
        return redirect(url_for('admin.panel.admin_root'))

    model = models.models_dict.get(model_name)

    if 'add' not in model.Admin.actions:
        return redirect(url_for('admin.panel.admin_root'))

    raw_form = model_form(model, exclude=model.Admin.excludes)
    raw_form.submit = wtforms.SubmitField(
        'Enviar', validators=[DataRequired()]
    )

    if request.method == 'GET':
        form = raw_form(obj=model())
        form.hidden_tag = do_nothing

        params = {
            'form': form,
            'model_name': model_name,
            'models': models.models_list
        }
    elif request.method == 'POST':
        new_model = model()
        form = raw_form(request.form, obj=new_model)
        form.hidden_tag = do_nothing

        if form.validate():
            form.populate_obj(new_model)
            new_model.save()
            flash('Objecto creado satisfactoriamente')

        params = {
            'form': form,
            'model_name': model_name,
            'models': models.models_list
        }

    return render_template('admin/panel/model-form.html', **params)


@admin_panel.route(
    '/model/edit/<model_name>/<int:object_id>', methods=['GET', 'POST']
)
@route_decorators.is_admin
def admin_model_edit(model_name, object_id):
    if model_name not in [x.__name__ for x in models.models_list]:
        flash('Modelo inexistente')
        return redirect(url_for('admin.panel.admin_root'))

    model = models.models_dict.get(model_name)

    if 'edit' not in model.Admin.actions:
        return redirect(url_for('admin.panel.admin_root'))

    raw_form = model_form(model, exclude=model.Admin.excludes)
    raw_form.submit = wtforms.SubmitField(
        'Enviar', validators=[DataRequired()]
    )

    if request.method == 'GET':
        form = raw_form(obj=model.get(id=object_id))
        form.hidden_tag = do_nothing

        params = {
            'form': form,
            'model_name': model_name,
            'models': models.models_list
        }

        return render_template('admin/panel/model-form.html', **params)
    elif request.method == 'POST':
        _object = model.get(id=object_id)

        form = raw_form(request.form, obj=_object)
        form.hidden_tag = do_nothing

        params = {
            'form': form,
            'model_name': model_name,
            'models': models.models_list
        }

        if not form.validate():
            return render_template('admin/panel/model-form.html', **params)

        form.populate_obj(_object)
        _object.save()

        flash('Objecto actualizado satisfactoriamente')
        return render_template('admin/panel/model-form.html', **params)


@admin_panel.route(
    '/product/add/code/<int:product_id>',
    methods=['GET', 'POST']
)
@route_decorators.is_admin
def admin_panel_add_code(product_id):
    if request.method == 'GET':
        form = admin.ProductCodeForm()
        form.product_id.data = product_id

        params = {
            'form': form
        }

        return render_template('admin/panel/generic-form.html', **params)
    elif request.method == 'POST':
        form = admin.ProductCodeForm(request.form)

        if not form.validate():
            params = {
                'form': form
            }

            return render_template('admin/panel/generic-form.html', **params)

        user_id = session.get('user')
        product_id = int(form.product_id.data)
        code_content = form.code.data

        code_id = productcode.ProductCode().create_code(
            code_content, product_id, user_id
        )

        flash(constants.PRODUCTCODE_ADDED.format(code_id))

        code = productcode.ProductCode().get_id(code_id)
        admin_id = code.user_owner

        adminlog.AdminLog().push(
            constants.ADMINLOG_CODE_ADDED, **{
                'product': product_id,
                'user': admin_id
            }
        )

        paidrequests = paidrequest.PaidRequest().get_paid_paidrequests()
        code_added = False

        new_form = admin.ProductCodeForm()
        new_form.product_id.data = product_id

        params = {
            'form': new_form
        }

        for paidrequest_data in paidrequests:
            relations = paidrequest_data.get('relations')

            if len(relations) != 1:
                continue

            if relations[0].get('product').get('id') != product_id:
                continue

            # The newly added code can be delivered instantly

            request_id = paidrequest_data.get('id')

            productcode.ProductCode().update(**{
                'id': code.id,
                'paidrequest': request_id,
                'sent': True
            })

            message_content = constants.DEFAULT_REQUEST_MESSAGE + code.code

            message.Message().push(**{
                'user': admin_id,
                'to_user': paidrequest_data.get('user').get('id'),
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
                paidrequest_data.get('user').get('id'),
                constants.NOTIFICATION_MESSAGE_RECEIVED,
                **{
                    'paidrequest': request_id
                })

            paidrequest.PaidRequest().accept_paidrequest(
                request_id,
                user_id=admin_id
            )

            history.History().push(
                constants.HISTORY_ACCEPTED_STATE,
                request_id,
                constants.HISTORY_PAIDREQUEST_TYPE
            )

            adminlog.AdminLog().push(
                constants.ADMINLOG_PAIDREQUEST_ACCEPTED, **{
                    'paidrequest': request_id,
                    'user': admin_id
                }
            )

            notification.Notification().push(
                paidrequest_data.get('user').get('id'),
                constants.NOTIFICATION_PAIDREQUEST_ACCEPTED,
                **{'paidrequest': request_id}
            )

            testimonial.Testimonial().create(**{
                'user': paidrequest_data.get('user').get('id'),
                'paidrequest': request_id,
                'date': datetime.datetime.now()
            })

            if len(relations[0].get('product').get('codes')) == 1:
                product.Product().update(**{
                    'id': product_id,
                    'product_type': 1
                })

            flash(
                constants.PRODUCTCODE_ADDED_TO_REQUEST.format('C', request_id)
            )

            code_added = True

            break

        if code_added:
            return render_template('admin/panel/generic-form.html', **params)

        userrequests = userrequest.UserRequest().get_paid_userrequests()

        for userrequest_data in userrequests:
            relations = userrequest_data.get('relations')

            if len(relations) != 1:
                continue

            if relations[0].get('product').get('id') != product_id:
                continue

            # The newly added code can be delivered instantly

            request_id = userrequest_data.get('id')

            productcode.ProductCode().update(**{
                'id': code.id,
                'userrequest': request_id,
                'sent': True
            })

            message_content = constants.DEFAULT_REQUEST_MESSAGE + code.code

            message.Message().push(**{
                'user': admin_id,
                'to_user': userrequest_data.get('user').get('id'),
                'has_code': True,
                'userrequest': request_id,
                'content': message_content
            })

            adminlog.AdminLog().push(
                constants.ADMINLOG_CODE_DELIVERED, **{
                    'userrequest': request_id
                }
            )

            notification.Notification().push(
                userrequest_data.get('user').get('id'),
                constants.NOTIFICATION_MESSAGE_RECEIVED,
                **{
                    'userrequest': request_id
                })

            userrequest.UserRequest().accept_userrequest(
                request_id,
                user_id=admin_id
            )

            history.History().push(
                constants.HISTORY_ACCEPTED_STATE,
                request_id,
                constants.HISTORY_USERREQUEST_TYPE
            )

            adminlog.AdminLog().push(
                constants.ADMINLOG_USERREQUEST_ACCEPTED, **{
                    'userrequest': request_id,
                    'user': admin_id
                }
            )

            notification.Notification().push(
                userrequest_data.get('user').get('id'),
                constants.NOTIFICATION_USERREQUEST_ACCEPTED,
                **{'userrequest': request_id}
            )

            testimonial.Testimonial().create(**{
                'user': userrequest_data.get('user').get('id'),
                'userrequest': request_id,
                'date': datetime.datetime.now()
            })

            if len(relations[0].get('product').get('codes')) == 1:
                product.Product().update(**{
                    'id': product_id,
                    'product_type': 1
                })

            flash(
                constants.PRODUCTCODE_ADDED_TO_REQUEST.format('A', request_id)
            )

            break

        return render_template('admin/panel/generic-form.html', **params)
