from odoo import models, fields, api
import requests

class FacebookGroup(models.Model):
    _name = 'facebook.group'
    _description = 'Facebook Group'

    account_id = fields.Many2one('res.users', string='Account', default=lambda self: self.env.user)
    group_avatar = fields.Binary('Avatar')
    group_name = fields.Char(string="Name", required=True)
    group_id = fields.Char(string="Group ID", required=True)
    access_token = fields.Char(string="Access Token")
    category = fields.Char(string="Main Category")
    category_ids = fields.Many2many('facebook.category', string='Categories',
                                    relation='facebook_group_category_rel',
                                    column1='group_id', column2='category_id')

    is_favorite = fields.Boolean(string="Favorite", default=False, tracking=True)
    display_name = fields.Char(compute='_compute_display_name')

    post_content = fields.Text(string="Post Content")
    comment_content = fields.Text(string="Comment Content")

    # New fields for manual input
    group_description = fields.Text(string="Group Description")
    member_count = fields.Integer(string="Member Count")
    is_public = fields.Boolean(string="Is Public Group", default=True)

    @api.depends('group_name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.group_name

    def toggle_favorite(self):
        for record in self:
            record.is_favorite = not record.is_favorite

    def post_to_group(self):
        for record in self:
            if record.access_token and record.group_id and record.post_content:
                url = f"https://graph.facebook.com/{record.group_id}/feed"
                payload = {
                    'message': record.post_content,
                    'access_token': record.access_token
                }
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    record.message_post(body="Post successful!")
                else:
                    record.message_post(body="Failed to post!")

    def comment_on_post(self, post_id):
        for record in self:
            if record.access_token and post_id and record.comment_content:
                url = f"https://graph.facebook.com/{post_id}/comments"
                payload = {
                    'message': record.comment_content,
                    'access_token': record.access_token
                }
                response = requests.post(url, data=payload)
                if response.status_code == 200:
                    record.message_post(body="Comment successful!")
                else:
                    record.message_post(body="Failed to comment!")

    # New method for manual group creation
    @api.model
    def create_group_manually(self, vals):
        return self.create(vals)

    # New method to update group information
    def update_group_info(self, vals):
        self.write(vals)