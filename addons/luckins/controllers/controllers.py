# -*- coding: utf-8 -*-
# from odoo import http


# class Luckins(http.Controller):
#     @http.route('/luckins/luckins/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/luckins/luckins/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('luckins.listing', {
#             'root': '/luckins/luckins',
#             'objects': http.request.env['luckins.luckins'].search([]),
#         })

#     @http.route('/luckins/luckins/objects/<model("luckins.luckins"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('luckins.object', {
#             'object': obj
#         })
