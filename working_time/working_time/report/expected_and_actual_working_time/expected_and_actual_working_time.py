# Copyright (c) 2024, ALYF GmbH and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from babel.dates import format_date
from frappe import _
from frappe.utils.data import getdate


def execute(filters):
	employee = filters.get("employee")
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	daily_working_hours = filters.get("daily_working_hours")

	# check permissions
	employee_doc = frappe.get_doc("Employee", employee)
	frappe.has_permission("Employee", "read", employee_doc, throw=True)
	frappe.has_permission("Working Time", "read", throw=True)

	return get_columns(), list(
		get_data(employee, from_date, to_date, daily_working_hours)
	)


def get_columns():
	return [
		{"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
		{
			"fieldname": "weekday",
			"label": _("Weekday"),
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"fieldname": "on_leave",
			"label": _("On Leave"),
			"fieldtype": "Check",
			"width": 100,
		},
		{
			"fieldname": "is_holiday",
			"label": _("Is Holiday"),
			"fieldtype": "Check",
			"width": 100,
		},
		{
			"fieldname": "expected_working_time",
			"label": _("Expected Working Time"),
			"fieldtype": "Duration",
			"width": 200,
			"hide_days": 1,
			"hide_seconds": 1,
		},
		{
			"fieldname": "actual_working_time",
			"label": _("Actual Working Time"),
			"fieldtype": "Duration",
			"width": 200,
			"hide_days": 1,
			"hide_seconds": 1,
		},
		{
			"fieldname": "difference",
			"label": _("Difference"),
			"fieldtype": "Duration",
			"width": 100,
			"hide_days": 1,
			"hide_seconds": 1,
		},
		{
			"fieldname": "not_plausible",
			"label": _("Not Plausible"),
			"fieldtype": "Check",
			"width": 150,
		},
	]


def daterange(start_date, end_date):
	for n in range(int((end_date - start_date).days) + 1):
		yield start_date + timedelta(n)


def get_data(employee, from_date, to_date, daily_working_hours):
	holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
	for current_date in daterange(from_date, to_date):
		actual_working_time = (
			frappe.db.get_value(
				"Working Time",
				{"employee": employee, "date": current_date, "docstatus": 1},
				"working_time",
			)
			or 0
		)
		weekday = format_date(current_date, format="EEE", locale=frappe.local.lang)
		on_leave = int(
			bool(
				frappe.db.exists(
					"Attendance",
					{
						"employee": employee,
						"attendance_date": current_date,
						"status": "On Leave",
						"docstatus": 1,
					},
				)
			)
		)
		is_holiday = int(
			bool(
				frappe.db.exists(
					"Holiday", {"parent": holiday_list, "holiday_date": current_date}
				)
			)
		)

		if current_date.isoweekday() in (6, 7) or on_leave or is_holiday:
			expected_working_time = 0
		else:
			expected_working_time = daily_working_hours * 60 * 60

		yield (
			current_date,
			weekday,
			on_leave,
			is_holiday,
			expected_working_time,
			actual_working_time,
			actual_working_time - expected_working_time,
			int(not on_leave and not is_holiday and not actual_working_time),
		)
