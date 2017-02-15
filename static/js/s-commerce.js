jQuery(document).ready(function($){
    //if you change this breakpoint in the style.css file (or _layout.scss if you use SASS), don't forget to update this value as well
    var $L = 1200,
        $menu_navigation = $('#main-nav'),
        $cart_trigger = $('#cd-cart-trigger'),
        $hamburger_icon = $('#cd-hamburger-menu'),
        $lateral_cart = $('#cd-cart'),
        $shadow_layer = $('#cd-shadow-layer');

    //open cart

    $cart_trigger.on('click', function(event){
        event.preventDefault();
        //close lateral menu (if it's open)

        $menu_navigation.removeClass('speed-in');
        toggle_panel_visibility($('#cd-cart'), $('#cd-shadow-layer'), $('body'));
    });

    //close lateral cart or lateral menu

    $("body").on('click', '#cd-shadow-layer', function(){
        $shadow_layer = $('#cd-shadow-layer');
        $lateral_cart = $('#cd-cart,#cd-notifications');

        $shadow_layer.removeClass('is-visible');
        // firefox transitions break when parent overflow is changed, so we need to wait for the end of the trasition to give the body an overflow hidden
        if( $lateral_cart.hasClass('speed-in') ) {
            $lateral_cart.removeClass('speed-in').on('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend', function(){
                $('body').removeClass('overflow-hidden');
            });
            $menu_navigation.removeClass('speed-in');
        } else {
            $menu_navigation.removeClass('speed-in').on('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend', function(){
                $('body').removeClass('overflow-hidden');
            });
            $lateral_cart.removeClass('speed-in');
        }
    });

    $('.s-commerce-user-nav-notifications').on('click', function(event){
        event.preventDefault();

        $menu_navigation.removeClass('speed-in');
        toggle_panel_visibility($('#cd-notifications'), $('#cd-shadow-layer'), $('body'));

        var $this = $(this);

        if (!$this.data('loaded')) {
            $.ajax({
                url: '/user/notifications',
                type: 'GET',
                success: function(data){
                    $('.s-commerce-navbar-item-loading').hide();
                    $('.cd-notifications-items').html(data);
                }
            })

            $.ajax({
                'url': '/notifications/seen/'
            });

            $this.data('loaded', 1)
        }
    });
});

function toggle_panel_visibility ($lateral_panel, $background_layer, $body) {
    if($lateral_panel.hasClass('speed-in')) {
        // firefox transitions break when parent overflow is changed, so we need to wait for the end of the trasition to give the body an overflow hidden

        $lateral_panel.removeClass('speed-in').one('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend', function() {
            $body.removeClass('overflow-hidden');
        });

        $background_layer.removeClass('is-visible');
    } else {
        $lateral_panel.addClass('speed-in').one('webkitTransitionEnd otransitionend oTransitionEnd msTransitionEnd transitionend', function(){
            $body.addClass('overflow-hidden');
        });

        $background_layer.addClass('is-visible');
    }
}

function move_navigation( $navigation, $MQ) {
    if ( $(window).width() >= $MQ ) {
        $navigation.detach();
        $navigation.appendTo('header');
    } else {
        $navigation.detach();
        $navigation.insertAfter('header');
    }
}

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

function parseButton(selector) {
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

$('body').on('click', '.s-commerce-remove-cart-button', function(){
    var $this = $(this);
    var button = new Button($this);

    if (button.is_loading()) {
        var notification = new Notification;
        notification.push(MESSAGE_LOADING_GENERIC);

        return Error;
    }

    button.to_loading(true);

    $.ajax({
        url: '/ajax/store/cart/remove/',
        type: 'POST',
        data:{
            relation_id: $this.data('relationid')
        },
        success: function(data) {
            $this.data('loading', 0);

            var count = parseInt($('.s-commerce-cart-counter').text());

            $('.s-commerce-cart-item[data-relationid="' + $this.data('relationid') + '"]').fadeOut();
            $('.s-commerce-cart-item[data-relationid="' + $this.data('relationid') + '"]').remove();

            $('.s-commerce-cart-counter').text(count - 1);

            $('.s-commerce-cart-hud').html(data);
        },
        error: function(data){
            $this.data('loading', 0);
        }
    });
});


$('.s-commerce-cart-button, .s-commerce-offer-cart-button').on('click', function() {
    var $this = $(this);
    var button = new Button($this);
    var notification = new Notification;

    if (button.is_loading()) {
        var notification = new Notification;
        notification.push(MESSAGE_LOADING_GENERIC);

        return Error;
    }

    button.to_loading(true);

    $.ajax({
        url: '/ajax/store/cart/add/',
        type: 'POST',
        data:{
            product_id: $this.data('productid')
        },
        success: function(data){
            $this.data('loading', 0);
            notification.push('Producto añadido a tu carrito');

            $('body').find('#cd-cart').html(data);

            button.restore_loading();
        },
        error: function(data){
            $this.data('loading', 0);

            var json_data = JSON.parse(data.responseText);

            if (json_data['status'] == 1) {
                notification.push('El producto no se encuentra disponible');
            } else if (json_data['status'] == 2) {
                notification.push('El producto no contiene precios activos');
            } else if (json_data['status'] == 3) {
                notification.push('No puedes añadir productos de entrega inmediata a tu carrito');
            } else if (json_data['status'] == 4) {
                notification.push('Tu carrito se encuentra lleno');
            } else {
                notification.push('No se pudo añadir al carrito, intentelo nuevamente');
            }

            button.restore_loading();
        }
    });
});

$('#cd-cart-trigger').on('click', function(){
    $('.s-commerce-navbar-item-loading').show();

    var $this = $(this);

    if (!$this.data('loaded')) {
        $.ajax({
            url: '/user/cart/',
            type: 'GET',
            success: function(data) {
                $('.s-commerce-navbar-item-loading').hide();
                $('#cd-cart').html(data);

                $this.data('loaded', '1');
            }
        });
    }
});
