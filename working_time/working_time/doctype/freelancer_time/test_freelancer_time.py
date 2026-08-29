# Copyright (c) 2023, ALYF GmbH and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestFreelancerTime(FrappeTestCase):
	def get_freelancer_time(self, time_logs):
		return frappe.get_doc(
			{
				"doctype": "Freelancer Time",
				"from_date": "2026-05-01",
				"to_date": "2026-05-31",
				"time_logs": time_logs,
			}
		)

	def test_log_requires_task_jira_key_or_external_note(self):
		freelancer_time = self.get_freelancer_time(
			[
				{
					"date": "2026-05-15",
					"project": "Project A",
					"duration": 3600,
				},
			]
		)
		self.assertRaises(frappe.ValidationError, freelancer_time.validate)

		freelancer_time.time_logs[0].note = "internal note"
		self.assertRaises(frappe.ValidationError, freelancer_time.validate)

		freelancer_time.time_logs[0].note = "+ab"
		self.assertRaises(frappe.ValidationError, freelancer_time.validate)

		freelancer_time.time_logs[0].note = "+invoice note"
		freelancer_time.validate()

		freelancer_time.time_logs[0].note = None
		freelancer_time.time_logs[0].issue_key = "KEY-1"
		freelancer_time.validate()

		freelancer_time.time_logs[0].issue_key = None
		freelancer_time.time_logs[0].task = "TASK-1"
		freelancer_time.validate()
