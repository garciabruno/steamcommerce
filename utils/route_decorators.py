#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import session
from flask import url_for
from flask import request
from flask import redirect

from functools import wraps

import json


def as_json(f):
    @wraps(f)
    def as_json_inner(*args, **kwargs):
        response = f(*args, **kwargs)

        if type(response) == tuple and len(response) == 2:
            return (
                json.dumps(response[0]),
                response[1],
                {'Content-Type': 'application/json'}
            )

        return (
            json.dumps(response),
            200,
            {'Content-Type': 'application/json'}
        )

    return as_json_inner


def is_logged_in(f):
    @wraps(f)
    def logged_in_inner(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('views.store.store_catalog'))

        if not session.get('email'):
            if request.url_rule.rule != url_for('views.user.user_register'):
                return redirect(url_for('views.user.user_register'))

        return f(*args, **kwargs)

    return logged_in_inner


def is_admin(f):
    @wraps(f)
    def is_admin_inner(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/')

        return f(*args, **kwargs)

    return is_admin_inner


def ajax_is_admin(f):
    @wraps(f)
    def ajax_is_admin_inner(*args, **kwargs):
        if not session.get('admin'):
            return (
                json.dumps({'success': False, 'message': 'Unauthorized'}),
                403,
                {'Content-Type': 'application/json'}
            )

        return f(*args, **kwargs)

    return ajax_is_admin_inner


def ajax_is_logged_in(f):
    @wraps(f)
    def ajax_is_logged_in_inner(*args, **kwargs):
        if not session.get('user'):
            return (
                json.dumps({'success': False, 'message': 'Not logged in'}),
                403,
                {'Content-Type': 'application/json'}
            )

        return f(*args, **kwargs)

    return ajax_is_logged_in_inner


def not_logged_in(f):
    @wraps(f)
    def not_logged_in_inner(*args, **kwargs):
        if session.get('user'):
            return redirect('/')

        return f(*args, **kwargs)

    return not_logged_in_inner


def has_no_email(f):
    @wraps(f)
    def has_no_email_inner(*args, **kwargs):
        if not session.get('email'):
            return f(*args, **kwargs)

        return redirect(url_for('views.store.store_catalog'))

    return has_no_email_inner
