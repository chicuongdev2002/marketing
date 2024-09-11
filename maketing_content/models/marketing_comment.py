from odoo import models, fields

class MarketingComment(models.Model):
    _name = 'marketing.comment'
    _description = 'Marketing Comment'

    name = fields.Char(string='Comment', required=True)