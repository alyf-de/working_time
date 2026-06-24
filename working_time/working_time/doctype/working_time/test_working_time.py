# Copyright (c) 2023, ALYF GmbH and Contributors
# See license.txt

import unittest
from unittest.mock import MagicMock, patch

import frappe
from frappe import _dict

from working_time.working_time.doctype.working_time.working_time import (
	_get_configured_activity_types,
	aggregate_time_logs,
	get_activity_cost_rates,
	get_costing_rate,
	get_log_activity_type,
	resolve_billing_rate,
)
from working_time.working_time.doctype.working_time_log.working_time_log import (
	DEFAULT_ACTIVITY_TYPE,
	WorkingTimeLog,
)


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
		project_a = result[("Project A", None, "KEY-1", "Default")]
		self.assertEqual(project_a["hours"], 3.0)
		self.assertEqual(
			project_a["internal_notes"], ["Internal Note 1", "Internal Note 2", "Internal Note 1"]
		)
		self.assertEqual(project_a["customer_notes"], [])

		# Check Project B
		project_b = result[("Project B", "Task B", "KEY-2", "Default")]
		self.assertEqual(project_b["hours"], 2.0)
		self.assertEqual(project_b["internal_notes"], [])
		self.assertEqual(project_b["customer_notes"], ["Customer Note 1"])

	def test_aggregate_time_logs_by_activity_type(self):
		logs = [
			_dict(
				project="Project A",
				key="KEY-1",
				duration=3600,
				billable="100%",
				activity_type="Default",
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=1800,
				billable="100%",
				activity_type="Support",
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=1800,
				billable="100%",
				activity_type="Support",
			),
		]

		result = aggregate_time_logs(logs)

		self.assertEqual(result[("Project A", None, "KEY-1", "Default")]["hours"], 1.0)
		self.assertEqual(result[("Project A", None, "KEY-1", "Support")]["hours"], 1.0)

	def test_get_log_activity_type_defaults_to_default(self):
		self.assertEqual(
			get_log_activity_type(_dict(project="Project A", activity_type=None)),
			DEFAULT_ACTIVITY_TYPE,
		)
		self.assertEqual(
			get_log_activity_type(_dict(project="Project A", activity_type="Support")),
			"Support",
		)
		with self.assertRaises(ValueError):
			get_log_activity_type(_dict(project=None, activity_type=None))

	def test_aggregate_time_logs_without_activity_type_uses_default(self):
		logs = [
			_dict(
				project="Project A",
				key="KEY-1",
				duration=3600,
				billable="100%",
			),
		]

		result = aggregate_time_logs(logs)

		self.assertIn(("Project A", None, "KEY-1", DEFAULT_ACTIVITY_TYPE), result)

	def test_working_time_log_validate_sets_default_activity_type(self):
		log = WorkingTimeLog.__new__(WorkingTimeLog)
		log.project = "Project A"
		log.activity_type = None
		WorkingTimeLog.validate(log)
		self.assertEqual(log.activity_type, DEFAULT_ACTIVITY_TYPE)

	def test_parallel_logs_create_separate_timesheets_by_activity_type(self):
		working_time = self.get_working_time(
			[
				{
					"from_time": "09:00:00",
					"to_time": "11:00:00",
					"project": "Project A",
					"key": "KEY-1",
					"billable": "100%",
					"activity_type": "Default",
				},
				{
					"from_time": "11:00:00",
					"to_time": "12:00:00",
					"project": "Project A",
					"key": "KEY-1",
					"billable": "100%",
					"activity_type": "Support",
				},
			]
		)
		working_time.before_validate()

		project_details = _dict(
			customer="Customer",
			billing_rate=100,
			billing_rate_per_day=0,
			jira_site=None,
		)
		with (
			patch.object(working_time, "insert_timesheet") as insert_timesheet,
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_project_details",
				return_value=project_details,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_description",
				return_value="KEY-1",
			),
		):
			working_time.create_timesheets()

		self.assertEqual(insert_timesheet.call_count, 2)
		activity_types = {call.kwargs["activity_type"] for call in insert_timesheet.call_args_list}
		self.assertEqual(activity_types, {"Default", "Support"})
		for call in insert_timesheet.call_args_list:
			self.assertEqual(call.kwargs["project"], "Project A")
			self.assertEqual(call.kwargs["task"], None)

	def test_whole_day_timesheet_rejects_mixed_activity_types(self):
		whole_day_project = "Whole Day Project"
		working_time = self.get_working_time(
			[
				{
					"from_time": "09:00:00",
					"to_time": "12:00:00",
					"project": whole_day_project,
					"key": "KEY-1",
					"billable": "100%",
					"activity_type": "Default",
				},
				{
					"from_time": "12:00:00",
					"to_time": "17:00:00",
					"project": whole_day_project,
					"key": "KEY-2",
					"billable": "100%",
					"activity_type": "Support",
				},
			]
		)
		working_time.whole_day_project = whole_day_project
		working_time.before_validate()

		project_details = _dict(
			customer="Customer",
			billing_rate=100,
			billing_rate_per_day=800,
			jira_site=None,
		)
		with (
			patch.object(working_time, "insert_timesheet") as insert_timesheet,
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_project_details",
				return_value=project_details,
			),
		):
			self.assertRaises(
				frappe.ValidationError,
				working_time.create_whole_day_timesheet,
				working_time.time_logs,
			)
			insert_timesheet.assert_not_called()

	def test_get_activity_cost_rates_prefers_project_specific(self):
		project_rates = _dict(billing_rate=120, costing_rate=60)
		calls = []

		def get_value(doctype, filters, fields, as_dict=False):
			calls.append(filters)
			if filters.get("project") == "Project A":
				return project_rates
			return None

		with patch(
			"working_time.working_time.doctype.working_time.working_time.frappe.db.get_value",
			side_effect=get_value,
		):
			result = get_activity_cost_rates("EMP-1", "Support", "Project A")

		self.assertEqual(result, project_rates)
		self.assertEqual(calls[0]["project"], "Project A")
		self.assertEqual(len(calls), 1)

	def test_get_activity_cost_rates_falls_back_without_project(self):
		default_rates = _dict(billing_rate=80, costing_rate=40)
		calls = []

		def get_value(doctype, filters, fields, as_dict=False):
			calls.append(filters)
			if filters.get("project") == "Project A":
				return None
			if filters.get("project") == ("is", "not set"):
				return default_rates
			return None

		with patch(
			"working_time.working_time.doctype.working_time.working_time.frappe.db.get_value",
			side_effect=get_value,
		):
			result = get_activity_cost_rates("EMP-1", "Support", "Project A")

		self.assertEqual(result, default_rates)
		self.assertEqual(calls[0]["project"], "Project A")
		self.assertEqual(calls[1]["project"], ("is", "not set"))

	def test_get_costing_rate_uses_project_specific_activity_cost(self):
		with patch(
			"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
			return_value=_dict(billing_rate=0, costing_rate=60),
		):
			self.assertEqual(get_costing_rate("EMP-1", "Support", project="Project A"), 60)

	def test_resolve_billing_rate_uses_project_specific_activity_cost(self):
		with patch(
			"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
			return_value=_dict(billing_rate=120, costing_rate=0),
		):
			self.assertEqual(
				resolve_billing_rate("EMP-1", "Support", 100, project="Project A"),
				120,
			)

	def test_get_configured_activity_types_without_project(self):
		costs = [
			_dict(activity_type="Default", project="PROJ-0009"),
			_dict(activity_type="Forschung", project=None),
			_dict(activity_type="Default", project=None),
		]
		with patch(
			"working_time.working_time.doctype.working_time.working_time.frappe.get_all",
			return_value=costs,
		):
			self.assertEqual(_get_configured_activity_types("EMP-1"), ["Default", "Forschung"])

	def test_get_configured_activity_types_with_project(self):
		costs = [
			_dict(activity_type="Default", project="PROJ-0009"),
			_dict(activity_type="Default", project=None),
			_dict(activity_type="Forschung", project=None),
			_dict(activity_type="Ausführung", project="PROJ-OTHER"),
		]
		with patch(
			"working_time.working_time.doctype.working_time.working_time.frappe.get_all",
			return_value=costs,
		):
			self.assertEqual(
				_get_configured_activity_types("EMP-1", "PROJ-0009"),
				["Default", "Forschung"],
			)

	def test_get_configured_activity_types_without_employee(self):
		self.assertEqual(_get_configured_activity_types(None), [])

	def test_resolve_billing_rate_priority(self):
		activity_cost = _dict(billing_rate=150, costing_rate=0)
		activity_type = _dict(billing_rate=50, costing_rate=0)

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=activity_cost,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=activity_type,
			),
		):
			self.assertEqual(resolve_billing_rate("EMP-1", "Support", 100), 150)

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=None,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=activity_type,
			),
		):
			self.assertEqual(resolve_billing_rate("EMP-1", "Support", 100), 100)

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=_dict(billing_rate=0, costing_rate=0),
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=activity_type,
			),
		):
			self.assertEqual(resolve_billing_rate("EMP-1", "Support", 0), 50)

	def test_get_costing_rate_priority(self):
		activity_cost = _dict(billing_rate=0, costing_rate=45)
		activity_type = _dict(billing_rate=0, costing_rate=20)

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=activity_cost,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=activity_type,
			),
		):
			self.assertEqual(get_costing_rate("EMP-1", "Support"), 45)

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=None,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=activity_type,
			),
		):
			self.assertEqual(get_costing_rate("EMP-1", "Support"), 20)

	def test_resolve_billing_rate_falls_back_to_zero(self):
		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=None,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=None,
			),
		):
			self.assertEqual(resolve_billing_rate("EMP-1", "Support", 0), 0)

	def test_get_costing_rate_falls_back_to_zero(self):
		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=None,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=None,
			),
		):
			self.assertEqual(get_costing_rate("EMP-1", "Support"), 0)

	def test_insert_timesheet_sets_billing_and_costing_rates(self):
		working_time = self.get_working_time([])
		working_time.employee = "EMP-1"
		captured = {}

		def capture_get_doc(doc_dict):
			captured.update(doc_dict)
			doc = MagicMock()
			doc.insert = MagicMock()
			return doc

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_costing_rate",
				return_value=45,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.frappe.get_doc",
				side_effect=capture_get_doc,
			),
		):
			working_time.insert_timesheet(
				project="Project A",
				customer="Customer",
				task=None,
				activity_type="Support",
				billing_rate=150,
				hours=2,
				billing_hours=2,
				description="Support work",
				jira_issue_url=None,
				internal_notes=["internal"],
			)

		time_log = captured["time_logs"][0]
		self.assertEqual(time_log["billing_rate"], 150)
		self.assertEqual(time_log["base_billing_rate"], 150)
		self.assertEqual(time_log["costing_rate"], 45)
		self.assertEqual(time_log["base_costing_rate"], 45)

	def test_insert_timesheet_resolves_activity_rates_end_to_end(self):
		working_time = self.get_working_time([])
		working_time.employee = "EMP-1"
		captured = {}

		def capture_get_doc(doc_dict):
			captured.update(doc_dict)
			doc = MagicMock()
			doc.insert = MagicMock()
			return doc

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=_dict(billing_rate=150, costing_rate=45),
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=_dict(billing_rate=50, costing_rate=20),
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.frappe.get_doc",
				side_effect=capture_get_doc,
			),
		):
			working_time.insert_timesheet(
				project="Project A",
				customer="Customer",
				task=None,
				activity_type="Support",
				billing_rate=resolve_billing_rate("EMP-1", "Support", 100),
				hours=2,
				billing_hours=2,
				description="Support work",
				jira_issue_url=None,
				internal_notes=[],
			)

		time_log = captured["time_logs"][0]
		self.assertEqual(time_log["billing_rate"], 150)
		self.assertEqual(time_log["costing_rate"], 45)

	def test_insert_timesheet_falls_back_to_zero_rates(self):
		working_time = self.get_working_time([])
		working_time.employee = "EMP-1"
		captured = {}

		def capture_get_doc(doc_dict):
			captured.update(doc_dict)
			doc = MagicMock()
			doc.insert = MagicMock()
			return doc

		with (
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_cost_rates",
				return_value=None,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.get_activity_type_rates",
				return_value=None,
			),
			patch(
				"working_time.working_time.doctype.working_time.working_time.frappe.get_doc",
				side_effect=capture_get_doc,
			),
		):
			working_time.insert_timesheet(
				project="Project A",
				customer="Customer",
				task=None,
				activity_type="Support",
				billing_rate=resolve_billing_rate("EMP-1", "Support", 0),
				hours=2,
				billing_hours=2,
				description="Support work",
				jira_issue_url=None,
				internal_notes=[],
			)

		time_log = captured["time_logs"][0]
		self.assertEqual(time_log["billing_rate"], 0)
		self.assertEqual(time_log["costing_rate"], 0)

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
