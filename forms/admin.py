#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import wtforms

from flask_wtf import Form
from wtforms.validators import DataRequired


class ProductCodeForm(Form):
    product_id = wtforms.HiddenField(validators=[DataRequired()])
    code = wtforms.TextAreaField(validators=[DataRequired()])
    submit = wtforms.SubmitField(validators=[DataRequired()])


class ProductPriceForm(Form):
    product_id = wtforms.HiddenField(validators=[DataRequired()])
    price = wtforms.FloatField(validators=[DataRequired()])
    active = wtforms.BooleanField(
        validators=[DataRequired()],
        default=True
    )
    submit = wtforms.SubmitField(validators=[DataRequired()])
