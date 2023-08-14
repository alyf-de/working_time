# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import math

import frappe
from frappe.model.document import Document
from working_time.working_time.doctype.working_time.working_time import (
	FIVE_MINUTES,
	ONE_HOUR,
	get_description,
	get_jira_issue_url,
)
from working_time.jira_utils import get_description, get_jira_issue_url


class FreelancerTime(Document):
	def on_submit(self):
		self.create_timesheets()

	def create_timesheets(self):
		for log in self.time_logs:
			if log.duration and log.project:
				costing_rate = get_rate_and_currency(self.owner, log.date)
				billing_hours = hours = (
					math.ceil(log.duration / FIVE_MINUTES) * FIVE_MINUTES / ONE_HOUR
				)

				customer, billing_rate, jira_site = frappe.get_value(
					"Project",
					log.project,
					["customer", "billing_rate", "jira_site"],
				)

				frappe.get_doc(
					{
						"doctype": "Timesheet",
						"time_logs": [
							{
								"is_billable": 1,
								"project": log.project,
								"activity_type": "Default",
								"base_billing_rate": billing_rate,
								"base_costing_rate": costing_rate,
								"costing_rate": costing_rate,
								"billing_rate": billing_rate,
								"hours": hours,
								"from_time": log.date,
								"billing_hours": billing_hours,
								"description": get_description(
									jira_site, log.issue_key, log.note
								),
								"jira_issue_url": get_jira_issue_url(
									jira_site, log.issue_key
								),
							}
						],
						"parent_project": log.project,
						"customer": customer,
						"freelancer_time": self.name,
					}
				).insert()


def get_rate_and_currency(user, date) -> float:
	"""Get the rate for a freelancer at a given date."""
	return frappe.get_value(
		"Freelancer Rate",
		{"user": user, "from_date": ("<=", date)},
		"rate",
		order_by="from_date DESC"
	)
