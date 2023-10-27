# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _
from frappe.model.docstatus import DocStatus
from frappe.model.document import Document

from working_time.jira_utils import get_description, get_jira_issue_url

HALF_DAY = 3.25
OVERTIME_FACTOR = 1.15
MAX_HALF_DAY = HALF_DAY * OVERTIME_FACTOR * 60 * 60
FIVE_MINUTES = 5 * 60
ONE_HOUR = 60 * 60


class WorkingTime(Document):
    def before_validate(self):
        self.break_time = self.working_time = self.project_time = self.billable_time = 0
        self.project_pct = self.billable_pct = 0

        last_idx = len(self.time_logs) - 1
        for idx, log in enumerate(self.time_logs):
            log.to_time = self.time_logs[idx + 1].from_time if idx < last_idx else log.to_time
            log.cleanup_and_set_duration()
            log.duration = log.duration or 0
            self.break_time += log.duration if log.is_break else 0
            self.working_time += 0 if log.is_break else log.duration
            if log.project and not log.is_break:
                self.project_time += log.duration
                self.billable_time += get_billable_duration(log)

        if self.working_time:
            self.project_pct = round(self.project_time / self.working_time * 100, 0)
            self.billable_pct = round(self.billable_time / self.working_time * 100, 0)

    def validate(self):
        for log in self.time_logs:
            if log.duration and log.duration < 0:
                frappe.throw(_("Please fix negative duration in row {0}").format(log.idx))

            if (
                log.billable != "0%" and
                log.project and
                not log.key and
                (not log.note or not log.note.strip().startswith("+"))
            ):
                frappe.throw(_("Please add an issue key or invoice note to the billable row {0}").format(log.idx))

    def on_submit(self):
        self.create_attendance()
        self.create_timesheets()

    def on_cancel(self):
        self.delete_draft_timesheets()
        self.cancel_attendance()

    def create_attendance(self):
        if not frappe.db.exists(
            "Attendance",
            {
                "employee": self.employee,
                "attendance_date": self.date,
                "docstatus": ("!=", 2)
            }
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
                billing_hours = 0
                if log.billable != "0%":
                    billing_hours = (
                        math.ceil(
                            get_billable_duration(log) / FIVE_MINUTES
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
                                "is_billable": int(log.billable != "0%"),
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
                        "note": log.note if log.note and not log.note.strip().startswith("+") else None,
                        "parent_project": log.project,
                        "customer": customer,
                        "employee": self.employee,
                        "working_time": self.name,
                    }
                ).insert()

    def delete_draft_timesheets(self):
        for timesheet in frappe.get_list(
            "Timesheet", filters={"working_time": self.name, "docstatus": DocStatus.draft()}
        ):
            frappe.delete_doc("Timesheet", timesheet.name)

    def cancel_attendance(self):
        if frappe.has_permission("Attendance", "cancel"):
            # Cancelling will be done by the framework automatically
            return

        attendance_name = frappe.db.get_value(
            "Attendance",
            {
                "working_time": self.name,
                "docstatus": ("!=", DocStatus.cancelled())
            }
        )
        if not attendance_name:
            return

        attendance = frappe.get_doc("Attendance", attendance_name)
        attendance.flags.ignore_permissions = True
        attendance.cancel()


def get_costing_rate(employee):
    return frappe.get_value(
        "Activity Cost",
        {"activity_type": "Default", "employee": employee},
        "costing_rate",
    )


def get_billable_duration(log):
    if log.billable == "0%":
        return 0

    return log.duration * float(log.billable.rstrip("% ")) / 100
