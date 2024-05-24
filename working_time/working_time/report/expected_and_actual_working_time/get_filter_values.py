import frappe


@frappe.whitelist()
def get_employee_working_hours(employee: str):
	"""Return the average daily working time calculated from the employee's weekly hours."""
	if not isinstance(employee, str):
		raise ValueError("Employee should be a string")

	frappe.has_permission("Employee", throw=True)
	if not employee:
		return None
	working_hours_per_week = frappe.get_value("Employee", employee, "working_hours_per_week")
	if working_hours_per_week:
		return working_hours_per_week / 5


@frappe.whitelist()
def get_employee_name():
	return frappe.get_value("Employee", {"user_id": frappe.session.user}, "name")
