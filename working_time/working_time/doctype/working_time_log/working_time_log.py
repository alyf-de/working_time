# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

# import frappe
from datetime import timedelta
from frappe.model.document import Document
from frappe.utils.data import time_diff_in_seconds, to_timedelta


class WorkingTimeLog(Document):
	def cleanup_and_set_duration(self):
		self.ensure_timedelta()
		self.remove_seconds()
		self.uppercase_key()
		self.set_duration()

	def uppercase_key(self):
		if self.key:
			self.key = self.key.upper()

	def ensure_timedelta(self):
		if isinstance(self.from_time, str):
			self.from_time = to_timedelta(self.from_time) if self.from_time else None

		if isinstance(self.to_time, str):
			self.to_time = to_timedelta(self.to_time) if self.to_time else None

	def remove_seconds(self):
		if self.from_time:
			self.from_time = timedelta(seconds=self.from_time.total_seconds() // 60 * 60)

		if self.to_time:
			self.to_time = timedelta(seconds=self.to_time.total_seconds() // 60 * 60)

	def set_duration(self):
		if self.from_time and self.to_time:
			self.duration = (self.to_time - self.from_time).total_seconds()
