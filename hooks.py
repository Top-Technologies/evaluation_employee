# hooks.py
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def assign_user_groups(cr, registry):
    _logger.info("🔥 assign_user_groups hook STARTED 🔥")

    env = api.Environment(cr, SUPERUSER_ID, {})

    employee_group = env.ref(
        'evaluation_employee.group_evaluation_employee',
        raise_if_not_found=False
    )
    coach_group = env.ref(
        'evaluation_employee.group_evaluation_coach',
        raise_if_not_found=False
    )
    hr_group = env.ref(
        'evaluation_employee.group_evaluation_hr',
        raise_if_not_found=False
    )

    users = env['res.users'].search([])

    for user in users:
        if user.login in ('admin', 'root'):
            _logger.info("Skipping system user: %s", user.login)
            continue

        login = (user.login or '').lower()

        # Coach
        if 'coach' in login and coach_group and coach_group not in user.groups_id:
            user.groups_id |= coach_group
            _logger.info("Assigned Coach group to user: %s", user.login)

        # HR
        elif 'hr' in login and hr_group and hr_group not in user.groups_id:
            user.groups_id |= hr_group
            _logger.info("Assigned HR group to user: %s", user.login)

        # Default Employee
        elif employee_group and employee_group not in user.groups_id:
            user.groups_id |= employee_group
            _logger.info("Assigned Employee group to user: %s", user.login)

        else:
            _logger.info("No group change for user: %s", user.login)
