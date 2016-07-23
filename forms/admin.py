#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import wtforms

from flask_wtf import Form
from wtforms.validators import DataRequired
from wtforms.validators import Optional


class ProductCodeForm(Form):
    product_id = wtforms.HiddenField(validators=[DataRequired()])
    code = wtforms.TextAreaField(validators=[DataRequired()])
    submit = wtforms.SubmitField(validators=[DataRequired()])


class ProductPriceForm(Form):
    product_id = wtforms.HiddenField(validators=[DataRequired()])
    price = wtforms.FloatField(validators=[DataRequired()])
    price_type = wtforms.IntegerField(validators=[DataRequired()])
    currency = wtforms.TextField(validators=[Optional()])
    active = wtforms.BooleanField(
        validators=[DataRequired()],
        default=True
    )
    submit = wtforms.SubmitField(validators=[DataRequired()])


class SteamProduct(Form):
    sub_id = wtforms.IntegerField(validators=[Optional()])
    app_id = wtforms.IntegerField(validators=[Optional()])

    submit = wtforms.SubmitField(validators=[DataRequired()])


class ResumeForm(Form):
    start_date = wtforms.DateTimeField(
        u'Fecha de inicio',
        validators=[DataRequired()],
        format='%d/%m/%Y %H:%M'
    )

    end_date = wtforms.DateTimeField(
        u'Fecha de finalización',
        validators=[DataRequired()],
        format='%d/%m/%Y %H:%M'
    )

    commerce_id = wtforms.BooleanField(
        u'CuentaDigital Emiliano',
        validators=[Optional()],
        default=False
    )

    userrequests = wtforms.BooleanField(
        u'Mostrar pedidos de boleta',
        validators=[Optional()],
        default=True
    )

    paidrequests = wtforms.BooleanField(
        u'Mostrar pedidos de créditos',
        validators=[Optional()],
        default=True
    )

    user_id = wtforms.SelectField(
        u'Administrador',
        choices=[
            (1, 'nin'),
            (2, 'Emiliano'),
            (7102, 'pety99'),
            (19548, 'paueg')
        ],
        coerce=int
    )

    submit = wtforms.SubmitField(u'Enviar', validators=[DataRequired()])
