# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Student Registration',
    'summary': 'Manage Student Registration',
    'version': '1.0',
    'depends': ['base','crm','account',],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/inherit_partner_view.xml',
        'views/student_registration_view.xml',
        'views/inherit_invoice_view.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
    'sequence': 1,
    # 'license': 'LGPL-3',
}
