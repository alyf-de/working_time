# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.model.document import Document
from working_time.jira_client import JiraClient

HALF_DAY = 3.25
OVERTIME_FACTOR = 1.15
MAX_HALF_DAY = HALF_DAY * OVERTIME_FACTOR * 60 * 60
FIVE_MINUTES = 5 * 60
ONE_HOUR = 60 * 60


class WorkingTime(Document):
    def before_validate(self):
        last_idx = len(self.time_logs) - 1
        self.break_time = self.working_time = 0
        for idx, log in enumerate(self.time_logs):
            log.to_time = self.time_logs[idx + 1].from_time if idx < last_idx else log.to_time
            log.cleanup_and_set_duration()
            self.break_time += (log.duration or 0) if log.is_break else 0
            self.working_time += 0 if log.is_break else (log.duration or 0)

    def validate(self):
        for log in self.time_logs:
            if log.duration and log.duration < 0:
                frappe.throw(_("Please fix negative duration in row {0}").format(log.idx))

            if log.project and not log.key and not log.note:
                frappe.throw(_("Please add issue key or note in row {0}").format(log.idx))

    def on_submit(self):
        self.create_attendance()
        self.create_timesheets()

    def create_attendance(self):
        if not frappe.db.exists(
            "Attendance", {"employee": self.employee, "attendance_date": self.date}
        ):
            attendance = frappe.get_doc(
                {
                    "doctype": "Attendance",
                    "employee": self.employee,
                    "status": "Present"
                    if self.working_time > MAX_HALF_DAY
                    else "Half Day",
                    "attendance_date": self.date,
                    "working_time": self.name,
                }
            )
            attendance.flags.ignore_permissions = True
            attendance.save()
            attendance.submit()

    def create_timesheets(self):
        for log in self.time_logs:
            if log.duration and log.project:
                costing_rate = get_costing_rate(self.employee)
                hours = math.ceil(log.duration / FIVE_MINUTES) * FIVE_MINUTES / ONE_HOUR
                billing_hours = (
                    math.ceil(
                        log.duration * float(log.billable[:-1]) / 100 / FIVE_MINUTES
                    )
                    * FIVE_MINUTES
                    / ONE_HOUR
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
                                "from_time": self.date,
                                "billing_hours": billing_hours,
                                "description": get_description(
                                    jira_site, log.key, log.note
                                ),
                                "jira_issue_url": get_jira_issue_url(
                                    jira_site, log.key
                                ),
                            }
                        ],
                        "parent_project": log.project,
                        "customer": customer,
                        "employee": self.employee,
                        "working_time": self.name,
                    }
                ).insert()


def get_costing_rate(employee):
    return frappe.get_value(
        "Activity Cost",
        {"activity_type": "Default", "employee": employee},
        "costing_rate",
    )


def get_jira_issue_url(jira_site, key):
    return f"https://{jira_site}/browse/{key}" if key else None


def get_description(jira_site, key, note):
    if key:
        description = f"{JiraClient(jira_site).get_issue_summary(key)} ({key})"

        if note:
            description += f":\n\n{note}"
    else:
        description = note or "-"

    return description
