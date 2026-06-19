# Copyright (c) 2023, ALYF GmbH and Contributors
# See license.txt

import unittest

import frappe
from frappe import _dict

from working_time.working_time.doctype.working_time.working_time import aggregate_time_logs


class TestWorkingTime(unittest.TestCase):
	def get_working_time(self, time_logs):
		return frappe.get_doc(
			{
				"doctype": "Working Time",
				"employee": "Test Employee",
				"date": "2026-05-26",
				"time_logs": time_logs,
			}
		)

	def test_aggregate_time_logs(self):
		logs = [
			_dict(
				project="Project A",
				key="KEY-1",
				duration=3600,
				billable="100%",
				note="Internal Note 1",
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=1800,
				billable="100%",
				note="Internal Note 2",
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=1800,
				billable="100%",
				note="Internal Note 2",  # Duplicate, should be ignored
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=3600,
				billable="100%",
				note="Internal Note 1",  # Not consecutive, should be added
			),
			_dict(
				project="Project B",
				key="KEY-2",
				task="Task B",
				duration=3600,
				billable="100%",
				note="+Customer Note 1",
			),
			_dict(
				project="Project B",
				key="KEY-2",
				task="Task B",
				duration=3600,
				billable="100%",
				note="+Customer Note 1",  # Duplicate, should be ignored
			),
		]

		result = aggregate_time_logs(logs)

		# Check Project A
		project_a = result[("Project A", None, "KEY-1")]
		self.assertEqual(project_a["hours"], 3.0)
		self.assertEqual(
			project_a["internal_notes"], ["Internal Note 1", "Internal Note 2", "Internal Note 1"]
		)
		self.assertEqual(project_a["customer_notes"], [])

		# Check Project B
		project_b = result[("Project B", "Task B", "KEY-2")]
		self.assertEqual(project_b["hours"], 2.0)
		self.assertEqual(project_b["internal_notes"], [])
		self.assertEqual(project_b["customer_notes"], ["Customer Note 1"])

	def test_paid_break_totals(self):
		working_time = self.get_working_time(
			[
				{"from_time": "09:00:00", "to_time": "12:00:00", "is_break": 0},
				{
					"from_time": "12:00:00",
					"to_time": "12:30:00",
					"is_break": 1,
					"is_paid_break": 1,
				},
				{"from_time": "12:30:00", "to_time": "13:00:00", "is_break": 1},
				{"from_time": "13:00:00", "to_time": "17:00:00", "is_break": 0},
			]
		)

		working_time.before_validate()

		self.assertEqual(working_time.productive_time, 7 * 60 * 60)
		self.assertEqual(working_time.paid_break_time, 30 * 60)
		self.assertEqual(working_time.break_time, 60 * 60)
		self.assertEqual(working_time.working_time, 7.5 * 60 * 60)

	def test_whole_day_project_billable_time(self):
		working_time = self.get_working_time(
			[
				{
					"from_time": "09:00:00",
					"to_time": "12:00:00",
					"project": "Whole Day Project",
					"billable": "100%",
				},
				{
					"from_time": "13:00:00",
					"to_time": "15:00:00",
					"project": "Other Project",
					"billable": "50%",
				},
			]
		)
		working_time.whole_day_project = "Whole Day Project"
		working_time.before_validate()

		self.assertEqual(working_time.project_time, 5 * 60 * 60)
		self.assertEqual(working_time.billable_time, (8 * 60 * 60) + (2 * 60 * 60 * 0.5))
		self.assertEqual(working_time.billable_pct, 180)

	def test_non_break_clears_paid_break_flag(self):
		working_time = self.get_working_time(
			[
				{
					"from_time": "09:00:00",
					"to_time": "10:00:00",
					"is_break": 0,
					"is_paid_break": 1,
				}
			]
		)

		working_time.before_validate()

		self.assertEqual(working_time.time_logs[0].is_paid_break, 0)
		self.assertEqual(working_time.productive_time, 60 * 60)
		self.assertEqual(working_time.paid_break_time, 0)

	def test_max_working_time_policy_uses_productive_time(self):
		policy = _dict({"max_productive_time_per_day": 8 * 60 * 60})
		working_time = self.get_working_time(
			[
				{"from_time": "09:00:00", "to_time": "17:00:00", "is_break": 0},
				{
					"from_time": "17:00:00",
					"to_time": "18:00:00",
					"is_break": 1,
					"is_paid_break": 1,
				},
			]
		)
		working_time.before_validate()

		self.assertEqual(working_time.productive_time, 8 * 60 * 60)
		self.assertEqual(working_time.working_time, 9 * 60 * 60)
		working_time.validate_max_working_time(policy)

		over_limit = self.get_working_time(
			[
				{"from_time": "09:00:00", "to_time": "17:15:00", "is_break": 0},
			]
		)
		over_limit.before_validate()

		self.assertRaises(frappe.ValidationError, over_limit.validate_max_working_time, policy)

	def test_mandatory_breaks_policy_uses_productive_time(self):
		policy = _dict(
			{"mandatory_breaks": [_dict({"work_threshold": 6 * 60 * 60, "required_break_minutes": 30 * 60})]}
		)
		working_time = self.get_working_time(
			[
				{"from_time": "09:00:00", "to_time": "14:45:00", "is_break": 0},
				{
					"from_time": "14:45:00",
					"to_time": "15:05:00",
					"is_break": 1,
					"is_paid_break": 1,
				},
			]
		)
		working_time.before_validate()

		self.assertEqual(working_time.productive_time, 5.75 * 60 * 60)
		self.assertEqual(working_time.working_time, (5.75 * 60 * 60) + (20 * 60))
		working_time.validate_mandatory_breaks(policy)

		missing_break = self.get_working_time(
			[
				{"from_time": "09:00:00", "to_time": "15:00:00", "is_break": 0},
				{
					"from_time": "15:00:00",
					"to_time": "15:20:00",
					"is_break": 1,
					"is_paid_break": 1,
				},
			]
		)
		missing_break.before_validate()

		self.assertRaises(frappe.ValidationError, missing_break.validate_mandatory_breaks, policy)
