# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.model.docstatus import DocStatus
from frappe.model.document import Document
from frappe.utils.data import date_diff

from working_time.jira_utils import get_description, get_jira_issue_url
from working_time.working_time.doctype.working_time.working_time import (
	FIVE_MINUTES,
	ONE_HOUR,
	has_external_note,
	parse_note,
	task_not_in_project,
)


class FreelancerTime(Document):
	def before_validate(self):
		self.total_duration = sum(log.duration for log in self.time_logs if log.duration)

	def validate(self):
		self.validate_from_to_dates("from_date", "to_date")

		for log in self.time_logs:
			if date_diff(self.to_date, log.date) < 0:
				frappe.throw(_("The date in row {0} is after the end date.").format(log.idx))

			if date_diff(log.date, self.from_date) < 0:
				frappe.throw(_("The date in row {0} is before the start date.").format(log.idx))

			if not log.task and not log.issue_key and not has_external_note(log.note):
				frappe.throw(
					_("Please add a task, Jira key, or external note to billable row {0}").format(log.idx)
				)

			if task_not_in_project(log.task, log.project):
				frappe.throw(
					_("The task in row {0} does not belong to project {1}.").format(
						log.idx, frappe.bold(log.project)
					)
				)

	def on_submit(self):
		self.create_timesheets()

	def on_cancel(self):
		self.delete_draft_timesheets()

	def create_timesheets(self):
		for log in self.time_logs:
			if log.duration and log.project:
				costing_rate = get_rate_and_currency(self.owner, log.date)
				billing_hours = hours = math.ceil(log.duration / FIVE_MINUTES) * FIVE_MINUTES / ONE_HOUR

				customer, billing_rate, jira_site = frappe.get_value(
					"Project",
					log.project,
					["customer", "billing_rate", "jira_site"],
				)
				customer_note, internal_note = parse_note(log.note)

				frappe.get_doc(
					{
						"doctype": "Timesheet",
						"time_logs": [
							{
								"is_billable": 1,
								"project": log.project,
								"task": log.task,
								"activity_type": "Default",
								"base_billing_rate": billing_rate,
								"base_costing_rate": costing_rate,
								"costing_rate": costing_rate,
								"billing_rate": billing_rate,
								"hours": hours,
								"from_time": log.date,
								"billing_hours": billing_hours,
								"description": get_description(jira_site, log.issue_key, customer_note),
								"jira_issue_url": get_jira_issue_url(jira_site, log.issue_key),
							}
						],
						"note": internal_note,
						"parent_project": log.project,
						"customer": customer,
						"freelancer_time": self.name,
					}
				).insert()

	def delete_draft_timesheets(self):
		for timesheet in frappe.get_list(
			"Timesheet", filters={"freelancer_time": self.name, "docstatus": DocStatus.draft()}
		):
			frappe.delete_doc("Timesheet", timesheet.name)


def get_rate_and_currency(user, date) -> float:
	"""Get the rate for a freelancer at a given date."""
	return frappe.get_value(
		"Freelancer Rate",
		{"user": user, "from_date": ("<=", date)},
		"rate",
		order_by="from_date DESC",
	)
