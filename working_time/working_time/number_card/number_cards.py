import frappe
from frappe.utils.caching import redis_cache
from frappe.utils.data import flt, get_first_day, getdate

from working_time.working_time.report.expected_and_actual_working_time.expected_and_actual_working_time import (
	get_data,
)


@redis_cache(ttl=60 * 60 * 8, user=True)
def get_chart_data(employee: str, from_date: str, to_date: str, fieldname: str):
	data = list(get_data(employee, from_date, to_date, 0, fieldname))
	total_seconds = sum(item[5] for item in data)
	working_days = sum(not item[2] and not item[3] for item in data)
	return total_seconds / (working_days or 1)


def get_chart(fieldname: str):
	to_date = getdate()
	from_date = get_first_day(to_date)
	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})

	return {
		"value": flt(get_chart_data(employee, from_date, to_date, fieldname) / 60 / 60, 2),
		"fieldtype": "Float",
		"route_options": {
			"from_date": from_date,
			"to_date": to_date,
			"employee": employee,
		},
		"route": ["query-report", "Expected and Actual Working Time"],
	}


@frappe.whitelist()
def working_time():
	return get_chart("working_time")


@frappe.whitelist()
def break_time():
	return get_chart("break_time")


@frappe.whitelist()
def billable_time():
	return get_chart("billable_time")


@frappe.whitelist()
def project_time():
	return get_chart("project_time")
