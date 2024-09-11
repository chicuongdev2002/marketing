{
    # Tên module
    'name': 'Facebook Marketing',
    'version': '1.0',
  
    # Loại module
    # 'category': 'Tutorial',
    'category': 'Social',


    # Độ ưu tiên module trong list module
    # Số càng nhỏ, độ ưu tiên càng cao
    #### Chấp nhận số âm
    'sequence': 5,

    # Mô tả module
    'summary': 'Integrate Facebook with Odoo',
    'description': '',
    'images':["static/description/icon.png"],


    # Module dựa trên các category nào
    # Khi hoạt động, category trong 'depends' phải được install
    ### rồi module này mới đc install
    # 'depends': [],
    # 'external_dependencies': {
    #     'python': ['facebook_business'],
    # },
    'depends': ['base', 'bus', 'web','website_blog','website_sale','maketing_content'],
    # Module có được phép install hay không
    # Nếu bạn thắc mắc nếu tắt thì làm sao để install
    # Bạn có thể dùng 'auto_install'
    'installable': True,
    'auto_install': False,
    'application': True,

    # Import các file cấu hình
    # Những file ảnh hưởng trực tiếp đến giao diện (không phải file để chỉnh sửa giao diện)
    ## hoặc hệ thống (file group, phân quyền)
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/manager_account_view.xml',
        'views/fb_page_view.xml',
        'views/fb_marketing_comment_view.xml',
        'views/fb_marketing_content_view.xml',
        # 'views/manager_post_view.xml',
         'views/fb_group_view.xml',
        'views/fb_marketing_post_view.xml',
        'views/res_config_settings_views.xml',
        'views/ir_cron_data.xml',
        'views/menu.xml',
        # 'views/facebook_marketplace_views.xml',
        # 'views/product_template_view.xml',
    ],

    # Import các file cấu hình (chỉ gọi từ folder 'static')
    # Những file liên quan đến
    ## + các class mà hệ thống sử dụng
    ## + các chỉnh sửa giao diện
    ## + t
    'assets': {
        'web.assets_backend': [
            'facebook_marketing/static/src/js/*.js',
            'facebook_marketing/static/src/xml/*.xml',
        ],
    },
    'license': 'LGPL-3',
}