from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fb_catalog_product_id = fields.Char(string='Facebook Catalog Product ID')
    is_on_fb_marketplace = fields.Boolean(string='Is on Facebook Marketplace')
    product_brand_id = fields.Many2one('product.brand', string='Brand')  # Thêm trường này
    def action_post_to_facebook_catalog(self):
        integration = self.env['facebook.catalog.integration'].search([], limit=1)
        if not integration:
            raise UserError('Facebook Catalog Integration is not configured')
        
        for product in self:
            if product.fb_catalog_product_id:
                integration.update_product_on_catalog(product)
            else:
                fb_product_id = integration.post_product_to_catalog(product)
                if fb_product_id:
                    product.fb_catalog_product_id = fb_product_id

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if any(field in vals for field in ['name', 'description_sale', 'list_price', 'qty_available']):
            self.action_post_to_facebook_catalog()
        return res