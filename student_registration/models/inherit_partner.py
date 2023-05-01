from odoo import models, fields

class InheritPartner(models.Model):
    _inherit = 'res.partner'

    is_student = fields.Boolean(string='Is Student')
    birth_date = fields.Date(string='Birth Date', required=True)

    _sql_constraints = [('birth_date_past_check', 'CHECK (birth_date < CURRENT_DATE)', 'Birth Date must be in the past.')]
