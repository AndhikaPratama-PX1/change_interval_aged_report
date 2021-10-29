# -*- coding: utf-8 -*-
{
    'name': 'Customize Change Date Interval Aged Receivable & Payable Report',
    'category': 'Accounting', 
    'author': 'Apra IT Solutions', 
    'version': '1.1',
    'license': 'LGPL-3',
    'summary': """
        Use this module if want to change date interval on aged receivable & payable report (Aged Interval).
    """, 
    'depends': ['account','account_reports'],
    'data': [ 
       'security/ir.model.access.csv',
       'views/assets.xml',
       'wizard/tmp_aged_views.xml',

    ],   
    'images': [
        'static/description/change_interval_aged_report.png',
    ],

    'maintainer': 'Apra IT Solutions',
    'price': 10,
    'currency': 'USD',
}
