import frappe


@frappe.whitelist()
def get_employee_working_hours(user): # use weekly hours field in employee to calculate daily working time
	employee = frappe.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		return None
	working_hours_per_week = frappe.get_value("Employee", employee, "working_hours_per_week")
	if working_hours_per_week:
		return working_hours_per_week / 5


@frappe.whitelist()
def get_employee_name(user):
	return frappe.get_value("Employee", {"user_id": user}, "name")
