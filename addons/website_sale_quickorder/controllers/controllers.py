# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from odoo.osv import expression


class WebsiteSaleQuickorder(http.Controller):

    @http.route('/my/quick-order', type='http', auth="public", website=True)
    def index(self, **kw):
        dictV = {}
        dictV['page'] = 'quickorder'
        shopping_lists = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'shopping_list')])
        dictV['shopping_lists'] = shopping_lists
        quickorder = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'draft')], limit=1)
        dictV['quickorder'] = quickorder
        return request.render("website_sale_quickorder.index", dictV)

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        order = post.get('order') or 'website_sequence ASC'
        return 'is_published desc, %s, id desc' % order

    def _get_search_domain(self, search, search_in_description=True):
        domains = []
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('default_code', 'ilike', srch)]
                ]
                if search_in_description:
                    subdomains.append([('description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))
        return expression.AND(domains)

    @http.route('/my/products/search', type='json', auth='public', website=True)
    def products_search(self, term, options={}, **kwargs):
        """
        Returns list of products according to the term and product options

        Params:
            term (str): search term written by the user
            options (dict)
                - 'limit' (int), default to 5: number of products to consider
                - 'display_description' (bool), default to True
                - 'display_price' (bool), default to True
                - 'order' (str)
                - 'max_nb_chars' (int): max number of characters for the
                                        description if returned

        Returns:
            dict (or False if no result)
                - 'products' (list): products (only their needed field values)
                        note: the prices will be strings properly formatted and
                        already containing the currency
                - 'products_count' (int): the number of products in the database
                        that matched the search query
        """
        Product = request.env['product.product']
        display_description = options.get('display_description', True)
        display_price = options.get('display_price', True)
        order = self._get_search_order(options)
        max_nb_chars = options.get('max_nb_chars', 999)
        category = options.get('category')
        domain = self._get_search_domain(term, display_description)
        products = Product.search(
            domain,
            limit=min(20, options.get('limit', 5)),
            order=order
        )

        fields = ['id', 'name', 'lst_price', 'website_url']
        if display_description:
            fields.append('description_sale')

        res = {
            'products': products.read(fields),
            'products_count': Product.search_count(domain),
        }

        if display_description:
            for res_product in res['products']:
                desc = res_product['description_sale']
                if desc and len(desc) > max_nb_chars:
                    res_product['description_sale'] = "%s..." % desc[:(max_nb_chars - 3)]

        if display_price:
            FieldMonetary = request.env['ir.qweb.field.monetary']
            monetary_options = {
                'display_currency': request.website.get_current_pricelist().currency_id,
            }
            for res_product, product in zip(res['products'], products):
                res_product['list_price'] = FieldMonetary.value_to_html(res_product['lst_price'], monetary_options)
                res_product['price'] = FieldMonetary.value_to_html(res_product['lst_price'], monetary_options)
        return res

    @http.route(['/my/quick-order/cart'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, **kw):
        """This route is called when adding a product to cart (no options)."""

        dataset = json.loads(request.httprequest.data)
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        product_custom_attribute_values = None
        no_variant_attribute_values = None
        set_qty = 0
        for data in dataset.get('data'):
            sale_order._cart_update(
                product_id=int(data.get('product_id')),
                add_qty=data.get('add_qty'),
                set_qty=set_qty,
                product_custom_attribute_values=product_custom_attribute_values,
                no_variant_attribute_values=no_variant_attribute_values
            )
        value = {
          'status': True
        }
        return value

    @http.route(['/my/quick-order/update-qty'], type = "json", auth = "user", website = True)
    def update_quickorder_item(self):
        data = json.loads(request.httprequest.data)
        id = data.get('params').get('id')
        qty = data.get('params').get('data')
        if id:
            quick_order = request.env['quick.order.line'].browse(int(id))
            if quick_order:
                quick_order.write({"quantity" : int(qty)})
        return {'status': True}

    @http.route(['/quickorder/shoplist-item'], auth = "user", website = True)
    def getShopListItems(self, id=''):
        if id:
            shoplist = request.env['quick.order'].browse(int(id))
            quickorder = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'draft')], limit=1)
            for line in shoplist.quick_order_line:
                products_exists = self.variants_availability()
                if line.product_id.id not in products_exists:
                    quickorder.quick_order_line= [(0,0,{"product_id" : int(line.product_id.id)})]
        return request.redirect('/my/quick-order')

    @http.route(['/quickorder/addToList'], type = "json", auth = "user", website = True)
    def addShoplistItems(self, id=None, product_ids=[]):
        shoplist = request.env['quick.order'].browse(int(id))
        product_list = [id.product_id.id for id in shoplist.quick_order_line]
        quickorder = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'draft')], limit=1)
        status = False
        for line in quickorder.quick_order_line:
            if line.product_id.id not in product_list:
                shoplist.quick_order_line= [(0,0,{"product_id" : int(line.product_id.id)})]
            quickorder.write({"quick_order_line":[(2, int(line.id))]})
            status = True
        return {'status': status}

        #  By Jignresh =====================================

    @http.route(['/quickorder/deleteproduct'], type = "json", auth = "user", website = True)
    def delete_product(self, item_id='', **kw):
        data = json.loads(request.httprequest.data)
        success = ''
        delete = False
        item_id = data.get('params').get('data')
        if item_id:
            user_exists = request.env['quick.order'].search([('user_id', '=', request._uid),('state','=', 'draft')])
            if user_exists:
                user_exists.write({"quick_order_line":[(2, int(item_id))]})
                if not len(user_exists.quick_order_line):
                    success  = request.env['quick.order.message'].search([], limit = 1)
                    success = success.message_on_delete_all_products
                    delete = True
        return {"success" : success, "delete" : delete}

    def compute_currency(self, price):
        order = request.website.sale_get_order(force_create=1)
        from_currency = order.company_id.currency_id
        to_currency = order.pricelist_id.currency_id
        return round(from_currency.compute(price, to_currency), 2)

    def variants_availability(self):
        quick_order = request.env['quick.order'].search([('state','=','draft'), ('user_id', '=', request._uid)])
        return [id.product_id.id for id in quick_order.quick_order_line]

    def shopping_list_availability(self, shopping_list):
        if len(shopping_list)==1:
            return [id.product_id.id for id in shopping_list.quick_order_line]
        return []

    @http.route(['/quickorder/addproducts'], methods=['POST'], type = "json", auth = "user", website = True)
    def add_products(self, **kw):
        # product_ids = kw.get('product_ids')
        data = json.loads(request.httprequest.data)
        product_ids = data.get('product_ids')
        products = None
        total_valid = []
        delete_template_row = False
        template = ''
        product_r = []
        try :
            if len(product_ids):
                user_exists = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'draft')])
                if user_exists:
                    products_exists = self.variants_availability()
                    for product_id in product_ids:
                        if int(product_id) not in products_exists:
                            user_exists.quick_order_line= [(0,0,{"product_id" : int(product_id)})]
                            total_valid.append(int(product_id))
                    product_r = total_valid
                elif not user_exists:
                    ids = [(0,0, {"product_id" : int(id)}) for id in product_ids]
                    product_r = [int(id) for id in product_ids]
                    user_exists = request.env['quick.order'].create({
                        'quick_order_line': ids
                    })
                    products = user_exists.quick_order_line
                user_exists = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'draft')])
                print(user_exists)
                return {
                  'status': True,
                  'quickorder': user_exists.id
                }
                # if total_valid:
                #     products = user_exists.quick_order_line
                # if products:
                #     template = request.env['ir.ui.view'].sudo().render_template('quick_order.add_to_cart_mutliple_body',{'order_quicks' : products,'id' :user_exists.id, 'compute_currency' : self.compute_currency, 'product_r':  product_r})
                # product_template = request.env['product.template'].search([('product_variant_ids.id', '=', int(product_ids[0]))])
                # if product_template:
                #     combination = set(product_template.product_variant_ids.filtered(lambda x: x.product_tmpl_id._is_combination_possible(x.product_template_attribute_value_ids)).ids)
                #     delete_template_row = (set(self.variants_availability()) > combination) or (set(self.variants_availability()) == combination)
                # return {
                #     "template" : template,
                #     "delete_template_row" : delete_template_row
                #     }
        except Exception as e:
            raise Warning('Product id is invalid need int found String {}.'.format(e))
        return Response({'error' : "error"}, content_type='application/json',status=500)

    ################################################################################################
    ## Move Quick Order List into Order Cart as a single entity and change state of Quick Order List
    ################################################################################################
    @http.route(['/quickorder/createorder'], auth="user", type="json", website=True)
    def create_order(self,id=0, order_now=[], **kw):
        success  = request.env['quick.order.message'].search([], limit = 1)
        try :
            quick_order = request.env['quick.order'].browse(int(id))
        except Exception as e:
            raise Warning('Product id is invalid need int found String {}.'.format(e))
        if order_now and quick_order.state != 'done':
            total_lines = []
            sale_order = request.website.sale_get_order(force_create=1)
            if sale_order.order_line:
                total_lines = [order.product_id.id for order in sale_order.order_line]
            for order in order_now:
                if order.get('id') not in total_lines:
                        sale_order._cart_update(product_id = order['id'],line_id = None, set_qty = order.get('quantity'), add_qty = None)
                else:
                    order_line = request.env['sale.order.line'].sudo().search([('product_id', '=', order['id'])])
                    if len(order_line) > 0:
                        sale_order._cart_update(product_id = order.get('id'), line_id = order_line[0].id, add_qty = order.get('quantity'), set_qty = None )
            if not id:
                user_exists = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'draft')])
            if id:
                user_exists = request.env['quick.order'].browse(id)
            user_exists.write({'state' : 'done'})
            return success.message_on_empty_order_list
        return {"error": success.empty_shopping_list_submit}

    ######################################################################################
    ## Move Quick Order List into Shopping List by changing the state of Quick Order List
    ######################################################################################
    @http.route(['/quickorder/addshoppinglist'], auth='user', type='json', website=True)
    def add_shopping_list(self, name='', id=None, create=False, list_id= 0, **kw):
        param = json.loads(request.httprequest.data)
        data = param.get('params')
        id = data.get('id')
        create = data.get('create')
        quick_order = request.env['quick.order'].browse(int(id))
        quick_order.write({"state": "done"})
        product_ids = []
        template = ''
        data = {}
        if id and create:
            if quick_order:
                quick_order.write({"name": name, "state": "shopping_list"})
                return {
                        "url" : "/quickorder/shoppinglist/"+str(quick_order.id),
                        "route" : True
                    }
        elif id and list_id:

            quick_order_1 = request.env['quick.order'].browse(int(list_id))
            products = self.shopping_list_availability(quick_order_1)
            for id in quick_order.quick_order_line:
                if id.product_id.id not in products:
                    product_ids.append((4,id.id))
                else:
                    q_products = quick_order_1.quick_order_line.filtered(lambda x: x.product_id.id == id.product_id.id)
                    if q_products.exists():
                        q_products.quantity = id.quantity + q_products.quantity
            if product_ids:
                quick_order_1.write({"quick_order_line": product_ids})
                quick_order.unlink()
            return {
                    "url" : "/quickorder/shoppinglist/"+str(quick_order_1.id),
                    "route" : True
                }
        return json.dumps({"route" : False})

    ##################################################################
    ## Get All Shopping List and also based on id
    ##################################################################

    @http.route(['/quickorder/shoppinglist', '/quickorder/shoppinglist/<int:shopping_id>'], auth='user', type='http', website=True)
    def shopping_list(self,shopping_id=0, id=0, **kw):
        shopping_lists = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'shopping_list')])
        if id:
            shopping_list = request.env['quick.order'].search([('id', '=', int(id)),('state', '=', 'shopping_list'),('user_id', '=', request._uid)])
            return request.env['ir.ui.view'].render_template('quick_order.add_to_cart_mutliple',{
                                                                    'shopping_lists' : shopping_list,
                                                                    'shopping_list' : shopping_lists,
                                                                    'compute_currency' : self.compute_currency,
                                                                    'product_r': self.shopping_list_availability(shopping_list)
                                                                    })
        if shopping_id:
            shopping_list = request.env['quick.order'].search([('id', '=', shopping_id), ('state', '=', 'shopping_list'),('user_id', '=', request._uid)])
            try:
                len(shopping_list.quick_order_line)
            except Exception:
                shopping_list=None
        else:
            shopping_list = request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'shopping_list')])
        s_error = request.env['quick.order.message'].search([], limit = 1)
        return request.render('website_sale_quickorder.shopping_list', {
                        'shopping_lists' : shopping_list,
                        'shopping_list' : shopping_lists,
                        'error' :{'s_error': s_error.message_on_empty_shopping_list},
                        'product_r': self.shopping_list_availability(shopping_list)
                    })

    ############################################################################
    ## Delete all Shopping Lists and also baesd on unique id of product_id line .
    ############################################################################
    @http.route(['/quickorder/shoppinglist/delete'], auth='user', type='http', website=True)
    def shopping_list_delete(self, shopping_id=0, product_id=0, **kw):
        if shopping_id:
            shopping_list = request.env['quick.order'].search([('id', '=', int(shopping_id)),('state', '=', 'shopping_list'), ('user_id', '=', request._uid)])
            if shopping_list:
                if int(product_id) in shopping_list.quick_order_line.ids:
                    shopping_list.write({"quick_order_line": [(2, int(product_id))]})
                elif not product_id:
                    shopping_list.unlink()
                    if len(request.env['quick.order'].search([('user_id', '=', request._uid),('state', '=', 'shopping_list')])) <= 0:
                        s_error = request.env['quick.order.message'].search([], limit = 1)
                        return request.env['ir.ui.view'].render_template('website_sale_quickorder.404',{'error' :{'s_error': s_error.message_on_empty_shopping_list}})
                return json.dumps({'success' : "success"})
        return json.dumps({'error' : "error"})
