# -*- coding:Utf-8 -*-

'''
HistoryItem constants
'''

HISTORY_GENERATED_STATE = 1
HISTORY_PAID_STATE = 2
HISTORY_ACCEPTED_STATE = 3
HISTORY_DENIED_STATE = 4

HISTORY_USERREQUEST_TYPE = 1
HISTORY_CREDITREQUEST_TYPE = 2
HISTORY_PAIDREQUEST_TYPE = 3

'''
AdminLog constants
'''

ADMINLOG_USERREQUEST_ACCEPTED = 1
ADMINLOG_CREDITREQUEST_ACCEPTED = 2
ADMINLOG_PAIDREQUEST_ACCEPTED = 3

ADMINLOG_USERREQUEST_INVALID_PAYMENT = 4
ADMINLOG_CREDITREQUEST_INVALID_PAYMENT = 5

ADMINLOG_USERREQUEST_PAID = 6

ADMINLOG_USERREQUEST_DENIED = 14
ADMINLOG_CREDITREQUEST_DENIED = 15
ADMINLOG_PAIDREQUEST_DENIED = 16

'''
Notification constants
'''

NOTIFICATION_USERREQUEST_ACCEPTED = 1
NOTIFICATION_CREDITREQUEST_ACCEPTED = 2
NOTIFICATION_PAIDREQUEST_DONE = 3
NOTIFICATION_PAIDREQUEST_ACCEPTED = 4
NOTIFICATION_PAIDREQUEST_DENIED = 5

NOTIFICATION_NEW_TICKET_COMMENT = 6
NOTIFICATION_TICKET_STATUS_RESOLVED = 7

NOTIFICATION_USERREQUEST_DENIED = 8
NOTIFICATION_REQUEST_NOTE_ADDED = 9

NOTIFICATION_EMAIL_UPDATED = 10

'''
Request constants
'''

DEFAULT_REQUEST_MESSAGE = u'\
Hola, Hemos procesado su pedido.\nTu código/link de activación es:\n\
'

'''
Field constants
'''

FIELD_REQUIRED = 'Este campo es requerido'
FIELD_LENGTH_INVALID = 'El largo del valor no es suficiente'
FIELD_NOT_EMAIL = u'El valor ingresado no es una dirección de email correcta'
