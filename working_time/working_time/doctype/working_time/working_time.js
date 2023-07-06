// Copyright (c) 2023, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Working Time", {
    setup: function (frm) {
        frm.set_query("employee", "erpnext.controllers.queries.employee_query");
    },
    refresh: function (frm) {
        if (frm.doc.docstatus === 0) {
            // Linked documents will get created on submit.
            // Hide the dashboard if the document is not yet submitted.
            frm.dashboard.hide();
        }
    },
});

frappe.ui.form.on("Working Time Log", {
    time_logs_add: function (frm, cdt, cdn) {
        let prev_to_time;
        if (frm.doc.time_logs.length > 1) {
            prev_to_time = frm.doc.time_logs.at(-2).to_time;
        }
        frappe.model.set_value(cdt, cdn, "from_time", prev_to_time || frappe.datetime.now_time(false));
        frappe.model.set_value(cdt, cdn, "to_time", "");  // Otherwise Frappe may overwrite empty values with the current time on save.
    },
});
