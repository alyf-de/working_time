import frappe


def execute():
    doc_names = frappe.get_all("Working Time", pluck="name")

    for doc_name in doc_names:
        date, break_time, working_time = frappe.db.get_value(
            "Working Time", doc_name, ["from_date", "break_duration", "total_duration"]
        )
        frappe.db.set_value(
            "Working Time",
            doc_name,
            {"date": date, "break_time": break_time, "working_time": working_time},
            update_modified=False,
        )
