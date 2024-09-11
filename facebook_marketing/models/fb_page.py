from odoo import models, fields, api

class FacebookPage(models.Model):
    _name = 'facebook.page'
    _description = 'Facebook Page'

    account_id = fields.Many2one('manager.account', string='Account')
    page_avatar = fields.Binary('Avatar')
    page_name = fields.Char(string="Name")
    page_id = fields.Char(string="Page ID")
    access_token = fields.Char(string="Access Token")
    category = fields.Char(string="Main Category")
    category_ids = fields.Many2many('facebook.category', string='Categories', 
                                    relation='facebook_page_category_rel',
                                    column1='page_id', column2='category_id')
    is_favorite = fields.Boolean(string="Favorite", default=False, tracking=True)
    display_name = fields.Char(compute='_compute_display_name')
    
    @api.depends('page_name')
    def _compute_display_name(self):
        """
        Tính toán tên hiển thị của trang Facebook dựa trên tên trang.
        """
        for record in self:
            record.display_name = record.page_name

    def toggle_favorite(self):
        """
        Chuyển đổi trạng thái yêu thích của trang Facebook.
        Nếu is_favorite là True, nó sẽ được đặt thành False và ngược lại.
        """
        for record in self:
            record.is_favorite = not record.is_favorite