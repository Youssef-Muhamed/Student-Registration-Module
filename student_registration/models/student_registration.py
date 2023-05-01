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

    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                record.age = datetime.datetime.now().year - record.birth_date.year
            else:
                record.age = 0

    @api.model
    def create(self, vals):
        vals['student_id'] = self.env['res.partner'].browse(vals.get('student_id')).with_context(
            {'default_is_student': True}).id
        return super(StudentRegistration, self).create(vals)

    def confirm_registration(self):
        self.write({'state': 'confirmed'})

    def cancel_registration(self):
        self.write({'state': 'canceled'})

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def create_invoice(self):
        invoice_obj = self.env['account.move']
        invoice_vals = {
            'partner_id': self.student_id.id,
            'invoice_date': fields.Date.today(),
            'registration_id': self.id,
            'currency_id': self.currency_id.id,
            # 'type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'name': 'Registration Fees',
                'quantity': 1,
                'price_unit': self.amount,
                'account_id': self.student_id.property_account_receivable_id.id,
            })],
        }
        invoice = invoice_obj.create(invoice_vals)
        self.invoice_id = invoice.id
        self.state = 'invoiced'
        return {
            'name': _('Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_open_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('partner_id', '=', self.student_id.id)],
            'target': 'current'
        }