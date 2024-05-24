// Copyright (c) 2024, ALYF GmbH and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Expected and Actual Working Time"] = {
	filters: [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			reqd: 1,
			on_change: function(report){
				frappe.call({
					method: "working_time.working_time.report.expected_and_actual_working_time.get_filter_values.get_employee_working_hours",
					args: {
						"employee": report.get_filter_value("employee")
					},
					callback: (r) => {
						if (r.message) {
							var filter = report.get_filter("daily_working_hours");
							filter.set_value(r.message);
						}
					}
				});
			}
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.nowdate(),
		},
		{
			fieldname: "daily_working_hours",
			label: __("Daily Working Hours"),
			fieldtype: "Float",
			reqd: 1,
		},
	],
	// fetch filter values for employee and daily_working_hours using db call and python script
	onload: function(report) {
		frappe.call({
			method: "working_time.working_time.report.expected_and_actual_working_time.get_filter_values.get_employee_name",
			callback: function(r) {
				if (r.message) {
					var filter = report.get_filter("employee");
					filter.set_value(r.message);
				}
			}
		});
	}
};
