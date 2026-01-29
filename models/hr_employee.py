from odoo import models, api, fields

class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    evaluation_ids = fields.One2many('emp.evaluation', 'employee_id', string='Evaluations')
    
    emp_eval_type = fields.Selection([
        ('supervisor', 'Supervisor'),
        ('standard', 'Standard Employee'),
    ], string="Employee Type", default='standard', tracking=True)

class HREmployee(models.Model):
    _inherit = 'hr.employee'

class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
