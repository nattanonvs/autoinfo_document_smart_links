{
    "name": "AutoInfo Document Smart Links",
    "version": "15.0.1.2.3",
    "summary": "Smart buttons เชื่อม Sale Order / Delivery / Accounting และรวม Credit Notes + Debit Notes",
    "author": "AutoInfo, The Auto-Info Co., Ltd.",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": ["sale_stock", "purchase", "purchase_stock", "account"],
    "data": [
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
