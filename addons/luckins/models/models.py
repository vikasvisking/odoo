# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import requests
import json
from time import sleep

LUCKINS_KEY = 'E969003900AE000BFD3C00005E020107018C000025D3EC5E'
_logger = logging.getLogger(__name__)

# Get Access Token
def get_luckins_access_token():
    """
        This function is used to fetch the access to, So we
        can use that access token to fetch the data from the LuckinsLive.
    """
    url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/GetLogToken/1'
    myobj = {
        "CustomerIdentifier": LUCKINS_KEY,

        "ClientIPAddress": "103.212.235.58"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    token_request = requests.post(url, data = json.dumps(myobj), headers=headers)
    token = token_request.json()
    return token

class MainCategories(models.Model):
    _name = 'luckins.luckins'
    _description = 'luckins.luckins'

    luckins_id = fields.Integer('Luckin Id')
    name = fields.Char('Category Name')
    created_date = fields.Datetime('Created Date', default=lambda self: fields.datetime.now())

    def getLuckinsGeneralCategory(self):
        token = get_luckins_access_token()
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/TaxonomyList/1'
        payload = {
        	"Token":token,
        	"ViewportType":3,
        	"AssetSized2List":[{"Height":300,"Width":300,"MaintainAspectRatio":1,"Tag":"supllier_logo"}],
        	"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":6,"TSIUniqueIdentifier":""}]
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        general_cat_request = requests.post(url, data = json.dumps(payload), headers=headers)
        general_cat_data = general_cat_request.json()

        if general_cat_data.get('TaxonomyList'):
            cat_list = []
            for cat in general_cat_data.get('TaxonomyList'):
                get_obj = self.env['luckins.luckins'].search([('luckins_id','=',cat.get('TaxonomyCode'))])
                if cat.get('TaxonomyLabel') != "Business Services" and not get_obj:
                    cat_list.append({
                      'luckins_id': cat.get('TaxonomyCode'),
                      'name': cat.get('TaxonomyLabel')
                    })
            self.env['luckins.luckins'].create(cat_list)
            self.env.cr.commit()
            _logger.info('General Category Updated')


class MajorCategories(models.Model):

    _name = 'luckins.major_category'
    _description = 'luckins.major_category'

    luckins_id = fields.Integer('Luckin Id')
    name = fields.Char('Category Name')
    created_date = fields.Datetime('Created Date', default=lambda self: fields.datetime.now())
    general_category = fields.Many2one('luckins.luckins')

    def getLuckinsMajorCategory(self):
        categories = self.env['luckins.luckins'].search([])
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/TaxonomyList/1'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        token = get_luckins_access_token()

        for cat in categories:
            sub_cat_list = []
            payload = {
                "Token":token,
                "ViewportType":3,
                "AssetSized2List":[],
                "TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":6,"TSIUniqueIdentifier":cat.luckins_id}]
            }
            sub_cat_request = requests.post(url, data = json.dumps(payload), headers=headers)
            sub_cat_data = sub_cat_request.json()
            unwanted_cat = ["Business Software","Plant & Tool Hire","Training Services","Stainless Steel Conduit Systems","Steel Perimeter Trunking","MICC Accessories","MICC Cables","UPS & Standby Power","Physical Security","Oil & Water Storage","Space Heating - Gas Fired","Space Heating - Oil Fired","Space Heating - Solid Fuel","Domestic Appliances - Gas Fired","Electrical Appliances","Laboratory Service Controls","Miscellaneous","Structural Steel Products","Air Line Systems","HPF Pipe Systems","Pre-Insulated Pipe Systems","Push-fit Fittings - Carbon Steel","Push-fit Fittings - Copper","Push-fit Fittings - Stainless Steel","Screwed Fittings - Stainless Steel","Stainless Steel Hygenic Fittings","Chemical Waste Drainage Systems","Stainless Steel Drainage Systems","Steel Rainwater Systems","Wind Turbines & Accessories","Sanitaryware","Site Layout Systems & Scanners","Stationery & Office Consumables","Wiring Accessories - Track Mounted",]
            if sub_cat_data.get('TaxonomyList'):
                for sub_cat in sub_cat_data.get('TaxonomyList'):
                    major_obj = self.env['luckins.major_category'].search([('luckins_id','=',sub_cat.get('TaxonomyCode'))])
                    if sub_cat.get('TaxonomyLabel') not in unwanted_cat and not major_obj:
                        sub_cat_list.append({
                          'luckins_id': sub_cat.get('TaxonomyCode'),
                          'name': sub_cat.get('TaxonomyLabel'),
                          'general_category': cat.id
                        })
            if sub_cat_list:
                self.env['luckins.major_category'].create(sub_cat_list)
                self.env.cr.commit()
        _logger.info('Major Category Updated')


