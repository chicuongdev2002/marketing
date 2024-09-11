from odoo import models, fields, api

class MarketingContent(models.Model):
    _name = 'marketing.content'
    _description = 'Marketing Content'

    post_ids = fields.One2many('marketing.post', 'content_id', string='Posts')
    content = fields.Text(string='Content')
    include_link = fields.Boolean('Include Link', default=False)
    @api.depends('post_ids')
    def _compute_has_posts(self):
        for record in self:
            record.has_posts = bool(record.post_ids)
            
    def action_add_image(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Image',
            'view_mode': 'form',
            'res_model': 'marketing.content.image',
            'target': 'new',
            'context': {
                'default_content_id': self.id,
            }
        }