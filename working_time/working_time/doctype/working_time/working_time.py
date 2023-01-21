# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import time_diff_in_seconds


class WorkingTime(Document):
    def before_validate(self):
        self.remove_seconds()
        self.set_to_times()
        self.set_durations()

    def validate(self):
        for log in self.time_logs:
            if log.duration and log.duration < 0:
                frappe.throw(_("Time logs must be continuous"))

    def remove_seconds(self):
        for log in self.time_logs:
            if log.from_time:
                log.from_time = f"{log.from_time[:-2]}00"

            if log.to_time:
                log.to_time = f"{log.to_time[:-2]}00"

    def set_to_times(self):
        for i in range(0, len(self.time_logs) - 1):
            self.time_logs[i].to_time = self.time_logs[i + 1].from_time

    def set_durations(self):
        self.break_time = 0
        self.working_time = 0

        for log in self.time_logs:
            if log.from_time and log.to_time:
                log.duration = time_diff_in_seconds(log.to_time, log.from_time)

            if log.duration:
                if log.is_break:
                    self.break_time += log.duration
                else:
                    self.working_time += log.duration
