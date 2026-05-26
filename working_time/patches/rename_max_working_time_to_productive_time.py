from frappe.model.utils.rename_field import rename_field


def execute():
	rename_field(
		"Working Time Policy",
		"max_working_time_per_day",
		"max_productive_time_per_day",
	)
