from odoo import http
from odoo.http import request
from odoo.addons.sale.controllers.portal import CustomerPortal


class Reorder(CustomerPortal):

    @http.route(['/my/reorder', '/my/reorder/<int:sale_id>'])
    def portal_reorder(self, sale_id=None, *kw):
        if sale_id:
            sale_order = request.env['sale.order'].browse(sale_id)
            sale_order.copy()
        return str("/my/orders")
