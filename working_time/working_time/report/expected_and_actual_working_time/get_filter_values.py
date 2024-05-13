import frappe

@frappe.whitelist()
def get_employee_working_hours(user): # use weekly hours field in employee to calculate daily working time
    employee = frappe.get_value("Employee", {"user_id": user}, "name")
    if employee:
        working_hours_per_week = frappe.get_value("Employee", employee, "working_hours_per_week")
        if working_hours_per_week:
            working_hours_per_day = working_hours_per_week / 5
            return working_hours_per_day
    return None

@frappe.whitelist()
def get_employee_name(user):
    employee = frappe.get_value("Employee", {"user_id": user}, "name")
    if employee:
        return employee
    return None
