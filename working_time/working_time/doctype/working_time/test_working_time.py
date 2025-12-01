# Copyright (c) 2023, ALYF GmbH and Contributors
# See license.txt

import unittest

from frappe import _dict

from working_time.working_time.doctype.working_time.working_time import aggregate_time_logs


class TestWorkingTime(unittest.TestCase):
	def test_aggregate_time_logs(self):
		logs = [
			_dict(
				project="Project A",
				key="KEY-1",
				duration=3600,
				billable="100%",
				note="Internal Note 1",
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=1800,
				billable="100%",
				note="Internal Note 2",
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=1800,
				billable="100%",
				note="Internal Note 2",  # Duplicate, should be ignored
			),
			_dict(
				project="Project A",
				key="KEY-1",
				duration=3600,
				billable="100%",
				note="Internal Note 1",  # Not consecutive, should be added
			),
			_dict(
				project="Project B",
				key="KEY-2",
				task="Task B",
				duration=3600,
				billable="100%",
				note="+Customer Note 1",
			),
			_dict(
				project="Project B",
				key="KEY-2",
				task="Task B",
				duration=3600,
				billable="100%",
				note="+Customer Note 1",  # Duplicate, should be ignored
			),
		]

		result = aggregate_time_logs(logs)

		# Check Project A
		project_a = result[("Project A", None, "KEY-1")]
		self.assertEqual(project_a["hours"], 3.0)
		self.assertEqual(
			project_a["internal_notes"], ["Internal Note 1", "Internal Note 2", "Internal Note 1"]
		)
		self.assertEqual(project_a["customer_notes"], [])

		# Check Project B
		project_b = result[("Project B", "Task B", "KEY-2")]
		self.assertEqual(project_b["hours"], 2.0)
		self.assertEqual(project_b["internal_notes"], [])
		self.assertEqual(project_b["customer_notes"], ["Customer Note 1"])
