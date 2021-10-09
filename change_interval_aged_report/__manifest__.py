# -*- coding: utf-8 -*-
{
    'name': 'Change Date Interval Aged Receivable & Payable Report',
    'category': 'Accounting', 
    'author': 'Apra IT Solutions', 
    'version': '1.0',
    'description': """
        Use this module if want to change date interval on aged receivable & payable report
    """, 
    'depends': ['base','account','account_reports'],
    'data': [ 
       'security/ir.model.access.csv',
       'views/assets.xml',
       'wizard/tmp_aged_views.xml',

    ],   
    'qweb': [ 
                # "static/src/xml/account_reconciliation.xml",
    ],
}