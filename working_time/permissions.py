import frappe


def check_working_time_read():
	frappe.has_permission("Working Time", "read", throw=True)


def check_employee_read(employee: str):
	if not employee:
		return

	frappe.has_permission("Employee", "read", frappe.get_doc("Employee", employee), throw=True)


def check_project_read(project: str | None):
	if not project:
		return

	frappe.has_permission("Project", "read", frappe.get_doc("Project", project), throw=True)


def check_activity_cost_read():
	frappe.has_permission("Activity Cost", "read", throw=True)


def check_activity_type_access(employee: str, project: str | None = None):
	check_working_time_read()
	check_employee_read(employee)
	check_activity_cost_read()
	check_project_read(project)
