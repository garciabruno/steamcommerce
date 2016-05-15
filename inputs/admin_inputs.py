#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask_inputs import Inputs
from wtforms.validators import DataRequired
from inputs import validators


class RequestIDInput(Inputs):
    form = {
        'request_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }


class RequestAssignInput(Inputs):
    form = {
        'request_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ],
        'user_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }
