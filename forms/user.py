#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask_wtf import Form

import constants

from wtforms.validators import Email
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import DataRequired

from wtforms import TextField
from wtforms import HiddenField
from wtforms import SubmitField
from wtforms import SelectField
from wtforms import BooleanField
from wtforms import IntegerField

from steamcommerce_api.core import models

PROVINCE_CHOICES = [('', 'Seleccionar Provincia')]

PROVINCE_CHOICES += [
    (x.letter, x.name) for x in models.Province.select().order_by(
        models.Province.name.asc()
    )
]


class RegisterForm(Form):
    email_validator = [
        DataRequired(
            message=constants.FIELD_REQUIRED
        ),
        Length(
            min=4,
            max=100,
            message=constants.FIELD_LENGTH_INVALID),
        Email(
            message=constants.FIELD_NOT_EMAIL
        )
    ]

    email = TextField(u'Dirección de email', validators=email_validator)

    submit = SubmitField('Enviar', validators=[DataRequired()])


class ProfileForm(Form):
    email_validator = [
        DataRequired(
            message=constants.FIELD_REQUIRED
        ),
        Length(
            min=4,
            max=100,
            message=constants.FIELD_LENGTH_INVALID),
        Email(
            message=constants.FIELD_NOT_EMAIL
        )
    ]

    email = TextField(u'Dirección de email', validators=email_validator)
    name = TextField(u'Nombre', validators=[DataRequired()])
    last_name = TextField(u'Apellido', validators=[DataRequired()])

    submit = SubmitField('Enviar', validators=[DataRequired()])


class ReservationForm(Form):
    request_id = HiddenField(u'request_id', validators=[DataRequired()])


class TestimonialsForm(Form):
    page_id = HiddenField(u'page_id', validators=[DataRequired()])
    submit = SubmitField('Cargar mas', validators=[DataRequired()])


class ShippingForm(Form):
    userrequest_id = HiddenField(u'userrequest_id')
    paidrequest_id = HiddenField(u'paidrequest_id')

    first_name = TextField(
        u'Nombre del destinatario',
        validators=[DataRequired()]
    )

    last_name = TextField(
        u'Apellido del destinatario',
        validators=[DataRequired()]
    )

    id_number = IntegerField(
        u'Número de DNI (Solo números, sin puntos)',
        validators=[DataRequired()]
    )

    province = SelectField(
        u'Provincia',
        choices=PROVINCE_CHOICES,
        validators=[DataRequired()]
    )

    city = SelectField(
        u'Ciudad',
        default=None,
        choices=[],
        validators=[DataRequired()]
    )

    address_one = TextField(
        u'Dirección',
        validators=[DataRequired()]
    )

    address_two = TextField(
        u'Dirección Secundaria (Opcional)',
        validators=[Optional()]
    )

    zipcode = TextField(
        u'Código Postal Argentino',
        validators=[DataRequired()]
    )

    submit = SubmitField(
        u'Finalizar compra',
        validators=[DataRequired()]
    )
