from odoo import fields, models,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_token = fields.Char(string="Facebook API Token", config_parameter='facebook.api_token')

    @api.model

    def set_values(self):
         super(ResConfigSettings, self).set_values()
         self.env['ir.config_parameter'].sudo().set_param('facebook.api_token', self.api_token)
