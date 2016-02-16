#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import config

from flask import Flask

app = Flask(__name__)

with app.app_context():
    app.config.from_object(config)

    @app.template_filter()
    def price_format(price):
        return '%.2f' % price
