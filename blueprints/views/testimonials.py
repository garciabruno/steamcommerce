#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import Blueprint
from flask import render_template

'''
Internal imports
'''

from steamcommerce_api.api import testimonial

testimonials = Blueprint('views.testimonials', __name__)


@testimonials.route('/')
def testimonials_root():
    testimonials_data = testimonial.Testimonial().get_testimonials(1)
    template_params = {
        'testimonials': testimonials_data,
        'active_section': 'testimonials'
    }

    return render_template('views/testimonials/view.html', **template_params)
