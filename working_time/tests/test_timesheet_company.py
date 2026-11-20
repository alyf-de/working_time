# Copyright (c) 2026, ALYF GmbH and Contributors
"""Generated **Timesheet**s must not fall back to the user's default company."""

import frappe
from erpnext import get_default_company
from frappe.tests import IntegrationTestCase

COMPANY = "_Test Company 1"
DATE = "2026-05-15"


class IntegrationTestTimesheetCompany(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.project = (
			frappe.get_doc(
				{"doctype": "Project", "project_name": "_Test Timesheet Company", "company": COMPANY}
			)
			.insert()
			.name
		)

	def setUp(self):
		super().setUp()
		self.assertNotEqual(get_default_company(), COMPANY)

	def get_timesheet_company(self, filters: dict) -> str:
		return frappe.get_last_doc("Timesheet", filters=filters).company

	def test_working_time_timesheet_uses_employee_company(self):
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Working Time Company Test",
				"gender": "Female",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
				"company": COMPANY,
				"status": "Active",
			}
		).insert()
		working_time = frappe.get_doc({"doctype": "Working Time", "employee": employee.name, "date": DATE})
		working_time.insert()

		working_time.insert_timesheet(
			project=self.project,
			customer=None,
			task=None,
			billing_rate=0,
			hours=1,
			billing_hours=0,
			description="Test",
			jira_issue_url=None,
			internal_notes=[],
		)

		self.assertEqual(self.get_timesheet_company({"working_time": working_time.name}), COMPANY)

	def test_freelancer_time_timesheet_uses_project_company(self):
		freelancer_time = frappe.get_doc(
			{
				"doctype": "Freelancer Time",
				"from_date": DATE,
				"to_date": DATE,
				"time_logs": [
					{"date": DATE, "project": self.project, "duration": 3600, "note": "+invoice note"},
				],
			}
		).insert()

		freelancer_time.create_timesheets()

		self.assertEqual(self.get_timesheet_company({"freelancer_time": freelancer_time.name}), COMPANY)
