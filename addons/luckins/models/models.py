# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import requests
import base64
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

        for cat in categories:
            sub_cat_list = []
            token = get_luckins_access_token()
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
    flag_bit = fields.Boolean(default = False,string = 'Flag Bit')
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
                self.env.cr.commit()
                _logger.info('Brand Minor Category Created')
        _logger.info('Brand Minor Category Successfully Updated')

class ProductCount(models.Model):

    _name = 'luckins.productcount'
    _description = 'luckins.productcount'

    minor_category = fields.Many2one('luckins.minor_category')
    brand = fields.Many2one('luckins.brands')
    item_count = fields.Integer('Item Count')

class ProductAtrributes(models.Model):

    _name = 'luckins.productatrribute'
    _description = 'luckins.productatrribute'

    product = fields.Many2one('luckins.product')
    name= fields.Char('Attribute Name')

class ProductAAttributeValue(models.Model):
    _name = 'luckins.productvalue'
    _description = 'luckins.productvalue'

    product = fields.Many2one('luckins.product')
    attribute = fields.Many2one('luckins.productatrribute')
    name= fields.Char('Attribute Name')
    value= fields.Char('Attribute Value')

def getImageFromURL(url):
    ImageSend = None
    if url:
        r = requests.get(url, allow_redirects=True)
        image = base64.b64encode(r.content)
        ImageSend = image.decode('ascii')
    return ImageSend