class MinorCategories(models.Model):

    _name = 'luckins.minor_category'
    _description = 'luckins.minor_category'

    luckins_id = fields.Integer('Luckin Id')
    name = fields.Char('Category Name')
    created_date = fields.Datetime('Created Date', default=lambda self: fields.datetime.now())
    major_category = fields.Many2one('luckins.major_category')

    def getLuckinMinorCategory (self):
        major_category = self.env['luckins.major_category'].search([])
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/TaxonomyList/1'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        for min_cat_ in major_category:
            access_token = get_luckins_access_token()

            payload = {
            	"Token":access_token,
            	"ViewportType":3,
            	"AssetSized2List":[{"Height":300,"Width":300,"MaintainAspectRatio":1,"Tag":"supllier_logo"}],
            	"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":5,"TSIUniqueIdentifier":min_cat_.luckins_id}]
            }
            min_cat_request = requests.post(url, data = json.dumps(payload), headers=headers)
            min_cat_data = min_cat_request.json()
            min_cat_list = []
            valid_brands = ["1128","1136","1186","1258","1318","2312","2055","3082","3125","3140","3970","6033","4429","4484","3626","5059","5381","5460","5500","5879","5946","5775","4016","6796","7651","4264","7726","7990","7950","8860","8879","8881","8882","9025","5054","3682","4392","9220","9677","7725","9800","9897"]
            if min_cat_data.get('TaxonomyList'):
                for cat in min_cat_data["TaxonomyList"]:
                    minor_obj = self.env['luckins.minor_category'].search([('luckins_id','=',cat.get('TaxonomyCode'))])
                    if not minor_obj:
                        minor_obj = self.env['luckins.minor_category'].create({
                            'luckins_id': cat.get('TaxonomyCode'),
                            'name': cat.get('TaxonomyLabel'),
                            'major_category': min_cat_.id
                        })
                        self.env.cr.commit()
                    if cat.get('IPList'):
                        for brand in cat.get('IPList'):
                            if brand.get('IPCode') in valid_brands:
                                image_url = ""
                                for asset in brand["Asset2List"]:
                                    if asset["Tag"] == "supllier_logo":
                                        image_url = asset["URL"]
                                brands_obj = self.env['luckins.brands'].search([('supplier_id', '=', brand.get('IPCode'))])
                                if not brands_obj:
                                    brands_obj = self.env['luckins.brands'].create({
                                      'name': brand.get('SupplierName'),
                                      'supplier_id': brand.get('IPCode'),
                                      'image': image_url
                                    })
                                    self.env['luckins.productcount'].create({
                                      'brand': brands_obj.id,
                                      'minor_category': minor_obj.id,
                                      'item_count': brand.get('ItemCount')
                                    })
                                    self.env.cr.commit()
        _logger.info('Minor Category Updated')


class Brands(models.Model):

    _name = 'luckins.brands'
    _description = 'luckins.brands'

    name = fields.Char('Brand Name')
    supplier_id = fields.Char('Supplier ID')
    image = fields.Char('Image URL')

