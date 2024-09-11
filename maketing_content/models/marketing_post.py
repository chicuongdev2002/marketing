from odoo import models, fields, api

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    content_id = fields.Many2one('marketing.content', string='Content', required=True)
    title = fields.Char(string='Title')
    body = fields.Text(string='Body')
    date_posted = fields.Datetime(string='Date Posted', default=fields.Datetime.now)
    is_active = fields.Boolean(string='Active', default=True)

    @api.depends('content_id')
    def _compute_content_title(self):
        for record in self:
            record.content_title = record.content_id.content if record.content_id else 'No Content'

    content_title = fields.Char(string='Content Title', compute='_compute_content_title', store=True)

    def action_view_content(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Content',
            'view_mode': 'form',
            'res_model': 'marketing.content',
            'res_id': self.content_id.id,
            'target': 'current',
        }
