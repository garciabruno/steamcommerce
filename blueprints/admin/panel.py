#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import flash
from flask import url_for
from flask import request
from flask import redirect
from flask import Blueprint
from flask import render_template

import wtforms

from wtfpeewee.orm import model_form
from wtforms.validators import DataRequired

from steamcommerce_api.core import models
from utils import route_decorators

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


@admin_panel.route('/model/add/<model_name>')
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

    form = raw_form(obj=model())
    form.hidden_tag = do_nothing

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
