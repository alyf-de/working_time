# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe

COLUMNS = [
    {
		"fieldname": "employee",
		"label": "Employee",
		"fieldtype": "Link",
		"options": "Employee",
	},
	{
		"fieldname": "total_working_time",
		"label": "Total Working Time",
		"fieldtype": "Duration",
		"hide_days": 1,
		"hide_seconds": 1,
	},
	{
		"fieldname": "total_project_time",
		"label": "Total Project Time",
		"fieldtype": "Duration",
		"hide_days": 1,
		"hide_seconds": 1,
	},
	{
		"fieldname": "total_break_time",
		"label": "Total Break Time",
		"fieldtype": "Duration",
		"hide_days": 1,
		"hide_seconds": 1,
	},
]


def execute(filters=None):
	data = frappe.get_all(
		"Working Time",
		fields=[
			"employee",
			"SUM(working_time) as total_working_time",
			"SUM(project_time) as total_project_time",
			"SUM(break_time) as total_break_time",
		],
		filters=[
			["docstatus", "=", 1],
			["date", ">=", filters.get("from_date")],
			["date", "<=", filters.get("to_date")],
		],
		group_by="employee",
	)
	return COLUMNS, data
