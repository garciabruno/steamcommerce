#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask_inputs import Inputs
from wtforms.validators import DataRequired
from inputs import validators


class SectionAPIInput(Inputs):
    args = {
        'section': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }
