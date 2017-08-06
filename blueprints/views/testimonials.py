#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import redirect
from flask import Blueprint

'''
Internal imports
'''


testimonials = Blueprint('views.testimonials', __name__)


@testimonials.route('/', methods=['GET', 'POST'])
def testimonials_root():
    return redirect('/')
