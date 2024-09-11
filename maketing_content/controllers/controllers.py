from odoo import http

class FacebookLiveController(http.Controller):

    @http.route('/call_facebook_api', type='json', auth='user')
    def call_facebook_api(self, **kw):
        return http.request.env['facebook-live.facebook-live'].call_facebook_api()