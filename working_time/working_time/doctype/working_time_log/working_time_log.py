# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds


class WorkingTimeLog(Document):
	def cleanup(self):
		self.remove_seconds()
		self.uppercase_key()
		self.set_duration()

	def uppercase_key(self):
		if self.key:
			self.key = self.key.upper()

	def remove_seconds(self):
		if self.from_time:
			self.from_time = f"{self.from_time[:-2]}00"

		if self.to_time:
			self.to_time = f"{self.to_time[:-2]}00"

	def set_duration(self):
		if self.from_time and self.to_time:
			self.duration = time_diff_in_seconds(self.to_time, self.from_time)
