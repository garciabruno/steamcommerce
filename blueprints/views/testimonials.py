#!/usr/bin/env python
# -*- coding:Utf-8 -*-

'''
External imports
'''

from flask import request
from flask import url_for
from flask import redirect
from flask import Blueprint
from flask import render_template

'''
Internal imports
'''

from steamcommerce_api.api import testimonial
from forms import user as user_form

testimonials = Blueprint('views.testimonials', __name__)


@testimonials.route('/', methods=['GET', 'POST'])
def testimonials_root():
    if request.method == 'GET':
        testimonials_data = testimonial.Testimonial().get_active(1)
        testimonials_count = testimonial.Testimonial().get_count()

        form = user_form.TestimonialsForm()
        form.page_id.data = 2

        template_params = {
            'testimonials': testimonials_data,
            'active_section': 'testimonials',
            'count': testimonials_count,
            'form': form
        }

        return render_template(
            'views/testimonials/view.html',
            **template_params
        )
    elif request.method == 'POST':
        form = user_form.TestimonialsForm(request.form)

        if not form.validate():
            return redirect(url_for('views.testimonials.testimonials_root'))

        try:
            int(form.page_id.data)
        except ValueError:
            return redirect(url_for('views.testimonials.testimonials_root'))

        testimonials_count = testimonial.Testimonial().get_count()
        testimonials_data = testimonial.Testimonial().get_active(
            int(form.page_id.data)
        )

        form.page_id.data = int(form.page_id.data)
        form.page_id.data += 1

        template_params = {
            'testimonials': testimonials_data,
            'active_section': 'testimonials',
            'count': testimonials_count,
            'form': form
        }

        return render_template(
            'views/testimonials/view.html',
            **template_params
        )
