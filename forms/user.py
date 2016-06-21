#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask_wtf import Form

import constants

from wtforms.validators import Email
from wtforms.validators import Length
from wtforms.validators import DataRequired
# from wtforms.validators import Optional

from wtforms import TextField
from wtforms import HiddenField
from wtforms import SubmitField
from wtforms import BooleanField


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
    # subscribe = BooleanField(
    #     u'Suscribirse a la lista de emails',
    #     default=True,
    #     validators=[Optional()]
    # )
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
    subscribe = BooleanField(
        u'Suscribirse a la lista de emails',
        default=True,
        validators=[DataRequired()]
    )
    submit = SubmitField('Enviar', validators=[DataRequired()])


class ReservationForm(Form):
    request_id = HiddenField(u'request_id', validators=[DataRequired()])
