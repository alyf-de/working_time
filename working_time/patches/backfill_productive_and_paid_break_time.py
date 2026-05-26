import frappe


def execute():
	wt = frappe.qb.DocType("Working Time")
	frappe.qb.update(wt).set(wt.productive_time, wt.working_time).set(wt.paid_break_time, 0).run()
