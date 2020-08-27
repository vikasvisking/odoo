import logging
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)

class QuickOrderLine(models.Model):
    _name = 'quick.order.line'

    name = fields.Char(string="Name", compute='get_name')
    product_id = fields.Many2one(comodel_name = "product.product", string = "Products", required = True)
    quantity = fields.Integer(string="Quantity", default=1)
    quick_order_id = fields.Many2one(comodel_name = "quick.order", string = "Quick Order", ondelete="cascade")

    def unlink(self):
        return super(QuickOrderLine, self).unlink()

    def get_name(self):
        for line in self:
            line.name = line.product_id.name

    @api.onchange('product_id')
    def change_product_id(self):
        return {
                'domain':{'product_id':[('website_published','=', True)]},
                }

    # @api.model
    def _get_product_price(self):
        product_id = self.product_id
        if product_id:
            prodtuct_value = product_id.product_tmpl_id._get_combination_info(product_id.product_template_attribute_value_ids, product_id.id)
            return prodtuct_value.get("price")*self.quantity
        return 0

class QuickOrder(models.Model):
    _name = "quick.order"

    name = fields.Char(string = "Name", readonly=True)
    quick_order_line = fields.One2many(string="Quick Order Line",comodel_name="quick.order.line", inverse_name="quick_order_id")
    user_id=fields.Many2one(comodel_name="res.users", string="User", default=lambda self: self._uid, readonly=True )
    state = fields.Selection([('draft', 'Draft'),('shopping_list', 'Shopping List'),('done', 'Done')], string = "Order State", default = 'draft')
    create_date = fields.Date(string="Created Date")
    write_date = fields.Date(string="Updated Date")


    @api.model
    def create(self, vals):
        values = vals.get("quick_order_line")
        if values:
            invalid = list(map(lambda x: self.get_product_id(x), values))
            if invalid and (sorted(invalid) != sorted(list(set(invalid)))):
                raise ValidationError(_('There is a product have already exits in your Quick Order. Please update the existing one or delete'))
        result = super(QuickOrder, self).create(vals)
        postfix = str(result.id)
        exists = False
        if vals.get("state") == "draft":
            exists = self.search([('user_id', '=', vals.get('user_id')), ('state', '=', 'draft'), ('id', '!=', result.id)], limit=1)
        if exists and exists.exists():
            raise ValidationError(_('There is already Quotation order %s in draft state for this customer. You can not create another draft qucik order for this customer. Please update the exixting one' % exists.name))
        if not vals.get('name'):
            name = False
            if len(postfix) == 1:
                name = 'QO00'+postfix
            elif len(postfix) == 2:
                name = 'QO0'+postfix
            else:
                name = 'QO'+postfix
            result.name = name
        quick_order = self.search([('state', '=', 'draft'),('user_id', '=', self._uid)])
        if len(quick_order) > 1:
            result.state = 'shopping_list'

        return result

    def write(self, vals):
        values = vals.get("quick_order_line")
        if values:
            invalid = list(filter(lambda a: a not in [False, None], list(map(lambda x: self.get_product_id(x), values))))
            check = any(x in invalid for x in self.quick_order_line.mapped("product_id.id"))
            if check or (invalid and (sorted(invalid) != sorted(list(set(invalid))))):
                raise ValidationError(_('There is a product have already exits in your Quick Order. Please update the existing one or delete'))
        result = super(QuickOrder, self).write(vals)
        return result


    def get_product_id(self, x):
        for i in x:
            if type(i).__name__ == "dict":
                return i.get("product_id")

class ResConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    def get_quick_form(self):
        template = self.env.ref("quick_order.quick_order_message_from_view").id
        res_id = self.env['quick.order.message'].search([], limit = 1)
        return {
            "name" : "Quick Order Message",
            "type" : "ir.actions.act_window",
            "res_model" : "quick.order.message",
            "view_mode" : "form",
            "view_type": "form",
            "res_id" : res_id.id,
            "view_id" : template
        }

class QuickOrderMessage(models.Model):
    _name = 'quick.order.message'

    name = fields.Char(string = "Quick Order Message", default = 'Quick Order Message')
    message_on_empty_order_list = fields.Char(string = "Message on empty Order list", default = lambda self : self.get_message_1(), required = True, translate = True)
    message_on_product_search = fields.Char(string = "Message on no Product found in search", default = lambda self: self.get_message_3(), required = True, translate = True)
    message_on_empty_shopping_list = fields.Char(string = "Message on empty Shopping list", default = lambda self: self.get_message_4(), required = True, translate = True)
    message_on_delete_all_products = fields.Char(string = "Message on delete all products from Quick Order list", default = lambda self: self.get_message_5(), required = True, translate = True)
    empty_shopping_list_submit = fields.Char(string = "Message on submit empty Shopping list into Cart", default = lambda self: self.get_message_6(), required = True, translate = True)

    def get_message_1(self):
        return "No Products found in your Order list"

    def get_message_3(self):
        return "No Products found for the related keyword"

    def get_message_4(self):
        return "No Shopping List available. Please create a new one"

    def get_message_5(self):
        return "All Products are successfully deleted from your Quick Order list"

    def get_message_6(self):
        return "No Products in your Shopping list for added into the Order Cart"
