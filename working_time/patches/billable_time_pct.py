import frappe


def execute():
	for wt_name in frappe.get_all(
		"Working Time",
		filters={"docstatus": 1},
		pluck="name"
	):
		wt = frappe.get_doc("Working Time", wt_name)
		wt.before_validate()
		wt.db_set(
			{
				"project_time": wt.project_time,
				"project_pct": wt.project_pct,
				"billable_time": wt.billable_time,
				"billable_pct": wt.billable_pct
			},
			update_modified=False
		)
