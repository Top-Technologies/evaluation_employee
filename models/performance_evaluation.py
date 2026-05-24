from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError
import logging
from . import ethiopian_calendar

_logger = logging.getLogger(__name__)


class EmpEvaluationBase(models.AbstractModel):
    _name = 'emp.evaluation.base'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Base Employee Evaluation'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        tracking=True,
    )

    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        related='employee_id.department_id',
        store=True,
        readonly=True
    )

    job_id = fields.Many2one(
        'hr.job',
        string="Job Position",
        related='employee_id.job_id',
        store=True,
        readonly=True
    )

    manager_id = fields.Many2one(
        'hr.employee',
        string="Manager",
        related='employee_id.parent_id',
        store=True,
        readonly=True
    )

    coach_id = fields.Many2one(
        'hr.employee',
        string='Coach',
        compute='_compute_coach',
        store=True,
        readonly=True
    )

    start_date = fields.Date(string="Period Start", default=fields.Date.today)
    end_date = fields.Date(string="Period End", default=fields.Date.today)
    evaluation_date = fields.Date(string='Evaluation Date')

    employee_comment = fields.Text(string="Employee’s Remarks")
    manager_comment = fields.Text(string="Manager’s Feedback")

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('reviewed_by_coach', 'Reviewed by Coach'),
            ('waiting_hr_approval', 'Waiting HR Approval'),
            ('done', 'Done')
        ],
        string='Status',
        default='draft',
        tracking=True
    )

    total_score = fields.Float(string="Total Score", compute="_compute_total_score", store=True)
    is_self = fields.Boolean(compute='_compute_is_self')
    allowed_employee_ids = fields.Many2many(
        'hr.employee',
        compute='_compute_allowed_employee_ids',
        string="Allowed Employees"
    )

    @api.depends('employee_id', 'employee_id.coach_id')
    def _compute_coach(self):
        for rec in self:
            rec.coach_id = rec.employee_id.coach_id if rec.employee_id else False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.department_id = rec.employee_id.department_id
                rec.job_id = rec.employee_id.job_id
            else:
                rec.department_id = False
                rec.job_id = False

    @api.depends_context('uid')
    @api.depends('employee_id')
    def _compute_is_self(self):
        current_user_id = self.env.user.id
        for rec in self:
            rec.is_self = (rec.employee_id.user_id.id == current_user_id)

    def _validate_evaluation_submission(self):
        today = fields.Date.today()
        for rec in self:
            if rec.end_date and rec.end_date > today:
                raise ValidationError("Cannot process evaluations for an expired period.")
            if rec.employee_id and rec.start_date and rec.end_date:
                domain = [
                    ('id', '!=', rec.id),
                    ('employee_id', '=', rec.employee_id.id),
                    ('start_date', '<=', rec.end_date),
                    ('end_date', '>=', rec.start_date),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError("An evaluation already exists for this employee within the specified period.")

    def action_submit_to_employee(self):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError("Transition is only allowed from Draft.")
        if not self.env.user.has_group('evaluation_employee.group_evaluation_coach'):
            raise AccessError("Only Coaches can submit evaluations for review.")
        
        current_user = self.env.user
        if (self.employee_id.coach_id.user_id != current_user and
                self.employee_id.parent_id.user_id != current_user and
                not current_user.has_group('evaluation_employee.group_evaluation_hr')):
            raise AccessError("You can only evaluate employees you are coaching or managing.")
        
        self._validate_evaluation_submission()
        self.state = 'reviewed_by_coach'
        
        try:
            self.message_post(
                body=f"Evaluation submitted for review by {self.env.user.name}.",
                partner_ids=[self.employee_id.user_id.partner_id.id] if self.employee_id.user_id else [],
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send evaluation notification to employee: %s", str(e))
        return True

    def action_submit_feedback(self):
        self.ensure_one()
        if self.state != 'reviewed_by_coach':
            raise ValidationError("Transition is only allowed from Reviewed by Coach.")
        if not self.is_self:
            raise AccessError("Only the evaluated employee can submit their feedback.")
        if not self.employee_comment:
            raise ValidationError("Please provide your remarks before submitting.")
        
        self._validate_evaluation_submission()
        self.state = 'waiting_hr_approval'
        
        try:
            hr_group = self.env.ref('evaluation_employee.group_evaluation_hr')
            hr_partners = hr_group.users.mapped('partner_id').ids
            self.message_post(
                body=f"Employee {self.employee_id.name} has submitted feedback. Waiting for HR approval.",
                partner_ids=hr_partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send evaluation notification to HR: %s", str(e))
        return True

    def action_confirm(self):
        self.ensure_one()
        if self.state not in ('draft', 'reviewed_by_coach', 'waiting_hr_approval'):
            raise ValidationError("Transition is only allowed from Draft, Reviewed by Coach, or Waiting HR Approval.")
        if not self.env.user.has_group('evaluation_employee.group_evaluation_hr'):
            raise AccessError("Only HR Managers can approve evaluations.")
        
        self._validate_evaluation_submission()
        self.state = 'done'
        self.evaluation_date = fields.Date.today()
        
        try:
            partners = []
            if self.coach_id.user_id:
                partners.append(self.coach_id.user_id.partner_id.id)
            if self.employee_id.user_id:
                partners.append(self.employee_id.user_id.partner_id.id)
                
            self.message_post(
                body="Evaluation Approved and Finalized by HR.",
                partner_ids=partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send approved evaluation notification: %s", str(e))
        return True

    def get_ethiopian_date_str(self, date_value):
        return ethiopian_calendar.format_ethiopian_date(date_value)


class EmpEvaluation(models.Model):
    _name = 'emp.evaluation'
    _inherit = 'emp.evaluation.base'
    _description = '3 Month Employee Evaluation'

    rating_selection = [('5', '5)'), ('4', '4)'), ('3', '3)'), ('2', '2)'), ('1', '1)'), ('NA', 'NA)')]
    
    # 3 Month criteria questions
    for i in range(1, 26):
        locals()[f'q{i}'] = fields.Selection(rating_selection, string=f"Q{i}")

    eval_employee_type = fields.Selection(
        related='employee_id.emp_eval_type',
        selection=[
            ('supervisor', 'Supervisor'),
            ('standard', 'Employee'),
        ],
        string='Employee Type',
        store=True,
        readonly=True
    )

    @api.depends('eval_employee_type', *[f'q{i}' for i in range(1, 26)])
    def _compute_total_score(self):
        for rec in self:
            total = 0
            if rec.eval_employee_type == 'standard':
                for i in range(1, 11):
                    val = getattr(rec, f'q{i}')
                    if val and val.isdigit():
                        total += int(val)
            elif rec.eval_employee_type == 'supervisor':
                for i in range(11, 26):
                    val = getattr(rec, f'q{i}')
                    if val and val.isdigit():
                        total += int(val)
            rec.total_score = total

    @api.depends_context('uid')
    def _compute_allowed_employee_ids(self):
        user = self.env.user
        subordinates = self.env['hr.employee'].search([
            '|',
            ('coach_id.user_id', '=', user.id),
            ('parent_id.user_id', '=', user.id)
        ])
        for rec in self:
            rec.allowed_employee_ids = subordinates

    def action_preview(self):
        return self.env.ref('evaluation_employee.action_report_emp_evaluation').report_action(self)

    @api.model
    def cron_notify_missing_evaluations(self):
        """Notify coaches about missing evaluations in active periods."""
        current_year_start = fields.Date.today().replace(month=1, day=1)
        current_year_end = fields.Date.today().replace(month=12, day=31)
        
        employees = self.env['hr.employee'].search([('coach_id', '!=', False)])
        for emp in employees:
            evaluation_exists = self.search_count([
                ('employee_id', '=', emp.id),
                ('start_date', '>=', current_year_start),
                ('start_date', '<=', current_year_end)
            ])
            if not evaluation_exists:
                pass
        return True


class EmpEvaluationSixty(models.Model):
    _name = 'emp.evaluation.sixty'
    _inherit = 'emp.evaluation.base'
    _description = '60 Days Employee Evaluation'

    rating_selection = [('5', '5)'), ('4', '4)'), ('3', '3)'), ('2', '2)'), ('1', '1)'), ('NA', 'NA)')]
    
    for i in range(1, 11):
        locals()[f'q{i}'] = fields.Selection(rating_selection, string=f"Q{i}")

    @api.depends(*[f'q{i}' for i in range(1, 11)])
    def _compute_total_score(self):
        for rec in self:
            total = 0
            for i in range(1, 11):
                val = getattr(rec, f'q{i}')
                if val and val.isdigit():
                    total += int(val)
            rec.total_score = total

    @api.depends_context('uid')
    def _compute_allowed_employee_ids(self):
        user = self.env.user
        subordinates = self.env['hr.employee'].search([
            '|',
            ('coach_id.user_id', '=', user.id),
            ('parent_id.user_id', '=', user.id)
        ])
        for rec in self:
            rec.allowed_employee_ids = subordinates

    def action_preview(self):
        return self.env.ref('evaluation_employee.action_report_emp_evaluation_sixty').report_action(self)


class EmpEvaluationNinety(models.Model):
    _name = 'emp.evaluation.ninety'
    _inherit = 'emp.evaluation.base'
    _description = '90 Days Employee Evaluation'

    rating_selection = [('5', '5)'), ('4', '4)'), ('3', '3)'), ('2', '2)'), ('1', '1)'), ('NA', 'NA)')]
    
    for i in range(1, 11):
        locals()[f'q{i}'] = fields.Selection(rating_selection, string=f"Q{i}")

    @api.depends(*[f'q{i}' for i in range(1, 11)])
    def _compute_total_score(self):
        for rec in self:
            total = 0
            for i in range(1, 11):
                val = getattr(rec, f'q{i}')
                if val and val.isdigit():
                    total += int(val)
            rec.total_score = total

    @api.depends_context('uid')
    def _compute_allowed_employee_ids(self):
        user = self.env.user
        subordinates = self.env['hr.employee'].search([
            '|',
            ('coach_id.user_id', '=', user.id),
            ('parent_id.user_id', '=', user.id)
        ])
        for rec in self:
            rec.allowed_employee_ids = subordinates

    def action_preview(self):
        return self.env.ref('evaluation_employee.action_report_emp_evaluation_ninety').report_action(self)


class EmpEvaluationHR(models.Model):
    _name = 'emp.evaluation.hr'
    _inherit = 'emp.evaluation.base'
    _description = 'HR Employee Evaluation'

    rating_selection = [('5', '5)'), ('4', '4)'), ('3', '3)'), ('2', '2)'), ('1', '1)'), ('NA', 'NA)')]
    
    for i in range(1, 11):
        locals()[f'q{i}'] = fields.Selection(rating_selection, string=f"Q{i}")

    @api.depends(*[f'q{i}' for i in range(1, 11)])
    def _compute_total_score(self):
        for rec in self:
            total = 0
            for i in range(1, 11):
                val = getattr(rec, f'q{i}')
                if val and val.isdigit():
                    total += int(val)
            rec.total_score = total

    @api.depends_context('uid')
    def _compute_allowed_employee_ids(self):
        user = self.env.user
        if user.has_group('evaluation_employee.group_evaluation_hr'):
            all_employees = self.env['hr.employee'].search([])
            for rec in self:
                rec.allowed_employee_ids = all_employees
        else:
            subordinates = self.env['hr.employee'].search([
                '|',
                ('coach_id.user_id', '=', user.id),
                ('parent_id.user_id', '=', user.id)
            ])
            for rec in self:
                rec.allowed_employee_ids = subordinates

    def action_preview(self):
        return self.env.ref('evaluation_employee.action_report_emp_evaluation_hr').report_action(self)
