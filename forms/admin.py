#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import wtforms

from flask_wtf import Form
from wtforms.validators import DataRequired


class ProductCodeForm(Form):
    product_id = wtforms.HiddenField(validators=[DataRequired()])
    code = wtforms.TextAreaField(validators=[DataRequired()])
    submit = wtforms.SubmitField(validators=[DataRequired()])
