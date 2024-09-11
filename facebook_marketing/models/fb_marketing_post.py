import requests
import json
from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import base64
import logging
import random
import traceback
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request

_logger = logging.getLogger(__name__)

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    content_id = fields.Many2one('marketing.content', string='Content', default=lambda self: self._get_latest_content())
    account_id = fields.Many2one('manager.account', string='Account', required=True)
    page_id = fields.Many2one('facebook.page', string='Page', domain="[('account_id', '=', account_id)]")
    post_now = fields.Boolean(string='Post Now')
    schedule_post = fields.Datetime(string='Đặt lịch post bài')
    comment = fields.Text(string='Comment')
    comment_suggestion_id = fields.Many2many('marketing.comment', string='Comment Suggestion')
    remind_time = fields.Selection([
        ('1', '1 minute'),
        ('2', '2 minutes'), 
        ('3', '3 minutes'),
        ('4', '4 minutes'),
        ('5', '5 minutes'),
        ('stop', 'Stop Auto Comment')
    ], string='Remind Time', default='')
    last_auto_comment_time = fields.Datetime('Last Auto Comment Time')
    start_auto_comment = fields.Datetime(string='Start Auto Comment')
    end_auto_comment = fields.Datetime(string='End Auto Comment')
    last_comment_index = fields.Integer('Chỉ số comment cuối cùng', default=-1)
    post_id = fields.Char('Post ID')
    post_url = fields.Char('Post URL')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft')
    # Chọn content mới nhất được lưu
    @api.model
    def _get_latest_content(self):
        return self.env['marketing.content'].search([], order='create_date desc', limit=1).id
    @api.onchange('content_id')
    def _onchange_content_id(self):
        if self.content_id:
            self.comment = self.content_id.content
    @api.model
    def create(self, vals):
        if 'content_id' not in vals:
            vals['content_id'] = self._get_latest_content()
        return super(MarketingPost, self).create(vals)
    @api.model
    def run_auto_comment_cron(self):
        _logger.info("Chạy cron job auto-comment")
        self._auto_comment()
    @api.onchange('post_now')
    def _onchange_post_now(self):
        if self.post_now:
            self.schedule_post = False
        else:
            self.schedule_post = fields.Datetime.now()
    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.page_id = False
        return {'domain': {'page_id': [('account_id', '=', self.account_id.id)]}}
    
    @api.onchange('comment_suggestion_id')
    def _onchange_comment_suggestion_id(self):
     if self.comment_suggestion_id:
        self.comment = '\n'.join(comment.name for comment in self.comment_suggestion_id)
     else:
        self.comment = ''
 
    @api.onchange('schedule_post')
    def _onchange_schedule_post(self):
        for record in self:
            if record.schedule_post:
                record.state = 'scheduled'
                record.start_auto_comment = record.schedule_post
                record.end_auto_comment = record.start_auto_comment + timedelta(weeks=1)
                _logger.info(f"Đặt lịch post bài với ID {record.id} vào lúc {record.schedule_post}")
    def post_next_comment_to_facebook(self):
     if not self.comment_suggestion_id:
        _logger.warning(f"Không tìm thấy gợi ý bình luận cho bài đăng có ID {self.id}")
        return

     comment_suggestions = self.comment_suggestion_id.mapped('name')
     if not comment_suggestions:
        _logger.warning(f"Danh sách gợi ý bình luận trống cho bài đăng có ID {self.id}")
        return

     # Tăng chỉ số và quay vòng nếu cần
     self.last_comment_index = (self.last_comment_index + 1) % len(comment_suggestions)
     comment_content = comment_suggestions[self.last_comment_index]

     if not comment_content or comment_content.lower() == 'false':
        _logger.warning(f"Bình luận được chọn không hợp lệ cho bài đăng có ID {self.id}: {comment_content}")
        return

     self.post_comment_to_facebook(comment_content)
     _logger.info(f"Đã đăng bình luận tiếp theo cho bài đăng có ID {self.id}: {comment_content}")
    #Post theo lịch
    def _post_scheduled(self):
        current_time = datetime.now()
        _logger.info(f"Kiểm tra các bài viết đã được lên lịch vào lúc {current_time}")
        scheduled_posts = self.search([('schedule_post', '<=', current_time), ('state', '=', 'scheduled')])
        _logger.info(f"Tìm thấy {len(scheduled_posts)} bài viết đã được lên lịch để xử lý")
        for post in scheduled_posts:
            _logger.info(f"Đang cố gắng đăng bài viết với ID {post.id}")
            post.post_to_facebook()
            if post.state == 'posted':
                _logger.info(f"Đăng bài viết thành công với ID {post.id}")
            else:
                _logger.error(f"Đăng bài viết thất bại với ID {post.id}")
       # Chọn content mới nhất được lưu
    @api.model
    def _get_latest_content(self):
        return self.env['marketing.content'].search([], order='create_date desc', limit=1)

    #Post facebook
    
    def post_to_facebook(self):
        content = self.content_id.content or "Không lấy được content"
        logging.info("-----------------------------------------------------------------")
        logging.info("%s \n\n\n\n", self.content_id)
        
        images = self.content_id.image_ids
        
        try:
            access_token = self.account_id.access_token
            page_id = self.page_id.page_id

            # Tải lên từng ảnh riêng lẻ
            media_ids = []
            for idx, attachment in enumerate(images):
                _logger.info(f"Available fields for attachment: {attachment._fields.keys()}")
                _logger.info(f"Attachment data: {attachment.read()}")
                
                image_data = attachment.image or attachment.datas
                if not image_data:
                    _logger.warning(f"Ảnh {idx} không có dữ liệu, bỏ qua.")
                    continue
                
                image_data = base64.b64decode(image_data)
                files = {f'file{idx}': (f'image{idx}.jpg', image_data, 'image/jpeg')}
                photo_data = {
                    'access_token': access_token,
                    'published': False  # Không đăng ảnh ngay lập tức
                }
                photo_response = requests.post(
                    f'https://graph.facebook.com/{page_id}/photos',
                    data=photo_data,
                    files=files
                )
                photo_response.raise_for_status()
                media_ids.append({'media_fbid': photo_response.json()['id']})

            # Tạo bài đăng với tất cả ảnh đã tải lên
            data = {
                'message': content,
                'access_token': access_token,
                'attached_media': json.dumps(media_ids)
            }

            _logger.info(f"Attempting to post to page {page_id}")
            _logger.info(f"Data being sent: {data}")
            _logger.info(f"Number of images being sent: {len(media_ids)}")

            response = requests.post(
                f'https://graph.facebook.com/{page_id}/feed',
                data=data
            )

            _logger.info(f"Response status code: {response.status_code}")
            _logger.info(f"Response content: {response.content}")

            response.raise_for_status()
            post_data = response.json()
            self.post_id = post_data.get('id')
            self.post_url = f"https://www.facebook.com/{self.post_id.replace('_', '/posts/')}"

            if self.content_id.include_link and self.content_id.url:
                try:
                    comment_response = requests.post(
                        f'https://graph.facebook.com/{self.post_id}/comments',
                        data={
                            'message': self.content_id.url,
                            'access_token': access_token
                        }
                    )
                    comment_response.raise_for_status()
                    _logger.info(f"Thêm bình luận thành công với URL sản phẩm vào bài viết")
                except requests.exceptions.RequestException as e:
                    _logger.error(f"Thêm bình luận URL thất bại : {e}")
                    _logger.error(f"Comment response content: {e.response.content if e.response else 'No response content'}")

            self.state = 'posted'
            self.start_auto_comment = datetime.now()
            self.end_auto_comment = self.start_auto_comment + timedelta(weeks=1)
        
        except requests.exceptions.RequestException as e:
            self.state = 'failed'
            _logger.error(f"Đăng lên trang '{page_id}' thất bại: {e}")
            _logger.error(f"Response content: {e.response.content if e.response else 'No response content'}")
            _logger.debug(f"Nội dung phản hồi: {e.response.content if e.response else 'Không có nội dung phản hồi'}")
        except Exception as e:
         self.state = 'failed'
         error_message = f"Lỗi không xác định khi đăng bài: {e}"
         _logger.error(error_message)
         _logger.error(f"Traceback: {traceback.format_exc()}")
         raise UserError(error_message)

        _logger.info("Kết thúc quá trình đăng bài lên Facebook")
        return True
    #Post comment
    def post_comment_to_facebook(self, comment_content=None):
     if comment_content is None:
        comment_content = self.comment or "Bình luận mặc định"
    
     if not comment_content or comment_content.lower() == 'false':
        _logger.warning(f"Nội dung bình luận không hợp lệ cho bài đăng có ID {self.post_id}: {comment_content}")
        return

     page_url = f'https://graph.facebook.com/{self.post_id}/comments'
     try:
        response = requests.post(
            page_url,
            data={
                'message': comment_content,
                'access_token': self.page_id.access_token
            }
        )
        response.raise_for_status()
        _logger.info(f"Đã đăng bình luận thành công cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}': {comment_content}")

     except requests.exceptions.RequestException as e:
        _logger.error(f"Không thể đăng bình luận cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}': {e}")
        _logger.error(f"Nội dung phản hồi: {e.response.content if e.response else 'Không có nội dung phản hồi'}")
    #Auto comment
    def _auto_comment(self):
     current_time = fields.Datetime.now()
     _logger.info(f"Đang chạy kiểm tra tự động bình luận lúc {current_time}")
    
     posts_to_comment = self.search([
        ('state', '=', 'posted'),
        ('post_id', '!=', False),
        ('start_auto_comment', '<=', current_time),
        ('end_auto_comment', '>=', current_time),
        ('remind_time', '!=', 'stop'),
        '|', ('last_auto_comment_time', '=', False),
        ('last_auto_comment_time', '<=', current_time - timedelta(minutes=1))
     ])
    
     _logger.info(f"Tìm thấy {len(posts_to_comment)} bài đăng cần bình luận")

     for post in posts_to_comment:
        if post.remind_time and post.remind_time != 'stop':
            minutes_since_last_comment = (current_time - (post.last_auto_comment_time or post.start_auto_comment)).total_seconds() / 60
            if minutes_since_last_comment >= float(post.remind_time):
                _logger.info(f"Đang đăng bình luận tự động cho bài đăng có ID {post.id}")
                post.post_next_comment_to_facebook()
                post.last_auto_comment_time = current_time
                _logger.info(f"Đã cập nhật thời gian bình luận tự động cuối cùng cho bài đăng có ID {post.id} thành {post.last_auto_comment_time}")
    #Post comment ngẫu nhiên       
    def post_random_comment_to_facebook(self):
     if not self.comment_suggestion_id:
        _logger.warning(f"Không tìm thấy gợi ý bình luận cho bài đăng có ID {self.id}")
        return

     comment_suggestions = self.comment_suggestion_id.mapped('name')
     if not comment_suggestions:
        _logger.warning(f"Danh sách gợi ý bình luận trống cho bài đăng có ID {self.id}")
        return

     comment_content = random.choice(comment_suggestions)
     if not comment_content or comment_content.lower() == 'false':
        _logger.warning(f"Bình luận ngẫu nhiên được chọn không hợp lệ cho bài đăng có ID {self.id}: {comment_content}")
        return

     self.post_comment_to_facebook(comment_content)
     _logger.info(f"Đã đăng bình luận ngẫu nhiên cho bài đăng có ID {self.id}: {comment_content}")
    #Button post comment
    def post_comment_button(self):
        for record in self:
            comment_content = record.comment or 'Default comment'
            record.post_comment_to_facebook(comment_content)
    
        if self.schedule_post:
            self.state = 'scheduled'
            self._post_scheduled()
        else:
            raise UserError('Vui lòng chọn thời gian post bài.') 
    @api.model
    def create(self, vals):
        record = super(MarketingPost, self).create(vals)
        if record.post_now:
            record.post_to_facebook()
            record.state = 'posted'
        elif record.schedule_post:
            record.state = 'scheduled'
        return record
    def write(self, vals):
        res = super(MarketingPost, self).write(vals)
        for record in self:
            if 'post_now' in vals and vals['post_now']:
                record.post_to_facebook()
                record.state = 'posted'
            elif 'schedule_post' in vals and vals['schedule_post']:
                record.state = 'scheduled'
        return res       