from odoo import models, fields

class MarketingContentImage(models.Model):
    _name = 'marketing.content.image'
    _description = 'Marketing Content Image'

    content_id = fields.Many2one('marketing.content', string='Marketing Content', required=True, ondelete='cascade')
    image = fields.Binary(string='Image')
    datas = fields.Binary(string='Data')