class LuckinsProducts(models.Model):

    _name = 'luckins.product'
    _desctiption = 'luckins.product'

    name = fields.Char('Product Name')
    catelog_no = fields.Char('Product Catelog Number')
    category = fields.Many2one('luckins.minor_category', string="Category")
    minor_cat = fields.Many2one('luckins.brand_minor_category', string="Brand Minor Category")
    product_type = fields.Char('Product Type')
    dimensions = fields.Char('Dimensions')
    finish = fields.Char('finish')
    short_desc = fields.Char('Short Description')
    short_key = fields.Char('Sort Key')
    other_desc = fields.Char('Other Description')
    luckin_live_description = fields.Text('Luckin Live Description')
    product_id = fields.Char('Luckin Product ID')
    price = fields.Float('Product Price')
    base_price = fields.Float('Product Base Price')
    discount = fields.Float('Product Discount')
    thumbnail = fields.Image('Thumbnail Image')
    small_thumbnail = fields.Image('Small Thumbnail')
    large_thumbnail = fields.Image('Large Thumbnail')
    big_image = fields.Image('Image')
    user_manual = fields.Char('User Manual')
    certifications = fields.Char('Certifications')
    technical_data_sheet = fields.Char('Technical Data Sheet')
    installation_time = fields.Char('Installation Time')
    odoo_id = fields.Integer('Odoo Id')
    priceper = fields.Char('Per Price')
    pricedes = fields.Char('Price Description')

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
            for product in luckins_product_list.get('PickListItemDetailsList'):
                catalogue_no = product.get('CatalogueNumber')
                vareint = False
                vareint_exists = self.env['luckins.product'].search([('catelog_no', '=', catalogue_no), ('product_id', '!=', product.get('TSIItemCode'))])
                if vareint_exists:
                    vareint = True

                access_token = get_luckins_access_token()
                if product.get('CatalogueNumber'):
                    product_req_data = {
                        "Token":access_token,
      					"ViewportType":3,
      					"AssetSized2List":[{"Height":100,"Width":100,"MaintainAspectRatio":1,"Tag":"small_thumbnails"},{"Height":400,"Width":400,"MaintainAspectRatio":1,"Tag":"large_thumbnails"},{"Height":800,"Width":800,"MaintainAspectRatio":1,"Tag":"large_image"}],
      					"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":1,"TSIUniqueIdentifier":product.get('TSIItemCode')}]
                        }
                    product_request = requests.post(single_product_url, data = json.dumps(product_req_data), headers=headers)
                    product_data = product_request.json()
                    sleep(5)
                    product_item = product_data.get('ItemDetailsList')[0]
                    product_id = product_item.get('TSIItemCode')
                    name = product_item.get('Product')
                    short_desc = product_item.get('ShortDescription')
                    small_thumbnail = ''
                    large_thumbnail = ''
                    big_image = ''
                    certifications = None
                    technical_data_sheet = None
                    user_manual = None
                    thumbnail = getImageFromURL(product_item.get('ThumbnailURL'))
                    for image_list in product_item.get('Asset2List'):
                        if image_list.get('Tag') == 'VIEWPORT_DESKTOP':
                            for image in image_list.get('Asset2CustomSizeList'):
                                if image.get('Tag') == 'small_thumbnails':
                                    small_thumbnail = image.get('URL')
                                    small_thumbnail = getImageFromURL(small_thumbnail)
                                elif image.get('Tag') == 'large_thumbnails':
                                    large_thumbnail = image.get('URL')
                                    large_thumbnail = getImageFromURL(large_thumbnail)
                                else:
                                    big_image = image.get('URL')
                                    big_image = getImageFromURL(big_image)
                        elif image_list.get('AdditionalInfo') == "URL":
                            certifications = image_list.get('URL')
                        elif image_list.get('AdditionalInfo') == "Technical Data Sheet":
                            technical_data_sheet = image_list.get('URL')
                        elif image_list.get('AdditionalInfo') == "User Manual":
                            user_manual = image_list.get('URL')
                        else:
                            continue

                    try:
                        minor_cat = self.env['luckins.brand_minor_category'].search([('luckins_id', '=', product_item.get('ProductRangeCodeMinor'))])
                    except Exception as e:
                        minor_cat = None

                    product_ = {}
                    product_['name'] = name
                    product_['dimensions'] = product_item.get('Dimensions')
                    product_['finish'] = product_item.get('Finish')
                    product_['short_desc'] = short_desc
                    product_['other_desc'] = product_item.get('OtherDesc')
                    product_['price'] = product_item.get('CalculatedDiscountedPrice')
                    product_['base_price'] = product_item.get('BasePrice')
                    product_['discount'] = product_item.get('Discount')
                    product_['product_type'] = product_item.get('ProductType')
                    product_['luckin_live_description'] = product_item.get('LUCKINSliveDescription')
                    product_['catelog_no'] = catalogue_no
                    product_['installation_time'] = product_item.get('InstallationTime')
                    product_['short_key'] = product_item.get('Sortkey')
                    product_['product_id'] =  product_id
                    product_['big_image'] =  big_image
                    product_['small_thumbnail'] =  small_thumbnail
                    product_['large_thumbnail'] =  large_thumbnail
                    product_['category'] =  cat.minor_category.id
                    product_['thumbnail'] =  thumbnail
                    product_['certifications'] =  certifications
                    product_['technical_data_sheet'] =  technical_data_sheet
                    product_['user_manual'] =  user_manual
                    product_['priceper'] = product.get('PickListItemPriceList')[0].get('PricePer')
                    product_['pricedes'] = product.get('PickListItemPriceList')[0].get('PriceDescription')

                    if minor_cat:
                        product_['minor_cat'] = minor_cat.id

                    products_obj = self.env['luckins.product'].search([('product_id', '=', product_id), ('category', '=', cat.minor_category.id)])
                    if not products_obj:
                        products_obj = self.env['luckins.product'].create(product_)
                    else:
                        products_obj.write(product_)
                    self.env.cr.commit()
                    if product_data.get('AttributeLabelList'):
                        self.env['luckins.productatrribute'].search([('product', '=', products_obj.id)]).unlink()
                        for attrb in product_data.get('AttributeLabelList'):
                            attribute_valu_dict = next((d for d in product_item.get('AttributeList') if d["AttributeLabelID"] == attrb["ID"]), None)
                            attrib_list = list(filter(lambda x: x.get('AttributeLabelID') == attrb.get('ID'), product_item.get('AttributeList')))
                            attribute = self.env['luckins.productatrribute'].create({
                              'product': products_obj.id,
                              'name': attrb.get('Description')
                            })
                            for value in attrib_list:
                                self.env['luckins.productvalue'].create({
                                  'product': products_obj.id,
                                  'name': attribute.name,
                                  'value': value.get('Value'),
                                  'attribute': attribute.id
                                })
                        self.env.cr.commit()

    def getMinorProducts(self):
        url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/ItemDetailsPicklist/1'
        single_product_url = 'https://xtra.luckinslive.com/LuckinsLiveRESTHTTPS/ItemDetail/1'
        headers = {
    	    "Content-Type": "application/json",
    	    "Accept": "application/json",
    	}
        new_record_fetch = True
        is_flag_exist = self.env['luckins.brand_minor_category'].search([('flag_bit', '=', True)])
        if is_flag_exist:
            new_record_fetch = False
        min_cats = self.env['luckins.brand_minor_category'].search([])
        for min in min_cats:
            if min.flag_bit:
                new_record_fetch = True
            if not new_record_fetch:
                continue
            min.write({
              'flag_bit': True
            })
            access_token = get_luckins_access_token()
            myobj = {
    			"Token":access_token,
    			"ViewportType":3,
    			"AssetSized2List":[],
    			"PageSize": min.item_count,
    			"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":2,"TSIUniqueIdentifier": min.luckins_id},{"TSIUniqueIdentifierType":7,"TSIUniqueIdentifier":min.major.brand.supplier_id}]
    		}
            products_request = requests.post(url, data = json.dumps(myobj), headers=headers)
            products_data = products_request.json()
            for product in products_data.get('PickListItemDetailsList'):
                catalogue_no = product.get('CatalogueNumber')
                is_varient = False
                varients = self.env['luckins.product'].search([( 'catelog_no', "=", catalogue_no), ('product_id', '!=', product.get('TSIItemCode'))])
                if varients:
                    is_varient = True

                if product.get('CatalogueNumber'):
                    access_token = get_luckins_access_token()
                    product_req_data =  {
    					"Token":access_token,
    					"ViewportType":3,
    					"AssetSized2List":[{"Height":100,"Width":100,"MaintainAspectRatio":1,"Tag":"small_thumbnails"},{"Height":400,"Width":400,"MaintainAspectRatio":1,"Tag":"large_thumbnails"},{"Height":800,"Width":800,"MaintainAspectRatio":1,"Tag":"large_image"}],
    					"TSIUniqueIdentifierPairList":[{"TSIUniqueIdentifierType":1,"TSIUniqueIdentifier":product.get('TSIItemCode')}]
    				}
                    product_request = requests.post(single_product_url, data = json.dumps(product_req_data), headers=headers)
                    product_data = product_request.json()
                    sleep(5)
                    product_item = product_data["ItemDetailsList"][0]
                    try:
                        category = self.env['luckins.minor_category'].search([('luckins_id', '=', product_item.get('CommodityCodeMinor'))])
                    except Exception as e:
                        category = None
                    product_id = product_item.get('TSIItemCode')
                    name = product_item.get('Product')
                    short_desc = product_item.get('ShortDescription')
                    small_thumbnail = ''
                    large_thumbnail = ''
                    big_image = ''
                    certifications = None
                    technical_data_sheet = None
                    user_manual = None
                    count = 1
                    thumbnail = getImageFromURL(product_item.get('ThumbnailURL'))
                    other_images_urls = []
                    for images_list in product_item.get('Asset2List'):
                        if images_list.get('Tag') == "VIEWPORT_DESKTOP":
                            for images in images_list.get('Asset2CustomSizeList'):
                                if count == 1:
                                    if images.get('Tag') == "small_thumbnails":
                                        small_thumbnail = getImageFromURL(images.get('URL'))
                                    elif images.get('Tag') == "large_thumbnails":
                                        large_thumbnail = getImageFromURL(images.get('URL'))
                                    else:
                                        big_image = getImageFromURL(images.get('URL'))
                                else:
                                    if images.get('Tag') == "large_image":
                                        other_images_urls.append(images.get('URL'))
                        elif images_list.get('AdditionalInfo') == "URL":
                            certifications = images_list["AdditionalInfo"]
                        elif images_list.get('AdditionalInfo') == "Technical Data Sheet":
                            technical_data_sheet = images_list.get('URL')
                        elif images_list.get('AdditionalInfo') == "User Manual":
                            user_manual = images_list.get('URL')
                        else:
                            continue
                        count += 1
                    tax_id = ""
                    product_ = {}
                    product_['name'] = name
                    product_['dimensions'] = product_item.get('Dimensions')
                    product_['finish'] = product_item.get('Finish')
                    product_['short_desc'] = short_desc
                    product_['other_desc'] = product_item.get('OtherDesc')
                    product_['price'] = product_item.get('CalculatedDiscountedPrice')
                    product_['base_price'] = product_item.get('BasePrice')
                    product_['discount'] = product_item.get('Discount')
                    product_['product_type'] = product_item.get('ProductType')
                    product_['luckin_live_description'] = product_item.get('LUCKINSliveDescription')
                    product_['catelog_no'] = catalogue_no
                    product_['installation_time'] = product_item.get('InstallationTime')
                    product_['short_key'] = product_item.get('Sortkey')
                    product_['product_id'] =  product_id
                    product_['big_image'] =  big_image
                    product_['small_thumbnail'] =  small_thumbnail
                    product_['large_thumbnail'] =  large_thumbnail
                    if category:
                        product_['category'] =  category.id
                    product_['thumbnail'] =  thumbnail
                    product_['certifications'] =  certifications
                    product_['technical_data_sheet'] =  technical_data_sheet
                    product_['user_manual'] =  user_manual
                    product_['minor_cat'] =  min.id
                    product_['priceper'] = product.get('PickListItemPriceList')[0].get('PricePer')
                    product_['pricedes'] = product.get('PickListItemPriceList')[0].get('PriceDescription')
