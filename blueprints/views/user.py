#!/usr/bin/env python
# -*- coding:Utf-8 -*-

from flask import Blueprint
from flask import render_template

from steamcommerce_api.api import user
from steamcommerce_api.api import userrequest
from steamcommerce_api.api import paidrequest
from steamcommerce_api.api import notification
from steamcommerce_api.api import creditrequest

user_view = Blueprint('views.user', __name__)


@user_view.route('/perfil')
def user_profile():
    user_id = 1
    user_data = user.User().get_by_id(user_id)
    notifications = notification.Notification().get_for_user(user_id)
    userrequests = userrequest.UserRequest().get_user_userrequests(user_id)
    creditrequests = creditrequest.CreditRequest().get_user_creditrequests(
        user_id
    )
    paidrequests = paidrequest.PaidRequest().get_user_paidrequests(user_id)

    params = {
        'user': user_data,
        'userrequests': userrequests,
        'paidrequests': paidrequests,
        'notifications': notifications,
        'creditrequests': creditrequests
    }

    return render_template('views/user/profile.html', **params)
