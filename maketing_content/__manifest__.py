{
    # Tên module
    'name': 'Marketing content',
    'version': '1.0',

    # Loại module
    'category': 'Social',

    # Độ ưu tiên module trong list module
    # Số càng nhỏ, độ ưu tiên càng cao
    #### Chấp nhận số âm
    'sequence': 5,

    # Mô tả module
    'summary': 'Create Content Maketing',
    'description': '',


    # Module dựa trên các category nào
    # Khi hoạt động, category trong 'depends' phải được install
    ### rồi module này mới đc install
    'depends': ['base', 'bus', 'web','website_blog','website_sale'],

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
        'views/marketing_content_views.xml',
        'views/maketing_content_image.xml',
        'views/manager_post_view.xml',
        'views/marketing_product_views.xml',
        'views/marketing_content_blog.xml',
        'views/marketing_content_comment_views.xml',
        'views/menu.xml',
        
    ],

    # Import các file cấu hình (chỉ gọi từ folder 'static')
    # Những file liên quan đến
    ## + các class mà hệ thống sử dụng
    ## + các chỉnh sửa giao diện
    ## + t
    'assets': {
            
    },
    'license': 'LGPL-3',
}
