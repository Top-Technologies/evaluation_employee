from odoo import models, api, fields

class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    evaluation_ids = fields.One2many('emp.evaluation', 'employee_id', string='Evaluations')
    
    emp_eval_type = fields.Selection([
        ('supervisor', 'Supervisor/manager'),
        ('standard', 'Employee'),
    ], string="Employee Type", default='standard', tracking=True, required=True,)

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def action_update_evaluation_groups(self):
        # Assign evaluation groups based on username matching keywords
        employee_group = self.env.ref('evaluation_employee.group_evaluation_employee', raise_if_not_found=False)
        coach_group = self.env.ref('evaluation_employee.group_evaluation_coach', raise_if_not_found=False)
        hr_group = self.env.ref('evaluation_employee.group_evaluation_hr', raise_if_not_found=False)

        for employee in self:
            user = employee.user_id
            if not user or user.login in ('admin', 'root'):
                continue

            login = (user.login or '').lower()
            if 'coach' in login and coach_group and coach_group not in user.groups_id:
                user.groups_id |= coach_group
            elif 'hr' in login and hr_group and hr_group not in user.groups_id:
                user.groups_id |= hr_group
            elif employee_group and employee_group not in user.groups_id:
                user.groups_id |= employee_group
        return True

class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
