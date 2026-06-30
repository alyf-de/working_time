from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from working_time.permissions import check_activity_type_access
from working_time.working_time.doctype.working_time.working_time import get_configured_activity_types

PERMISSIONS = "working_time.permissions.frappe.has_permission"


def deny_permission(*args, **kwargs):
	if kwargs.get("throw"):
		raise frappe.PermissionError
	return False


class TestWorkingTimePermissions(FrappeTestCase):
	def test_get_configured_activity_types_requires_permission(self):
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		if not employee:
			self.skipTest("No active employee")

		with patch(PERMISSIONS, side_effect=deny_permission):
			self.assertRaises(frappe.PermissionError, get_configured_activity_types, employee)

	def test_check_activity_type_access_checks_activity_cost(self):
		employee = frappe.db.get_value("Employee", {"status": "Active"}, "name")
		if not employee:
			self.skipTest("No active employee")

		checked = []

		def track(*args, **kwargs):
			checked.append((args[0], args[1]))
			return True

		with patch(PERMISSIONS, side_effect=track):
			check_activity_type_access(employee)

		self.assertIn(("Working Time", "read"), checked)
		self.assertIn(("Employee", "read"), checked)
		self.assertIn(("Activity Cost", "read"), checked)
