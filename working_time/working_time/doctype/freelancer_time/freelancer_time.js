// Copyright (c) 2023, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Freelancer Time Log", {
	task: function (frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (child.task && child.issue_key) {
			frappe.model.set_value(cdt, cdn, "issue_key", "");
		}
	},
	issue_key: function (frm, cdt, cdn) {
		const child = locals[cdt][cdn];
		if (child.issue_key && child.task) {
			frappe.model.set_value(cdt, cdn, "task", "");
		}
	},
});
