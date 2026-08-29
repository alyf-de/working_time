# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe

from working_time.jira_client import JiraClient


def get_description(*, task=None, jira_site=None, key=None, note=None):
	if task:
		description = frappe.db.get_value("Task", task, "subject") or task
	elif key and jira_site:
		description = f"{JiraClient(jira_site).get_issue_summary(key)} ({key})"
	elif key:
		description = key
	else:
		description = note or "-"

	if (task or key) and note:
		description += f":\n\n{note}"

	return description.strip()
