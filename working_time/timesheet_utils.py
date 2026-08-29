# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe

from working_time.jira_utils import get_jira_issue_summary


def get_task_description(task: str) -> str:
	subject = frappe.db.get_value("Task", task, "subject")

	return f"{subject} ({task})" if subject else task


def get_description(*, task=None, jira_site=None, key=None, note=None):
	if task:
		description = get_task_description(task)
	elif key and jira_site:
		description = get_jira_issue_summary(jira_site, key)
	elif key:
		description = key
	else:
		description = note or "-"

	if (task or key) and note:
		description += f":\n\n{note}"

	return description.strip()
