# Copyright (c) 2026, ALYF GmbH and Contributors

from __future__ import annotations

import frappe
from frappe.permissions import add_permission
from frappe.tests import IntegrationTestCase

from working_time.api.permission import has_app_permission


def _delete_custom_docperm(doctype: str, role: str) -> None:
	for name in frappe.get_all(
		"Custom DocPerm",
		filters={"parent": doctype, "role": role},
		pluck="name",
	):
		frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)


def _delete_role_and_user(role_name: str, user_email: str) -> None:
	frappe.set_user("Administrator")
	if frappe.db.exists("User", user_email):
		frappe.delete_doc("User", user_email, force=True, ignore_permissions=True)
	if role_name and frappe.db.exists("Role", role_name):
		frappe.delete_doc("Role", role_name, force=True, ignore_permissions=True)
	frappe.clear_cache()


class IntegrationTestWorkingTimeAppPermission(IntegrationTestCase):
	def test_has_app_permission_for_shipped_roles(self):
		cases = (
			("Employee", "wt.appperm.employee@example.com"),
			("Freelancer", "wt.appperm.freelancer@example.com"),
		)
		for role, email in cases:
			with self.subTest(role=role):
				self.addCleanup(lambda e=email: _delete_role_and_user("", e))

				user = frappe.get_doc(
					{
						"doctype": "User",
						"email": email,
						"first_name": "WT",
						"last_name": role,
						"send_welcome_email": 0,
						"enabled": 1,
					}
				)
				user.append("roles", {"role": role})
				user.insert(ignore_permissions=True)

				frappe.set_user(email)
				self.assertTrue(has_app_permission())

	def test_has_app_permission_with_custom_docperm(self):
		role_name = "WT AppPerm Custom Role"
		email = "wt.appperm.custom@example.com"
		doctype = "Working Time"
		self._register_role_user_cleanup(role_name, email, doctype)

		frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_if_duplicate=True)
		add_permission(doctype, role_name, 0, ptype="read")

		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "WT",
				"last_name": "Custom",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.append("roles", {"role": role_name})
		user.insert(ignore_permissions=True)

		frappe.set_user(email)
		self.assertTrue(has_app_permission())

	def test_has_app_permission_denied_without_read(self):
		role_name = "WT AppPerm Denied Role"
		email = "wt.appperm.denied@example.com"
		self._register_role_user_cleanup(role_name, email)

		frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_if_duplicate=True)
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "WT",
				"last_name": "Denied",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		)
		user.append("roles", {"role": role_name})
		user.insert(ignore_permissions=True)

		frappe.set_user(email)
		self.assertFalse(has_app_permission())

	def _register_role_user_cleanup(
		self, role_name: str, user_email: str, doctype: str | None = None
	) -> None:
		def cleanup() -> None:
			if doctype:
				_delete_custom_docperm(doctype, role_name)
			_delete_role_and_user(role_name, user_email)

		self.addCleanup(cleanup)
