import calendar
from datetime import date, timedelta

import frappe
from frappe import _
from frappe.translate import print_language
from frappe.utils.data import get_url


def is_last_working_day(d: date, absent_days: list[date]) -> bool:
	"""Check if a date is the last working day of the month.

	The last working day is the last non-absent day of the month.

	Args:
	- d: The date to check
	- absent_days: List of absent days (including weekends, holidays, and leaves)
	"""
	# Get the last day of the month
	last_dom = calendar.monthrange(d.year, d.month)[1]
	last_date = date(d.year, d.month, last_dom)

	# Find the last working day by moving backwards from the last day
	# until we hit a working day
	current = last_date
	while current >= d and current in absent_days:
		current -= timedelta(days=1)

	return current == d


def send_month_end_reminders():
	"""Send working time submission reminders to employees.

	This method is called every day. If it's the last working day for an employee,
	it sends a reminder to submit their working time entries before the month ends.
	"""
	today = date.today()
	last_dom = calendar.monthrange(today.year, today.month)[1]
	last_date = date(today.year, today.month, last_dom)

	for employee, holiday_list, prefered_email, first_name, user_id, reports_to in frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "holiday_list", "prefered_email", "first_name", "user_id", "reports_to"],
		as_list=True,
	):
		holidays = get_holiday_dates(holiday_list, today, last_date)
		leaves = get_leaves(employee, today, last_date)
		absent_days = list(set(holidays + leaves))

		if not is_last_working_day(today, absent_days):
			continue

		language = None
		if user_id:
			language = frappe.db.get_value("User", user_id, "language")

		reply_to = frappe.db.get_value("Employee", reports_to, "prefered_email") if reports_to else None

		with print_language(language):
			frappe.sendmail(
				recipients=prefered_email,
				reply_to=reply_to,
				subject=_("Remember to submit your working time"),
				message=_(
					"""Dear {first_name},

{month} is almost over. Please remember to submit your <a href='{url}'>working time</a>.

Thanks in advance!"""
				).format(
					first_name=first_name,
					month=_(today.strftime("%B")),
					url=get_url(f"/app/working-time?employee={employee}&docstatus=0"),
				),
			)


def get_holiday_dates(holiday_list: str, first_date: date, last_date: date) -> list[date]:
	"""Get all holiday dates for a given holiday list and date range.

	Args:
	- holiday_list: The name of the holiday list to check
	- first_date: The start date of the range
	- last_date: The end date of the range

	Returns:
	- A list of holiday dates
	"""
	return frappe.get_all(
		"Holiday",
		filters=[
			("parent", "=", holiday_list),
			("holiday_date", ">=", first_date),
			("holiday_date", "<=", last_date),
		],
		pluck="holiday_date",
	)


def get_leaves(employee: str, first_date: date, last_date: date) -> list[date]:
	return frappe.get_all(
		"Attendance",
		filters=[
			("employee", "=", employee),
			("attendance_date", ">=", first_date),
			("attendance_date", "<=", last_date),
			("status", "=", "On Leave"),
			("docstatus", "=", 1),
		],
		pluck="attendance_date",
	)


def send_stale_reminders(cutoff_days: int = 3):
	"""Send reminders to employees to submit their working time entries.

	This method is called every day. If an employee has a draft working time entry
	that is older than 3 days, it sends a reminder to submit it.
	"""
	today = date.today()
	for working_time, employee in frappe.get_all(
		"Working Time",
		filters=[
			("docstatus", "=", 0),
			("date", "<=", today - timedelta(days=cutoff_days)),
		],
		fields=["name", "employee"],
		as_list=True,
	):
		language = None
		user_id, prefered_email, first_name, reports_to = frappe.db.get_value(
			"Employee", employee, ["user_id", "prefered_email", "first_name", "reports_to"]
		)
		if user_id:
			language = frappe.db.get_value("User", user_id, "language")

		reply_to = frappe.db.get_value("Employee", reports_to, "prefered_email") if reports_to else None

		with print_language(language):
			frappe.sendmail(
				recipients=prefered_email or user_id,
				reply_to=reply_to,
				subject=_("Remember to submit your working time"),
				message=_(
					"""Dear {first_name},

You have a draft <a href='{url}'>working time entry</a> that is older than {cutoff_days} days. Please submit it as soon as possible.

Thanks in advance!"""
				).format(
					first_name=first_name,
					url=get_url(f"/app/working-time/{working_time}"),
					cutoff_days=cutoff_days,
				),
			)
