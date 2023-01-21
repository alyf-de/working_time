// Copyright (c) 2023, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Working Time", {});

frappe.ui.form.on("Working Time Log", {
    time_logs_add: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.from_time = frappe.datetime.now_time(false);
        row.to_time = ""; // Otherwise Frappe may overwrite empty values with the current time on save.
        frm.refresh_field("time_logs");
    },
});