class BrandMajorCategory(models.Model):

    _name = "luckins.brand_major_category"
    _description = "luckins.brand_major_category"

    brand = fields.Many2one('luckins.brands')
    luckins_id = fields.Char('Luckin Id')
    name = fields.Char('Category Name')
    item_count = fields.Integer('Item Count')
    created_date = fields.Datetime('Created Date', default=lambda self: fields.datetime.now())

    def getBrandMajorCategory(self):
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/TaxonomyList/1'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        brands = self.env['luckins.brands'].search([])
        for brand in brands:
            access_token = get_luckins_access_token()
            obj = {
    			"Token":access_token,
    			"ViewportType":3,
    			"AssetSized2List":[],
    			"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":5,"TSIUniqueIdentifier":""},{"TSIUniqueIdentifierType":7,"TSIUniqueIdentifier":brand.supplier_id}]
    		}
            get_brand_major = requests.post(url, data = json.dumps(obj), headers=headers)
            brand_major_data = get_brand_major.json()
            cat_list = []
            for cat in brand_major_data.get('TaxonomyList'):
                brand_major = self.env['luckins.brand_major_category'].search([('luckins_id','=',cat.get('TaxonomyCode')), ('brand','=',brand.id)])
                if not brand_major:
                    cat_list.append({
                      'brand': brand.id,
                      'luckins_id': cat.get('TaxonomyCode'),
                      'name': cat.get('TaxonomyLabel'),
                      'item_count': cat.get('ItemCount')
                    })
            if len(cat_list) > 0:
                self.env['luckins.brand_major_category'].create(cat_list)
                _logger.info('Brand Major Category Created')
        _logger.info('Brand Major Category Successfully Updated')

class BrandMinorCategory(models.Model):

    _name = "luckins.brand_minor_category"
    _description = "luckins.brand_minor_category"

    major = fields.Many2one('luckins.brand_major_category')
    luckins_id = fields.Char('Luckin Id')
    name = fields.Char('Category Name')
    item_count = fields.Integer('Item Count')
    created_date = fields.Datetime('Created Date', default=lambda self: fields.datetime.now())

    def getBrandMinorCategory(self):
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/TaxonomyList/1'
        headers = {
    	    "Content-Type": "application/json",
    	    "Accept": "application/json",
    	}
        brand_major = self.env['luckins.brand_major_category'].search([])
        for brand in brand_major:
            access_token = get_luckins_access_token()
            myobj = {
    			"Token":access_token,
    			"ViewportType":3,
    			"AssetSized2List":[],
    			"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":3,"TSIUniqueIdentifier":brand.luckins_id}]
    		}
            minor_cat_request = requests.post(url, data = json.dumps(myobj), headers=headers)
            minor_cat_data = minor_cat_request.json()
            minor_list = []
            for cat in minor_cat_data.get('TaxonomyList'):
                minor_obj = self.env['luckins.brand_minor_category'].search([('luckins_id','=',cat.get('TaxonomyCode')),('major' , '=', brand.id)])
                if not minor_obj:
                    minor_list.append({
                       'major': brand.id,
                      'luckins_id': cat.get('TaxonomyCode'),
                      'name': cat.get('TaxonomyLabel'),
                      'item_count': cat.get('ItemCount')
                    })
            if len(minor_list) > 0:
                self.env["luckins.brand_minor_category"].create(minor_list)
                _logger.info('Brand Minor Category Created')
        _logger.info('Brand Minor Category Successfully Updated')

class ProductCount(models.Model):

    _name = 'luckins.productcount'
    _description = 'luckins.productcount'

    minor_category = fields.Many2one('luckins.minor_category')
    brand = fields.Many2one('luckins.brands')
    item_count = fields.Integer('Item Count')


class LuckinsProducts(models.Model):

    _name = 'luckins.product'
    _desctiption = 'luckins.product'

    name = fields.Char('Product Name')
    catelog_num = fields.Char('Product Catelog Number')


    def getLuckinsProducts(self):
        headers = {
    	    "Content-Type": "application/json",
    	    "Accept": "application/json",
    	}
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/ItemDetailsPicklist/1'
        single_product_url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/ItemDetail/1'
        category = self.env['luckins.productcount'].search([])
        for cat in category:
            access_token = get_luckins_access_token()
            obj = {
    			"Token":access_token,
    			"ViewportType": 3,
    			"AssetSized2List": [],
    			"PageSize": cat.item_count,
    			"TSIUniqueIdentifierPairList": [{"TSIUniqueIdentifierType":7,"TSIUniqueIdentifier": cat.brand.supplier_id},{"TSIUniqueIdentifierType":4,"TSIUniqueIdentifier": cat.minor_category.luckins_id}]
    		}
            product_data_request = requests.post(url, data = json.dumps(obj), headers = headers)
            luckins_product_list = product_data_request.json()
            print('==============Start===========')
            print(luckins_product_list)
            print('==============End===========')
