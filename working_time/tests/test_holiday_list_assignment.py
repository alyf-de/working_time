# Copyright (c) 2026, ALYF GmbH and Contributors
"""HRMS v16 assigns holiday lists through **Holiday List Assignment**, not `Employee.holiday_list`."""

from datetime import date
from unittest.mock import patch

import frappe
from frappe import _dict
from frappe.tests import IntegrationTestCase, freeze_time

from working_time.reminders import send_month_end_reminders
from working_time.working_time.report.expected_and_actual_working_time.expected_and_actual_working_time import (
	get_data,
)

COMPANY = "_Test Company"
EMPLOYEE_EMAIL = "wt.holiday.assignment@example.com"
HOLIDAY = date(2026, 7, 31)  # Friday, last day of the month
DAY_BEFORE_HOLIDAY = date(2026, 7, 30)


class IntegrationTestHolidayListAssignment(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		holiday_list = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": "_Test Working Time Assigned Holidays",
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
				"holidays": [{"holiday_date": HOLIDAY, "description": "Test Holiday"}],
			}
		).insert()

		cls.employee = (
			frappe.get_doc(
				{
					"doctype": "Employee",
					"first_name": "Working Time Holiday Test",
					"gender": "Female",
					"date_of_birth": "1990-01-01",
					"date_of_joining": "2020-01-01",
					"company": COMPANY,
					"company_email": EMPLOYEE_EMAIL,
					"prefered_contact_email": "Company Email",
					"status": "Active",
				}
			)
			.insert()
			.name
		)

		frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Employee",
				"assigned_to": cls.employee,
				"holiday_list": holiday_list.name,
				"from_date": "2026-01-01",
			}
		).submit()

	def test_holiday_block_uses_assigned_holiday_list(self):
		working_time = frappe.get_doc({"doctype": "Working Time", "employee": self.employee, "date": HOLIDAY})
		policy = _dict(consider_holiday_list=1)

		self.assertRaises(frappe.ValidationError, working_time.validate_holiday_block, policy)

	def test_report_marks_assigned_holidays(self):
		rows = list(get_data(self.employee, DAY_BEFORE_HOLIDAY, HOLIDAY, 8, "working_time"))
		is_holiday_by_date = {row[0]: row[3] for row in rows}

		self.assertEqual(is_holiday_by_date, {DAY_BEFORE_HOLIDAY: 0, HOLIDAY: 1})

	def test_month_end_reminder_skips_assigned_holidays(self):
		with freeze_time("2026-07-30 12:00", is_utc=True), patch("frappe.sendmail") as sendmail:
			send_month_end_reminders()

		recipients = [call.kwargs["recipients"] for call in sendmail.call_args_list]
		self.assertIn(EMPLOYEE_EMAIL, recipients)
