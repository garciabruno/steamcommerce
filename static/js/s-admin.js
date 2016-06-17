var ADMIN_ACCEPT_REQUEST_SELECTOR = '.accept_request';
var ADMIN_DENY_REQUEST_SELECTOR = '.deny_request';
var ADMIN_DENY_REASON_SELECTOR = '#deny_reason';
var ADMIN_ASSIGN_REQUEST_SELECTOR = '.assign_request';
var ADMIN_ASSIGN_REQUEST_OPTION = '.request-assigment select option:selected';
var ADMIN_PAY_REQUEST_SELECTOR = '.pay_request';
var ADMIN_DEASSIGN_REQUEST_SELECTOR = '.deassign_request';

var MESSAGE_REQUEST_ACCEPTED = 'Pedido aceptado exitosamente';
var MESSAGE_REQUEST_DENIED = 'Pedido denegado exitosamente';
var MESSAGE_REQUEST_ASSIGNED = 'Pedido asignado exitosamente';
var MESSAGE_REQUEST_PAID = 'Pedido cobrado exitosamente';
var MESSAGE_REQUEST_DEASSIGNED = 'Pedido desasignado exitosamente';

var MESSAGE_REQUEST_BUTTON_DENIED = 'Pedido denegado';
var MESSAGE_REQUEST_BUTTON_ACCEPTED = 'Pedido aceptado';

var MESSAGE_REQUEST_ALREADY_DENIED = 'Este pedido ya se encuentra denegado';
var MESSAGE_REQUEST_ALREADY_ACCEPTED = 'Este pedido ya se encuentra aceptado';
var MESSAGE_REQUEST_ALREADY_PAID = 'Este pedido ya se encuentra cobrado';

var MESSAGE_ERROR_GENERIC = 'Hubo un error al enviar la solicitud';
var MESSAGE_LOADING_GENERIC = 'Cargando, espere un momento...';

var Button = function(selector) {
    var self = this;
    var selector = selector;

    this.get_state = function() {
        return $(selector).data();
    };

    this.confirm = function() {
        var state = self.get_state();

        if (typeof(state['confirm']) == 'undefined') {
            $(selector).data('confirm', '1');

            $(selector).data('original-html', $(selector).html());
            self.set_text('Confirmar');

            return false;
        } else {
            return true;
        }
    };

    this.to_loading = function(restore) {
        if (restore) {
            $(selector).data('original-html', $(selector).html());
        }

        $(selector).html('<i class="glyphicon glyphicon-cog"></i>');

        $(selector).data('loading', 1);
    };

    this.is_loading = function() {
        var state = self.get_state()['loading'];

        if (typeof(state) == 'undefined') {
            return false;
        } else {
            return parseInt(state);
        }
    };

    this.destroy = function() {
        $(selector).remove();
    };

    this.restore_loading = function(){
        $(selector).html($(selector).data('original-html'));
        $(selector).data('loading', 0);
    };

    this.set_text = function(text) {
        $(selector).text(text);
    };
};

var Notification = function() {
    var self = this;

    this.push = function (message) {
        $.createNotification({
            content: message,
            vertical: 'bottom',
            duration: 3500
        });

        console.info(message);
    };
};

