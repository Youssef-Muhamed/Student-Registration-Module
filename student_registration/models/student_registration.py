from odoo import models, fields,api,_
import datetime
from odoo.exceptions import ValidationError

class StudentRegistration(models.Model):
    _name = 'student.registration'
    _description = 'Student Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: self.env['ir.sequence'].next_by_code('student.registration') or _('New'))
    student_id = fields.Many2one('res.partner', string='Student', domain=[('is_student', '=', True)], required=True,
                                 default=lambda self: self.env['res.partner'].search([('is_student', '=', True)],
                                                                                     limit=1))
    phone = fields.Char(string='Phone', related='student_id.phone', readonly=True)
    birth_date = fields.Date(string='Birth Date', related='student_id.birth_date', readonly=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    date = fields.Date(string='Registration Date', required=True, default=fields.Date.today())
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(string='Registration Fees', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('canceled', 'Canceled')
    ], string='Status', default='draft')
    product_id = fields.Many2one('product.product', string='Product')

    # registration_invoice_id = fields.Many2one('account.invoice', string='Registration Invoice', readonly=True)
    invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True, copy=False)

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                record.age = datetime.datetime.now().year - record.birth_date.year
            else:
                record.age = 0


    # @api.onchange('student_id')
    # def _onchange_student_id(self):
    #     if self.student_id and not self.student_id.is_student:
    #         self.student_id = False
    #         return {
    #             'warning': {
    #                 'title': _('Warning'),
    #                 'message': _('Selected partner is not a student. Please select a student.')
    #             }
    #         }

    @api.model
    def create(self, vals):
        vals['student_id'] = self.env['res.partner'].browse(vals.get('student_id')).with_context(
            {'default_is_student': True}).id
        return super(StudentRegistration, self).create(vals)

    def confirm_registration(self):
        self.write({'state': 'confirmed'})

    def cancel_registration(self):
        self.write({'state': 'canceled'})

    # def create_registration_invoice(self):
    #     invoice = self.env['account.invoice'].create({
    #         'partner_id': self.student_id.id,
    #         'currency_id': self.currency_id.id,
    #         'invoice_date': self.date,
    #         'type': 'out_invoice',
    #         'invoice_line_ids': [(0, 0, {
    #             'name': 'Registration Fees',
    #             'price_unit': self.amount,
    #             'quantity': 1,
    #             'account_id': self.env['ir.config_parameter'].sudo().get_param('registration.reg_fees_account_id'),
    #         })]
    #     })
    #     self.write({'registration_invoice_id': invoice.id, 'state': 'invoiced'})
    #     return {
    #         'name': _('Registration Invoice'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.invoice',
    #         'res_id': invoice.id,
    #         'view_mode': 'form',
    #         'context': {'default_type': 'out_invoice'},
    #         'target': 'current',
    #     }
    #

    # @api.multi
    # def create_invoice(self):
    #     # self.env['ir.model.data'].create({
    #     #     'name': 'my_module.registration_product',
    #     #     'module': 'my_module',
    #     #     'model': 'product.product',
    #     #     'res_id': product_id.id,
    #     # })
    #     # product = self.env.ref('my_module.registration_product')
    #
    #     # Create invoice data
    #     invoice_data = {
    #         'partner_id': self.student_id.id,
    #         'currency_id': self.currency_id.id,
    #         'invoice_line_ids': [(0, 0, {
    #             'name': 'Registration Fees',
    #             'price_unit': self.amount,
    #             'quantity': 1,
    #             'product_id': self.product_id.id,
    #         })],
    #         'registration_id': self.id,
    #     }
    #
    #     # Create invoice
    #     invoice = self.env['account.move'].create(invoice_data)
    #
    #     # Link invoice to registration
    #     self.invoice_id = invoice.id
    #
    #     # Change registration state to invoiced
    #     self.state = 'invoiced'

    # @api.multi
    def create_invoice(self):
        # Get the account for registration fees
        account_id = self.env['ir.config_parameter'].sudo().get_param('registration.reg_fees_account_id')

        # Create the invoice line
        invoice_line = self.env['account.move.line'].new({
            'name': 'Registration Fees',
            'price_unit': self.amount,
            'quantity': 1,
            'product_id': self.product_id.id,
            'account_id': account_id,
        })

        # Create the invoice
        invoice = self.env['account.move'].create({
            'partner_id': self.student_id.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, invoice_line._convert_to_write(invoice_line._cache))],
            'registration_id': self.id,
        })

        # Link the invoice to the registration
        self.invoice_id = invoice.id

        # Change the registration state to invoiced
        self.state = 'invoiced'

    @api.model_create_multi
    def open_invoice(self):
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
        }
