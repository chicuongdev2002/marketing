import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class FacebookCatalogAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = 'https://graph.facebook.com/v20.0/'

    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.request(method, url, headers=headers, json=data)
        if response.status_code != 200:
            raise UserError(f"Lỗi khi thực hiện yêu cầu tới Facebook API: {response.status_code} {response.text}")
        return response.json()

    def create_product(self, catalog_id, product_data):
        endpoint = f"{catalog_id}/products"
        return self._make_request('POST', endpoint, data=product_data)

    def update_product(self, product_id, product_data):
        endpoint = f"{product_id}"
        return self._make_request('POST', endpoint, data=product_data)

    def delete_product(self, product_id):
        endpoint = f"{product_id}"
        return self._make_request('DELETE', endpoint)

class FacebookCatalogIntegration(models.Model):
    _name = 'facebook.catalog.integration'
    _description = 'Facebook Catalog Integration'

    name = fields.Char(string='Tên', required=True)
    # fb_access_token = fields.Char(string='Facebook Access Token', required=True)
    fb_catalog_id = fields.Char(string='Facebook Catalog ID', required=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company)
    manager_account_id = fields.Many2one('manager.account', string='Manager Account', required=True)
    def _get_api(self):
        access_token = self.manager_account_id.access_token
        return FacebookCatalogAPI(access_token)

    def post_product_to_catalog(self, product):
        api = self._get_api()
        
        product_variant = product.product_variant_id
        
        # Sử dụng một URL công khai thay vì localhost
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if 'localhost' in base_url:
            base_url = 'https://dev02.t4tek.tk'  # Thay thế bằng URL thực tế của bạn
        
        # Kiểm tra số lượng có sẵn một cách an toàn
        availability = 'available for order' if product.type == 'service' else 'in stock'
        
        # Đảm bảo rằng trường description luôn có giá trị
        description = product.description_sale or 'Không có mô tả'
        
        # Đảm bảo rằng sản phẩm có ít nhất một trong các số nhận dạng toàn cầu bắt buộc
        brand = product.company_id.name if hasattr(product, 'company_id') and product.company_id else ''
        # Đảm bảo URL được định dạng đúng
        image_url = f"{base_url}/web/image/product.template/{product.id}/image_1024"
        product_url = f"{base_url}/shop/{product.id}"  # Thay thế bằng URL thực tế của sản phẩm
        product_data = {
            'retailer_id': str(product.id),
            'name': product.name,
            'description': description,
            'price': int(product.list_price),  # Chuyển đổi giá trị price thành số nguyên
            'currency': product.currency_id.name,
            'availability': availability,
            'condition': 'new',
            'image_url': image_url,
            'brand': brand,
            'url': product_url
        }
        
        _logger.info(f"Đang đăng sản phẩm lên Facebook Catalog với dữ liệu: {product_data}")
        _logger.info(f"Sử dụng Catalog ID: {self.fb_catalog_id}")
        _logger.info(f"Access Token (10 ký tự đầu): {self.manager_account_id.access_token[:10]}...")
          # Kiểm tra và loại bỏ các trường có giá trị None
        product_data = {k: v for k, v in product_data.items() if v is not None}
        try:
            response = api.create_product(self.fb_catalog_id, product_data)
            if response:
                _logger.info(f"Sản phẩm {product.name} đã được đăng thành công lên Facebook Catalog. Phản hồi: {response}")
                _logger.info(f"URL đã post: {api.base_url}{self.fb_catalog_id}/products, Tham số: {product_data}")
                return response.get('id')
            else:
                _logger.error(f"Không thể đăng sản phẩm {product.name} lên Facebook Catalog.")
                return None
        except UserError as e:
            # _logger.error(f"Lỗi khi đăng sản phẩm lên Facebook Catalog: {str(e)}")
            raise

    def update_product_on_catalog(self, product):
        api = self._get_api()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if 'localhost' in base_url:
            base_url = 'https://dev02.t4tek.tk'
        product_variant = product.product_variant_id.with_context(prefetch_fields=False)
        
        # Đảm bảo rằng trường description luôn có giá trị
        description = product.description_sale or 'Không có mô tả'
        
        # Đảm bảo rằng sản phẩm có ít nhất một trong các số nhận dạng toàn cầu bắt buộc
        brand = product.company_id.name if hasattr(product, 'company_id') and product.company_id else ''
        
        # Đảm bảo URL được định dạng đúng
        image_url = product.image_1920 and f"{base_url}/web/image/product.template/{product.id}/image_1024" or ''
        product_url = f"{base_url}/shop/{product.id}" 
        product_data = {
            'retailer_id': str(product.id),
            'name': product.name,
            'description': description,
            'price': int(product.list_price),  # Chuyển đổi giá trị price thành số nguyên
            'currency': product.currency_id.name,
            'availability': 'in stock',  # Giả định sản phẩm luôn có sẵn
            'condition': 'new',
            'image_url': image_url,
            'brand': brand,
            'url': product_url
        }
        
        _logger.info(f"Cập nhật sản phẩm trên Facebook Catalog với dữ liệu: {product_data}")
        
        try:
            response = api.update_product(product.fb_catalog_product_id, product_data)
            if response:
                _logger.info(f"Sản phẩm {product.name} đã được cập nhật thành công trên Facebook Catalog. Phản hồi: {response}")
                _logger.info(f"URL đã post: {api.base_url}{product.fb_catalog_product_id}, Tham số: {product_data}")
                return True
            else:
                _logger.error(f"Không thể cập nhật sản phẩm {product.name} trên Facebook Catalog.")
                return False
        except UserError as e:
            _logger.error(f"Lỗi khi cập nhật sản phẩm trên Facebook Catalog: {str(e)}")
            raise

    def delete_product_from_catalog(self, product):
        api = self._get_api()
        
        _logger.info(f"Đang xóa sản phẩm {product.name} khỏi Facebook Catalog.")
        
        try:
            response = api.delete_product(product.fb_catalog_product_id)
            if response:
                _logger.info(f"Sản phẩm {product.name} đã được xóa thành công khỏi Facebook Catalog. Phản hồi: {response}")
                return True
            else:
                _logger.error(f"Không thể xóa sản phẩm {product.name} khỏi Facebook Catalog.")
                return False
        except UserError as e:
            _logger.error(f"Lỗi khi xóa sản phẩm khỏi Facebook Catalog: {str(e)}")
            raise

    def sync_products_with_catalog(self):
        products = self.env['product.template'].search([('fb_catalog_product_id', '!=', False)])
        for product in products:
            self.update_product_on_catalog(product)
