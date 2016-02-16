#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask_inputs import Inputs
from wtforms.validators import DataRequired
from inputs import validators


class AddCartInput(Inputs):
    form = {
        'product_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }


class RemoveCartInput(Inputs):
    form = {
        'relation_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }


class UserRequestInput(Inputs):
    form = {
        'product_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }


class PaidRequestInput(Inputs):
    form = {
        'product_id': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }


class CreditRequestInput(Inputs):
    form = {
        'amount': [
            DataRequired(),
            validators.is_int,
            validators.is_unsigned
        ]
    }


class SearchInput(Inputs):
    form = {
        'title': [
            DataRequired(),
            validators.length_is_ok
        ]
    }
