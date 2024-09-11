from odoo import models, fields, api
import logging
import json
import requests

_logger = logging.getLogger(__name__)

class FacebookCategory(models.Model):
    _name = 'facebook.category'
    _description = 'Facebook Categories List'

    # Các trường dữ liệu của model
    fb_category_name = fields.Char(string='Category Name')
    fb_category_id = fields.Char(string='Category ID')
    parent_category = fields.Many2one('facebook.category', string='Parent Category', index=True, ondelete='set null')
    parent_category_path = fields.Char(string='Parent Path')
    blog_category = fields.Many2many('blog.tag', string='Blog Categories')
    product_category = fields.Many2many('product.category', string='Product Categories')
    
    # product_category_names = fields.Char(string='Product Category Names', compute='_compute_product_category_names')

    # @api.depends('product_category')
    # def _compute_product_category_names(self):
    #     for record in self:
    #         if record.product_category:
    #             record.product_category_names = ', '.join(record.product_category.mapped('name'))
    #         else:
    #             record.product_category_names = ''

    def _format_category_name(self, category):
        # Giả sử phương thức này định dạng tên danh mục theo một cách nào đó
        return category.get('name', '').strip().title()

    def _create_or_update_category(self, categories, parent_category_id, parent_category_path):
        for category in categories:
            # Tạo hoặc cập nhật danh mục và các danh mục con
            fb_category_name = category.get('name')
            fb_category_id = category.get('id')
            path = parent_category_path + '/' + fb_category_name

            # Kiểm tra xem danh mục đã tồn tại chưa
            category_record = self.search([('fb_category_id', '=', fb_category_id)], limit=1)
            if category_record:
                # Nếu danh mục đã tồn tại, cập nhật nó
                category_record.write({
                    'fb_category_name': fb_category_name,
                    'parent_category': parent_category_id,
                    'parent_category_path': path,
                })
            else:
    
                # Nếu danh mục chưa tồn tại, tạo mới
                category_record = self.create({
                    'fb_category_name': fb_category_name,
                    'fb_category_id': fb_category_id,
                    'parent_category': parent_category_id,
                    'parent_category_path': path,
                })

            subcategories = category.get('fb_page_categories', [])
            if subcategories:
                self._create_or_update_category(subcategories, category_record.id, category_record.parent_category_path)

    @api.model
    def fetch_facebook_categories(self):
        access_token = self.env['ir.config_parameter'].sudo().get_param('facebook.api_token')
        
        url = f"https://graph.facebook.com/v20.0/fb_page_categories?access_token={access_token}"
        response = requests.get(url)
       
        if response.status_code == 200:
            categories = response.json().get('data', [])
            _logger.info("Kết nối thành công với Facebook API để lấy danh sách category.")
            
            # Kiểm tra xem danh mục cha đã tồn tại chưa
            parent_category = self.search([('fb_category_name', '=', None), ('fb_category_id', '=', None)], limit=1)
            if not parent_category:
                parent_category = self.create({
                    'fb_category_name': None,
                    'fb_category_id': None,
                    'parent_category': None,
                    'parent_category_path': None,
                })
            parent_category_path = ''
            self._create_or_update_category(categories, parent_category.id, parent_category_path)
        else:
            _logger.error("Không thể kết nối với Facebook API để lấy category facebook. Mã lỗi: %s, Phản hồi: %s", response.status_code, response.text)