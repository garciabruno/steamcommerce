#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from wtforms.validators import ValidationError


def is_int(form, field):
    try:
        int(field.data)
    except ValueError:
        raise ValidationError('Field type is not int')


def is_unsigned(form, field):
    try:
        int(field.data)
    except ValueError:
        return None

    if int(field.data) <= 0:
        raise ValidationError('Field type is not unsigned')


def length_is_ok(form, field):
    if len(field.data) == 0 or len(field.data) > 512:
        raise ValidationError('Field data length is invalid')
