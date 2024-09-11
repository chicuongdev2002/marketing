
import json
import logging
from odoo import models, fields, api
import requests
import base64
from datetime import datetime, timedelta
import time

_logger = logging.getLogger(__name__)

class ManagerAccount(models.Model):
    _name = 'manager.account'
    _description = 'Load account facebook information'
    
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    # Thêm trường này
    is_favorite = fields.Boolean(string="Favorite", default=False, tracking=True)
    account_name = fields.Char('User Name')
    account_id = fields.Char(string='Account ID', required=True)
    access_token = fields.Text('Access Token', required=True)
    account_avatar = fields.Binary('Avatar')
    page_ids = fields.One2many('facebook.page', 'account_id', string="Pages")
    display_name = fields.Char(compute='_compute_display_name')
    cliend_id = fields.Char('Client ID', required=True)
    id_secret = fields.Char('Client Secret', required=True)
    last_token_refresh = fields.Datetime('Last Token Refresh')

    @api.depends('account_name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.account_name
    #Load dữ liệu        
    def load_data(self):
        for record in self:
            record.load_account_info()
            record.load_account_ava()
            record.load_pages()
        return True
    # Tự động Refesh token
    def _cron_refresh_tokens(self):
        accounts = self.search([])
        for account in accounts:
            if account.update_access_token():
                account.load_data()
    def update_access_token(self, max_retries=3, retry_delay=5):
     now = fields.Datetime.now()
     if not self.last_token_refresh or (now - self.last_token_refresh) > timedelta(minutes=1):
        url = "https://graph.facebook.com/v20.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.cliend_id,
            "client_secret": self.id_secret,
            "fb_exchange_token": self.access_token
        }
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    self.last_token_refresh = now
                    _logger.info(f"Token truy cập đã được cập nhật cho tài khoản {self.account_name}")
                    return True
                else:
                    _logger.warning(f"Phản hồi không mong đợi cho tài khoản {self.account_name}: {data}")
            except requests.exceptions.RequestException as e:
                error_message = str(e)
                if response.status_code == 400:
                    error_details = response.json().get('error', {})
                    error_message = f"Lỗi {error_details.get('code')}: {error_details.get('message')}"
                
                _logger.error(f"Lỗi cập nhật token truy cập cho tài khoản {self.account_name}: {error_message}")
                
                if attempt < max_retries - 1:
                    _logger.info(f"Thử lại sau {retry_delay} giây...")
                    time.sleep(retry_delay)
                else:
                    _logger.error(f"Không thể cập nhật token sau {max_retries} lần thử")
                    # Thông báo cho admin hoặc người dùng về lỗi liên tục
                    self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                        'title': 'Lỗi Làm Mới Token',
                        'message': f"Không thể làm mới token cho {self.account_name}. Vui lòng kiểm tra thông tin đăng nhập và quyền của ứng dụng.",
                        'type': 'danger',
                    })
                    return False
     return True
    #Load thông tin account
    def load_account_info(self):
        url_info_request = f'https://graph.facebook.com/v20.0/{self.account_id}?access_token={self.access_token}'  
        try:
            info_response = requests.get(url_info_request)
            info_data = info_response.json()

            # logging.info(info_data)

            #set fields
            self.account_name = info_data['name']

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get account info: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
        return None
    #Load avatar
    def load_account_ava(self):
        url_avatar_request = f'https://graph.facebook.com/v20.0/{self.account_id}/picture?type=large&access_token={self.access_token}'
        try:
            avatar_response = requests.get(url_avatar_request)

            #set fields
            self.account_avatar = base64.b64encode(avatar_response.content).decode('utf-8')

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get Avatar: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
        return None
    #Load pages
    def load_pages(self):
        url_pages_request = f'https://graph.facebook.com/v20.0/{self.account_id}/accounts?access_token={self.access_token}'
        try:
            pages_response = requests.get(url_pages_request)
            page_data = pages_response.json()

            if page_data and 'data' in page_data:
                for page in page_data['data']:
                    # Tạo hoặc cập nhật Facebook Page
                    facebook_page = self.env['facebook.page'].search([('page_id', '=', page['id'])], limit=1)
                    if not facebook_page:
                        facebook_page = self.env['facebook.page'].create({
                            'account_id': self.id,
                            'page_name': page['name'],
                            'page_id': page['id'],
                            'page_avatar': self.get_pages_ava(page['id']),
                            'access_token': page['access_token'],
                            'category': page['category']
                        })
                    else:
                        facebook_page.write({
                            'page_name': page['name'],
                            'page_avatar': self.get_pages_ava(page['id']),
                            'access_token': page['access_token'],
                            'category': page['category']
                        })

                    # Xử lý các category
                    category_ids = []
                    if 'category_list' in page:
                        for category in page['category_list']:
                            fb_category = self.env['facebook.category'].search([('fb_category_id', '=', category['id'])], limit=1)
                            if fb_category:
                                category_ids.append(fb_category.id)
                            else:
                                # Nếu category không tồn tại, bạn có thể quyết định tạo mới hoặc bỏ qua
                                new_category = self.env['facebook.category'].create({
                                    'fb_category_name': category['name'],
                                    'fb_category_id': category['id'],
                                })
                                category_ids.append(new_category.id)
                        
                    # Cập nhật các category cho Facebook Page
                    facebook_page.write({
                        'category_ids': [(6, 0, category_ids)]
                    })

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get Page: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
        return None
    #Load avatar page
    def get_pages_ava(self, page_id):
        url_page_ava_request = f'https://graph.facebook.com/v20.0/{page_id}/picture?type=large&access_token={self.access_token}'
        try:
            avatar_page_response = requests.get(url_page_ava_request)
            return base64.b64encode(avatar_page_response.content)
            # logging.info(base64.b64encode(avatar_page_response.content))
            # return base64.b64encode(avatar_page_response.content)

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get Avatar Page: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
            return None   
    #Thêm vào yêu thích
    def toggle_favorite(self):
        for record in self:
            record.is_favorite = not record.is_favorite