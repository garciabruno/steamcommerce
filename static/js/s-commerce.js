$('.v5-purchase-button').on('click', function(){
    $('.v5-payment-container').slideDown();
});

$('.v5-invoice-confirm').on('click', function(){
    //
});

$('.v5-remove-from-cart').on('click', function(){
    var $this = $(this);
    var is_loading = $this.data('loading');

    if (is_loading == null){
        $this.data('loading', 1);
    } else if (is_loading){
        return;
    }

    Materialize.toast('Eliminando del carrito ...', 1000);

    $.ajax({
        url: '/ajax/store/cart/remove/',
        type: 'POST',
        data:{
            relation_id: $this.data('relationid')
        },
        success: function(data){
            $this.data('loading', 0);

            $('.v5-cart-item[data-relationid="' + $this.data('relationid') + '"]').fadeOut();

            Materialize.toast('Producto removido del carrito', 1500);
        },
        error: function(data){
            var json_data = JSON.parse(data.responseText);
            $this.data('loading', 0);
        }
    });
});


$('.v5-add-to-cart').on('click', function(){
    var $this = $(this);
    var is_loading = $this.data('loading');

    if (is_loading == null){
        $this.data('loading', 1);
    } else if (is_loading){
        return;
    }

    Materialize.toast('Añadiendo al carrito ...', 2000);

    $.ajax({
        url: '/ajax/store/cart/add/',
        type: 'POST',
        data:{
            product_id: $this.data('productid')
        },
        success: function(data){
            $this.data('loading', 0);
            Materialize.toast('Producto añadido a tu carrito', 1500);
        },
        error: function(data){
            $this.data('loading', 0);

            var json_data = JSON.parse(data.responseText);

            if (json_data['errors'] == 'cart_full') {
                Materialize.toast('Tu carrito se encuentra lleno', 1000);
            } else if (json_data['errors'] == 'product_not_available', 1000) {
                Materialize.toast('El producto no se encuentra disponible', 1000);
            } else {
                Materialize.toast('No se pudo añadir al carrito, intentelo nuevamente', 1000);
            }
        }
    });
});

$('#search').on('focusin', function(){
    $('#catalog').fadeOut();
    $('#offers').fadeOut();

    $('#results').fadeIn();
});

$('#show_catalog').on('click', function(){
    $('#results').fadeOut();

    $('#catalog').fadeIn();
});

last_search = +new Date();
is_searching = false;
last_searched = '';

function check_last_searched(){
    var current_value = $('#search').val();

    if (current_value != last_searched){
        search_product(current_value);
        last_searched = current_value;
    }

    setTimeout(function(){
        check_last_searched()
    }, 550);
}

check_last_searched();

function search_product(title){
    $.ajax({
        url: '/ajax/store/search/products/',
        type: 'POST',
        data:{
            title: title
        },
        success: function(data){
            is_searching = false;
            $('.search-text-title').text(title);
            $('.search-loader').hide();

            $('#products-results').html('');
            $('#products-results').append(data);
        },
        error: function(data){
            is_searching = false;
            $('.search-loader').hide();
        }
    });
}


$('#search').on('input', function(){
    console.log(last_search);
    console.log(+new Date() - last_search)

    if (+new Date() - last_search <= 300) {
        return;
    }

    var $this = $(this);
    var title = $this.val();

    if (title.length < 3) {
        return;
    }

    if (is_searching) {
        return;
    }

    $('.search-text').show();
    $('.search-loader').show();

    last_search = +new Date();
    is_searching = true;

    search_product(title);
});

$('#search_form').on('submit', function(e){
    e.preventDefault();
});