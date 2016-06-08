#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import wtforms

from flask_wtf import Form

from wtforms.widgets import TextArea
from wtforms.validators import Optional
from wtforms.validators import DataRequired

import constants


class MessageForm(Form):
    request_id = wtforms.HiddenField(
        'request_id',
        validators=[DataRequired()]
    )
    request_type = wtforms.HiddenField(
        'request_type',
        validators=[DataRequired()]
    )
    to_user = wtforms.HiddenField(
        'to_user',
        validators=[DataRequired()]
    )
    content = wtforms.StringField(
        'Mensaje',
        validators=[DataRequired()],
        widget=TextArea(),
        default=constants.DEFAULT_REQUEST_MESSAGE
    )

    visible = wtforms.BooleanField(
        'Visible (Falso = Solo para administradores)',
        validators=[Optional()],
        default=True
    )

    has_code = wtforms.BooleanField(
        u'Contiene código/link activación',
        validators=[Optional()],
        default=True
    )

    submit = wtforms.SubmitField(
        'Enviar', validators=[DataRequired()]
    )