var Request = function(requestButton) {
    var self = this;

    this.accept_request = function(request_type, request_id) {
        if (request_type == 'A') {
            var URL = '/admin/ajax/userrequest/accept/';
        } else if (request_type == 'B') {
            var URL = '/admin/ajax/creditrequest/accept/';
        } else if (request_type == 'C') {
            var URL = '/admin/ajax/paidrequest/accept/';
        }

        $.ajax({
            url: URL,
            type: 'POST',
            data: {
                request_id: request_id
            },
            error: function(err) {
                var errData = $.parseJSON(err.responseText);
                var notification = new Notification;

                if (errData['status'] == 0) {
                    notification.push(MESSAGE_REQUEST_ALREADY_ACCEPTED);
                } else {
                    notification.push(MESSAGE_ERROR_GENERIC);
                }

                requestButton.restore_loading();
            },
            success: function(data) {
                var notification = new Notification;
                notification.push(MESSAGE_REQUEST_ACCEPTED);

                requestButton.restore_loading();
                requestButton.set_text(MESSAGE_REQUEST_BUTTON_ACCEPTED);
            }
        });
    };

    this.deny_request = function(request_type, request_id, reason) {
        if (request_type == 'A') {
            var URL = '/admin/ajax/userrequest/deny/';
        } else if (request_type == 'C') {
            var URL = '/admin/ajax/paidrequest/deny/';
        }

        $.ajax({
            url: URL,
            type: 'POST',
            data: {
                request_id: request_id,
                reason: reason || ''
            },
            error: function(err) {
                var errData = $.parseJSON(err.responseText);
                var notification = new Notification;

                if (errData['status'] == 0) {
                    notification.push(MESSAGE_REQUEST_ALREADY_DENIED);
                } else {
                    notification.push(MESSAGE_ERROR_GENERIC);
                }

                requestButton.restore_loading();
            },
            success: function(data) {
                var notification = new Notification;
                notification.push(MESSAGE_REQUEST_DENIED);

                requestButton.restore_loading();
                requestButton.set_text(MESSAGE_REQUEST_BUTTON_DENIED);
            }
        });
    };

    this.assign_request = function(request_type, request_id, user_id) {
        if (request_type == 'A') {
            var URL = '/admin/ajax/userrequest/assign/to/';
        } else {
            var URL = '/admin/ajax/paidrequest/assign/to/';
        }

        $.ajax({
            url: URL,
            type: 'POST',
            data: {
                request_id: request_id,
                user_id: user_id
            },
            error: function(err) {
                var notification = new Notification;
                notification.push(MESSAGE_ERROR_GENERIC);

                requestButton.restore_loading();
            },
            success: function(data) {
                var notification = new Notification;
                notification.push(MESSAGE_REQUEST_ASSIGNED);

                requestButton.restore_loading();
            }
        });
    };

    this.deassign_request = function(request_type, request_id) {
        if (request_type == 'A') {
            var URL = '/admin/ajax/userrequest/deassign/';
        } else {
            var URL = '/admin/ajax/paidrequest/deassign/';
        }

        $.ajax({
            url: URL,
            type: 'POST',
            data: {
                request_id: request_id
            },
            error: function(err) {
                var notification = new Notification;
                notification.push(MESSAGE_ERROR_GENERIC);

                requestButton.restore_loading();
            },
            success: function(data) {
                var notification = new Notification;
                notification.push(MESSAGE_REQUEST_DEASSIGNED);

                requestButton.restore_loading();
            }
        });
    };

    this.set_paid = function(request_type, request_id) {
        if (request_type == 'A') {
            var URL = '/admin/ajax/userrequest/set/paid/';
        } else if (request_type == 'B') {
            var URL = '/admin/ajax/creditrequest/set/paid/';
        }

        $.ajax({
            url: URL,
            type: 'POST',
            data: {
                request_id: request_id
            },
            error: function(err) {
                var errData = $.parseJSON(err.responseText);
                var notification = new Notification;

                if (errData['status'] == 0) {
                    notification.push(MESSAGE_REQUEST_ALREADY_PAID);
                } else {
                    notification.push(MESSAGE_ERROR_GENERIC);
                }

                requestButton.restore_loading();
            },
            success: function(data) {
                var notification = new Notification;

                notification.push(MESSAGE_REQUEST_PAID);
                requestButton.restore_loading();
            }
        });
    }
};

function parseAdminButton(selector) {
    var button = new Button(selector);

    if (!button.confirm()) {
        return Error;
    }

    if (button.is_loading()) {
        var notification = new Notification;
        notification.push(MESSAGE_LOADING_GENERIC);

        return Error;
    }

    button.to_loading(false);

    return button;
}

$(ADMIN_ACCEPT_REQUEST_SELECTOR).on('click', function() {
    var button = parseAdminButton(ADMIN_ACCEPT_REQUEST_SELECTOR);

    if (button == Error) {
        return;
    }

    var request = new Request(button);
    var state = button.get_state();

    request.accept_request(state['requesttype'], state['requestid']);
});

$(ADMIN_DENY_REQUEST_SELECTOR).on('click', function() {
    var button = parseAdminButton(ADMIN_DENY_REQUEST_SELECTOR);

    if (button == Error) {
        return;
    }

    var request = new Request(button);
    var state = button.get_state();

    var reason = $(ADMIN_DENY_REASON_SELECTOR).val()

    request.deny_request(state['requesttype'], state['requestid'], reason);
});

$(ADMIN_ASSIGN_REQUEST_SELECTOR).on('click', function(){
    var button = parseAdminButton(ADMIN_ASSIGN_REQUEST_SELECTOR);

    if (button == Error) {
        return;
    }

    var request = new Request(button);
    var state = button.get_state();
    var user_id = $(ADMIN_ASSIGN_REQUEST_OPTION).val();

    request.assign_request(state['requesttype'], state['requestid'], user_id);
});

$(ADMIN_PAY_REQUEST_SELECTOR).on('click', function() {
    var button = parseAdminButton(ADMIN_PAY_REQUEST_SELECTOR);

    if (button == Error) {
        return;
    }

    var request = new Request(button);
    var state = button.get_state();

    request.set_paid(state['requesttype'], state['requestid']);
});

$(ADMIN_DEASSIGN_REQUEST_SELECTOR).on('click', function(){
    var button = parseAdminButton(ADMIN_DEASSIGN_REQUEST_SELECTOR);

    if (button == Error) {
        return;
    }

    var request = new Request(button);
    var state = button.get_state();

    request.deassign_request(state['requesttype'], state['requestid']);
});
