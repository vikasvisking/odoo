odoo.define('website_sale_quickorder.quickorder', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var core = require('web.core');
var concurrency = require('web.concurrency');
var qweb = core.qweb;


publicWidget.registry.AddInCart = publicWidget.Widget.extend({
  selector: '.all-btns',
  events: {
    'click .add-to-cart': '_OnAddClick'
  },

  _OnAddClick: async function (event) {
    var body = $('#quick-order-table').find('tbody');
    var tr = $(body).find('tr');
    var list = [];
    tr.map((index, item) => {
      var id = $(item).data('id');
      var quantity = parseInt($(item).find('input[name="add_qty"]').val());
      list.push({
        product_id: id,
        add_qty: quantity,
      })
    });

    const response = await fetch('/my/quick-order/cart', {
      method: 'POST',
      headers: {
      'Content-Type': 'application/json'
      },
      body: JSON.stringify({data: list})
    })

    var status = await response.json()
    if (status.result.status) {
      window.location.href = '/shop/cart'
    }
  }
});


publicWidget.registry.AddInQuickOrderList = publicWidget.Widget.extend({
  selector: '.o_wsale_products_searchbar_form',
  events: {
    'click .pro-item': '_OnClick'
  },
  _OnClick: function (event) {
    var div =  event.target;
    console.log(div)
    div = $(div).closest('.pro-item')
    this.id = $(div).data('id')
    this.src = $(div).data('src')
    this.price = $(div).data('price')
    this.name = $(div).data('name')
    var html = '<tr data-id="' + this.id + '">\
                    <td class="d-flex">\
                      <img src="' + this.src + '" class="flex-shrink-0 o_image_64_contain" />\
                      <span class="ml-2">'+ this.name +'</span>\
                    </td>\
                    <td>\
                    <div class="css_quantity input-group" contenteditable="false">\
                        <div class="input-group-prepend">\
                            <a t-attf-href="#" class="btn btn-secondary js_add_cart_json decrement" aria-label="Remove one" title="Remove one">\
                                <i class="fa fa-minus text-light"></i>\
                            </a>\
                        </div>\
                        <input type="number" class="form-control quantity" data-min="1" name="add_qty" value="1" t-att-value="add_qty or 1"/>\
                        <div class="input-group-append">\
                            <a t-attf-href="#" class="btn btn-secondary float_left js_add_cart_json increment" aria-label="Add one" title="Add one">\
                                <i class="fa fa-plus text-light"></i>\
                            </a>\
                        </div>\
                    </div>\
                    </td>\
                    <td>\
                      100\
                    </td>\
                    <td>' + this.price + '\
                    </td>\
                    <td>\
                      <button type="button" class="btn btn-danger btn-circle remove"> <i class="fa fa-times" ></i> </button>\
                    </td>\
                </tr>'
    $('.first-tr').remove()
    $('#quick-order-table > tbody').append(html)
  }
})

publicWidget.registry.RemoveQuickOrderItem = publicWidget.Widget.extend({
  selector: '#quick-order-table',
  events: {
    'click .remove': '_OnBtnClick',
    'click .increment': '_onIncrement',
    'click .decrement': '_onDecrement'
  },

  _OnBtnClick: function (event) {
    var btn = event.target;
    $(btn).closest('tr').remove();
    const trlen = $('#quick-order-table > tbody tr').length;
    if (trlen === 0) {
      var html = `<tr class="first-tr">
                    <td colspan="5">
                      <h3 class="my-3 text-center">No products available</h3>
                    </td>
                  </tr>`
      $('#quick-order-table > tbody').append(html);
    };
  },

  _onIncrement: function (event) {
    var inc = event.target;
    var input = $(inc).closest('td').find('input');
    $(input).val(parseInt($(input).val()) + 1);
  },

  _onDecrement: function (event) {
    var inc = event.target;
    var input = $(inc).closest('td').find('input');
    var value = parseInt($(input).val());
    if (value > 1) {
      $(input).val( value - 1);
    }
  }
})

publicWidget.registry.quickOrderSearch = publicWidget.Widget.extend({
    selector: '.o_wsale_products_searchbar_form',
    xmlDependencies: ['/website_sale_quickorder/static/src/xml/productDropdown.xml'],
    events: {
      'input .quick-search': '_onInput',
      'focusout': '_onFocusOut',
      'keydown .quick-search': '_onKeydown'
    },
    autocompleteMinWidth: 300,
    /**
    * @constructor
    */
    init: function () {
      this._super.apply(this, arguments);
      this._dp = new concurrency.DropPrevious();
      this._onInput = _.debounce(this._onInput, 400)
      this._onFocusOut = _.debounce(this._onFocusOut, 100)
    },
    /**
    * @override
    **/
    start: function () {
      this.$input = this.$('.quick-search')
      this.order = this.$('.o_wsale_search_order_by').val();
      this.limit = parseInt(this.$input.data('limit'));
      this.displayDescription = !!this.$input.data('displayDescription');
      this.displayPrice = !!this.$input.data('displayPrice')
      this.displayImage = !!this.$input.data('displayImage')

      if (this.limit) {
          this.$input.attr('autocomplete', 'off');
      }

      return this._super.apply(this, arguments)
    },

    _fetch: function () {
      return this._rpc({
        route:  '/my/products/search',
        params: {
            'term': this.$input.val(),
            'options': {
                'order': this.order,
                'limit': this.limit,
                'display_description': this.displayDescription,
                'display_price': this.displayPrice,
                'max_nb_chars': Math.round(Math.max(this.autocompleteMinWidth, parseInt(this.$el.width())) * 0.22),
            },
        },
      })
    },

    _render: function (res) {
      var $prevMenu = this.$menu
      this.$el.toggleClass('dropdown show', !!res);
      if (res) {
        console.log(res)
        var products = res['products'];
        this.$menu = $(qweb.render('website_sale_quickorder.productsSearchBar.autocomplete', {
          products: products,
          hasMoreProducts: products.length < res['products_count'],
          currency: res['currency'],
          widget: this,
        }));
        this.$menu.css('min-width', this.autocompleteMinWidth)
        this.$el.append(this.$menu)
      }
      if ($prevMenu) {
        $prevMenu.remove();
      }
    },

    _onInput: function () {
      if (!this.limit) {
        return;
      }
      this._dp.add(this._fetch()).then(this._render.bind(this));
    },

    _onFocusOut: function () {
      if (!this.$el.has(document.activeElement).length) {
        this._render();
      }
    },

    _onKeydown: function (ev) {
        switch (ev.which) {
            case $.ui.keyCode.ESCAPE:
                this._render();
                break;
            case $.ui.keyCode.UP:
            case $.ui.keyCode.DOWN:
                ev.preventDefault();
              if (this.$menu) {
                  let $element = ev.which === $.ui.keyCode.UP ? this.$menu.children().last() : this.$menu.children().first();
                  $element.focus();
              }
              break;
        }
    },
  })
});
