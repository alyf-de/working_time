# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import math
from datetime import datetime

import frappe
from frappe import _
from frappe.model.docstatus import DocStatus
from frappe.model.document import Document
from frappe.utils.data import add_to_date, flt, format_duration, get_time, getdate

from working_time.jira_utils import get_description, get_jira_issue_url
from working_time.working_time.number_card.number_cards import get_chart_data

HALF_DAY = 3.25
OVERTIME_FACTOR = 1.15
MAX_HALF_DAY = HALF_DAY * OVERTIME_FACTOR * 60 * 60
FIVE_MINUTES = 5 * 60
ONE_HOUR = 60 * 60
WHOLE_DAY_HOURS = 8


class WorkingTime(Document):
	def before_validate(self):
		self.break_time = self.working_time = self.productive_time = self.paid_break_time = 0
		self.project_time = self.billable_time = 0
		self.project_pct = self.billable_pct = 0

		last_idx = len(self.time_logs) - 1
		for idx, log in enumerate(self.time_logs):
			log.to_time = self.time_logs[idx + 1].from_time if idx < last_idx else log.to_time
			log.cleanup_and_set_duration()
			log.duration = log.duration or 0

			if log.is_break:
				self.break_time += log.duration
				if log.is_paid_break:
					self.paid_break_time += log.duration
					self.working_time += log.duration
			else:
				log.is_paid_break = 0
				self.productive_time += log.duration
				self.working_time += log.duration
				if log.project:
					self.project_time += log.duration
					self.billable_time += get_billable_duration(log)

		if self.working_time:
			self.project_pct = round(self.project_time / self.working_time * 100, 0)
			self.billable_pct = round(self.billable_time / self.working_time * 100, 0)

	def validate(self):
		billable_projects = {log.project for log in self.time_logs if log.billable != "0%" and log.project}
		jira_sites = get_jira_sites_for_projects(billable_projects)

		for log in self.time_logs:
			if log.duration and log.duration < 0:
				frappe.throw(_("Please fix negative duration in row {0}").format(log.idx))

			if billable_row_missing_invoice_reference(log, jira_sites.get(log.project)):
				frappe.throw(
					_("Please add an issue key or invoice note to the billable row {0}").format(log.idx)
				)

		self.validate_working_time_policy()

	def validate_working_time_policy(self):
		policy_name = frappe.db.get_value("Employee", self.employee, "working_time_policy")
		if not policy_name:
			return

		policy = frappe.get_doc("Working Time Policy", policy_name)

		self.validate_blocked_day(policy)
		self.validate_holiday_block(policy)
		self.validate_max_working_time(policy)
		self.validate_mandatory_breaks(policy)
		self.validate_min_rest_between_days(policy)

	def validate_blocked_day(self, policy):
		if not policy.blocked_days:
			return

		day_name = getdate(self.date).strftime("%A")
		blocked_days = [row.blocked_day for row in policy.blocked_days]
		if day_name in blocked_days:
			frappe.throw(_("{0} is a blocked day according to the Working Time Policy").format(day_name))

	def validate_holiday_block(self, policy):
		if not policy.consider_holiday_list:
			return

		holiday_list = frappe.db.get_value("Employee", self.employee, "holiday_list")
		if not holiday_list:
			return

		is_holiday = frappe.db.exists(
			"Holiday",
			{"parent": holiday_list, "holiday_date": self.date, "weekly_off": 0},
		)
		if is_holiday:
			frappe.throw(
				_("{0} is a holiday according to your holiday list").format(
					frappe.utils.format_date(self.date)
				)
			)

	def validate_max_working_time(self, policy):
		if not policy.max_productive_time_per_day:
			return

		if self.productive_time > policy.max_productive_time_per_day:
			frappe.throw(
				_("Productive time ({0}) exceeds the maximum allowed ({1}) per day").format(
					format_duration(self.productive_time),
					format_duration(policy.max_productive_time_per_day),
				)
			)

	def validate_mandatory_breaks(self, policy):
		if not policy.mandatory_breaks:
			return

		for row in policy.mandatory_breaks:
			if self.productive_time >= row.work_threshold and self.break_time < row.required_break_minutes:
				frappe.throw(
					_("Productive time of {0} or more requires at least {1} of break time").format(
						format_duration(row.work_threshold),
						format_duration(row.required_break_minutes),
					)
				)

	def validate_min_rest_between_days(self, policy):
		if not policy.min_rest_between_days or not self.time_logs:
			return

		previous = frappe.db.get_value(
			"Working Time",
			{
				"employee": self.employee,
				"date": ("<", self.date),
				"docstatus": ("!=", 2),
				"name": ("!=", self.name),
			},
			["name", "date"],
			order_by="date desc",
			as_dict=True,
		)
		if not previous:
			return

		last_to_time = frappe.db.get_value(
			"Working Time Log",
			{"parent": previous.name, "to_time": ("is", "set")},
			"to_time",
			order_by="to_time desc",
		)
		if not last_to_time:
			return

		first_from_time = self.time_logs[0].from_time
		if not first_from_time:
			return

		prev_end = datetime.combine(getdate(previous.date), get_time(last_to_time))
		curr_start = datetime.combine(getdate(self.date), get_time(first_from_time))
		rest_seconds = (curr_start - prev_end).total_seconds()

		if rest_seconds < policy.min_rest_between_days:
			frappe.throw(
				_("Rest time since previous day ({0}) is less than the required minimum ({1})").format(
					format_duration(rest_seconds),
					format_duration(policy.min_rest_between_days),
				)
			)

	def before_submit(self):
		if self.whole_day_project and not any(
			log.project == self.whole_day_project for log in self.time_logs
		):
			frappe.throw(
				_("Please add at least one time log for the whole day project {0}.").format(
					frappe.bold(self.whole_day_project)
				),
				title=_("Missing Time Log"),
			)

	def on_submit(self):
		self.create_attendance()
		self.create_timesheets()

	def on_cancel(self):
		self.delete_draft_timesheets()
		self.cancel_attendance()

	def create_attendance(self):
		existing = frappe.db.exists(
			"Attendance",
			{"employee": self.employee, "attendance_date": self.date, "docstatus": ("!=", 2)},
		)

		if existing:
			frappe.db.set_value("Attendance", existing, "working_time", self.name)
		else:
			attendance = frappe.get_doc(
				{
					"doctype": "Attendance",
					"employee": self.employee,
					"status": "Present" if self.working_time > MAX_HALF_DAY else "Half Day",
					"attendance_date": self.date,
					"working_time": self.name,
				}
			)
			attendance.flags.ignore_permissions = True
			attendance.save()
			attendance.submit()

	def create_timesheets(self):
		regular_logs = self.time_logs
		if self.whole_day_project:
			whole_day_logs = [log for log in self.time_logs if log.project == self.whole_day_project]
			regular_logs = [log for log in self.time_logs if log.project != self.whole_day_project]
			if whole_day_logs:
				self.create_whole_day_timesheet(whole_day_logs)

		aggregated_time_logs = aggregate_time_logs(regular_logs)

		for (project, task, key), data in aggregated_time_logs.items():
			details = get_project_details(project)

			self.insert_timesheet(
				project=project,
				customer=details.customer,
				task=task,
				billing_rate=details.billing_rate,
				hours=data["hours"],
				billing_hours=data["billable_hours"],
				description=get_description(details.jira_site, key, "; ".join(data["customer_notes"])),
				jira_issue_url=get_jira_issue_url(details.jira_site, key),
				internal_notes=data["internal_notes"],
			)

	def create_whole_day_timesheet(self, logs):
		"""Merge all time logs for the whole day project into a single 8-hour timesheet."""
		customer_notes_by_key = {}
		internal_notes = []
		tasks = set()
		for log in logs:
			customer_note, internal_note = parse_note(log.note)
			if internal_note and (not internal_notes or internal_notes[-1] != internal_note):
				internal_notes.append(internal_note)

			customer_notes = customer_notes_by_key.setdefault(log.key, [])
			if customer_note and (not customer_notes or customer_notes[-1] != customer_note):
				customer_notes.append(customer_note)

			if log.task:
				tasks.add(log.task)

		details = get_project_details(self.whole_day_project)
		billing_rate = (
			flt(details.billing_rate_per_day) / WHOLE_DAY_HOURS
			if details.billing_rate_per_day
			else details.billing_rate
		)

		lines = []
		for key, customer_notes in customer_notes_by_key.items():
			note = "; ".join(customer_notes)
			if key:
				line = get_description(details.jira_site, key, None)
				if note:
					line += f": {note}"
				lines.append(line)
			elif note:
				lines.append(note)

		description = "\n".join(lines) or "-"
		keys = [key for key in customer_notes_by_key if key]
		hours = sum(log.duration or 0 for log in logs) / ONE_HOUR

		self.insert_timesheet(
			project=self.whole_day_project,
			customer=details.customer,
			task=tasks.pop() if len(tasks) == 1 else None,
			billing_rate=billing_rate,
			hours=hours,
			billing_hours=WHOLE_DAY_HOURS,
			description=description,
			jira_issue_url=get_jira_issue_url(details.jira_site, keys[0]) if len(keys) == 1 else None,
			internal_notes=internal_notes,
		)

	def insert_timesheet(
		self,
		project,
		customer,
		task,
		billing_rate,
		hours,
		billing_hours,
		description,
		jira_issue_url,
		internal_notes,
	):
		costing_rate = get_costing_rate(self.employee)

		frappe.get_doc(
			{
				"doctype": "Timesheet",
				"time_logs": [
					{
						"is_billable": int(billing_hours > 0),
						"project": project,
						"task": task,
						"activity_type": "Default",
						"base_billing_rate": billing_rate,
						"base_costing_rate": costing_rate,
						"costing_rate": costing_rate,
						"billing_rate": billing_rate,
						"hours": hours,
						"from_time": self.date,
						"billing_hours": billing_hours,
						"description": description,
						"jira_issue_url": jira_issue_url,
					}
				],
				"note": ",\n".join(internal_notes),
				"parent_project": project,
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
			"Attendance", {"working_time": self.name, "docstatus": ("!=", DocStatus.cancelled())}
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


def get_project_details(project: str):
	return frappe.get_value(
		"Project",
		project,
		["customer", "billing_rate", "billing_rate_per_day", "jira_site"],
		as_dict=True,
	)


def get_billable_duration(log):
	if log.billable == "0%":
		return 0

	return log.duration * float(log.billable.rstrip("% ")) / 100


def get_jira_sites_for_projects(projects: set[str]) -> dict[str, str | None]:
	if not projects:
		return {}

	return {
		row.name: row.jira_site
		for row in frappe.get_all(
			"Project",
			filters={"name": ("in", list(projects))},
			fields=["name", "jira_site"],
		)
	}


def billable_row_missing_invoice_reference(log, jira_site: str | None) -> bool:
	if log.billable == "0%" or not log.project or log.key:
		return False

	note = log.note.strip() if log.note else ""
	if not note:
		return True

	if jira_site:
		return not note.startswith("+")

	return False


def parse_note(note: str | None) -> tuple[str | None, str | None]:
	"""Parse a note into customer note and internal note."""
	customer_note = None
	internal_note = None
	stripped_note = note.strip() if note else None
	if stripped_note:
		if stripped_note.startswith("+"):
			customer_note = stripped_note[1:].strip()
		else:
			internal_note = stripped_note

	return customer_note, internal_note


def calculate_hours(log) -> tuple[float, float]:
	"""Calculate hours and billable hours from a time log."""
	hours = math.ceil(log.duration / FIVE_MINUTES) * FIVE_MINUTES / ONE_HOUR
	billing_hours = 0.0
	if log.billable != "0%":
		billing_hours = math.ceil(get_billable_duration(log) / FIVE_MINUTES) * FIVE_MINUTES / ONE_HOUR

	return hours, billing_hours


def aggregate_time_logs(time_logs) -> dict[tuple[str | None, str | None, str | None], dict]:
	"""Aggregate time logs by project and issue key."""
	aggregated_time_logs = {
		# (log.project, log.task, log.key): {
		#     customer_notes: [],
		#     internal_notes: [],
		#     billable_hours: 0,
		#     hours: 0,
		# }
	}

	for log in time_logs:
		if log.duration and log.project:
			hours, billing_hours = calculate_hours(log)
			customer_note, internal_note = parse_note(log.note)

			if (log.project, log.task, log.key) in aggregated_time_logs:
				aggregated_time_logs[(log.project, log.task, log.key)]["hours"] += hours
				aggregated_time_logs[(log.project, log.task, log.key)]["billable_hours"] += billing_hours

				customer_notes = aggregated_time_logs[(log.project, log.task, log.key)]["customer_notes"]
				if customer_note and (not customer_notes or customer_notes[-1] != customer_note):
					customer_notes.append(customer_note)

				internal_notes = aggregated_time_logs[(log.project, log.task, log.key)]["internal_notes"]
				if internal_note and (not internal_notes or internal_notes[-1] != internal_note):
					internal_notes.append(internal_note)
			else:
				aggregated_time_logs[(log.project, log.task, log.key)] = {
					"hours": hours,
					"billable_hours": billing_hours,
					"customer_notes": [customer_note] if customer_note else [],
					"internal_notes": [internal_note] if internal_note else [],
				}

	return aggregated_time_logs


@frappe.whitelist()
def get_working_time_stats(employee: str, date: str):
	if not employee or not date:
		return []

	today = getdate(date)
	yesterday = getdate(add_to_date(today, days=-1))
	start_of_last_month = getdate(add_to_date(today.replace(day=1), months=-1))
	start_of_this_month = today.replace(day=1)
	end_of_last_month = getdate(add_to_date(start_of_this_month, days=-1))

	working_time_avg_last_month = get_chart_data(
		employee, start_of_last_month, end_of_last_month, "working_time"
	)
	break_time_avg_last_month = get_chart_data(employee, start_of_last_month, end_of_last_month, "break_time")
	billing_time_avg_last_month = get_chart_data(
		employee, start_of_last_month, end_of_last_month, "billable_time"
	)
	billing_time_ratio_last_month = (
		billing_time_avg_last_month / working_time_avg_last_month if working_time_avg_last_month else 0
	)

	stats = [
		{
			"timespan": _("Last Month"),
			"daily_working_time": {
				"value": flt(working_time_avg_last_month, 2),
			},
			"billing_time_ratio": {
				"value": flt(billing_time_ratio_last_month * 100, 2),
			},
			"daily_break_time": {
				"value": flt(break_time_avg_last_month, 2),
			},
		}
	]
	if yesterday.month == today.month:
		working_time_avg_this_month = get_chart_data(employee, start_of_this_month, yesterday, "working_time")
		break_time_avg_this_month = get_chart_data(employee, start_of_this_month, yesterday, "break_time")
		billing_time_avg_this_month = get_chart_data(
			employee, start_of_this_month, yesterday, "billable_time"
		)
		billing_time_ratio_this_month = (
			billing_time_avg_this_month / working_time_avg_this_month if working_time_avg_this_month else 0
		)

		stats.append(
			{
				"timespan": _("This Month"),
				"daily_working_time": {
					"value": flt(working_time_avg_this_month, 2),
					"pct_change": get_pct_change(working_time_avg_this_month, working_time_avg_last_month),
				},
				"billing_time_ratio": {
					"value": flt(billing_time_ratio_this_month * 100, 2),
					"pct_change": get_pct_change(
						billing_time_ratio_this_month, billing_time_ratio_last_month
					),
				},
				"daily_break_time": {
					"value": flt(break_time_avg_this_month, 2),
					"pct_change": get_pct_change(break_time_avg_this_month, break_time_avg_last_month),
				},
			},
		)

	return stats


def get_pct_change(new, old):
	return flt(-100 * (1 - new / old), 2) if old else 0
