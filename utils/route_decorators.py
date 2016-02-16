#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from functools import wraps


def as_json(f):
    @wraps(f)
    def as_json_inner(*args, **kwargs):
        response = f(*args, **kwargs)

        return response, 200, {'Content-Type': 'application/json'}

    return as_json_inner
