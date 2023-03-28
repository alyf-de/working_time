from frappe import get_hooks
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = get_hooks("working_time_custom_fields")
	create_custom_fields({
		"Timesheet": custom_fields.get("Timesheet", []),
		"Attendance": custom_fields.get("Attendance", []),
	})