#
                    products_obj = self.env['luckins.product'].search([('product_id', '=', product_id), ('minor_cat', '=', min.id)])
                    if not products_obj:
                        products_obj = self.env['luckins.product'].create(product_)
                    else:
                        products_obj.write(product_)
                    self.env.cr.commit()

                    if product_data.get('AttributeLabelList'):
                        self.env['luckins.productatrribute'].search([('product', '=', products_obj.id)]).unlink()
                        for attrb in product_data.get('AttributeLabelList'):
                            attribute_valu_dict = next((d for d in product_item.get('AttributeList') if d["AttributeLabelID"] == attrb["ID"]), None)
                            attrib_list = list(filter(lambda x: x.get('AttributeLabelID') == attrb.get('ID'), product_item.get('AttributeList')))
                            attribute = self.env['luckins.productatrribute'].create({
                              'product': products_obj.id,
                              'name': attrb.get('Description')
                            })
                            for value in attrib_list:
                                self.env['luckins.productvalue'].create({
                                  'product': products_obj.id,
                                  'name': attribute.name,
                                  'value': value.get('Value'),
                                  'attribute': attribute.id
                                })
                        self.env.cr.commit()


    def ImportProducts(self):
        products = self.env['luckins.product'].search([('odoo_id', '=', None)])
        for product in products:
            product_template = self.env['product.template'].create({
              'name': product.short_desc,
              'type': 'consu',
              'description_sale': product.other_desc,
                'image_1920':product.large_thumbnail,
                'image_1024':product.big_image,
                'image_512':product.small_thumbnail,
                'image_256':product.thumbnail,
                'image_128':product.big_image,
                'list_price': float(product.pricedes.replace('£', '')),
                'lst_price': float(product.pricedes.replace('£', ''))
            })
            attribute = self.env['luckins.productatrribute'].search([('product', '=', product.id)])
            attrb_list = []
            for attrb in attribute:
                attribute_temp = self.env['product.attribute'].search([('name', '=', attrb.name)], limit=1)
                if not attribute_temp:
                    attribute_temp = self.env['product.attribute'].create({
                      'name': attrb.name
                    })
                values = self.env['luckins.productvalue'].search([( 'attribute', '=', attrb.id )])
                val_list = []
                for val in values:
                    valu = self.env['product.attribute.value'].search([('name', '=', val.value), ('attribute_id', '=', attribute_temp.id)])
                    if not valu:
                        valu = self.env['product.attribute.value'].create({
                          'name': val.value,
                          'attribute_id': attribute_temp.id
                        })
                    val_list.append(valu.id)
                temp_attrb = self.env['product.template.attribute.line'].create({
                  'attribute_id' : attribute_temp.id,
                  'value_ids' : val_list,
                  'product_tmpl_id' :product_template.id
                })
                attrb_list.append(temp_attrb.id)
            product_template.write({
                'attribute_line_ids': attrb_list
            })
            product_product = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)])
            for prop in product_product:
                prop.write({
                  'default_code': product.product_id,
                  'image_variant_1920': product.large_thumbnail,
                  'image_variant_1024': product.big_image,
                  'image_variant_128': product.small_thumbnail,
                  'image_variant_512': product.thumbnail,
                  'image_variant_256': product.big_image,
                })
            product.write({
              'odoo_id': product_template.id
            })
