# Copyright (c) 2026, ALYF GmbH and Contributors

from __future__ import annotations

import contextlib
from unittest import TestCase

import frappe
from frappe.permissions import add_permission


def delete_custom_docperm(doctype: str, role: str) -> None:
	for name in frappe.get_all(
		"Custom DocPerm",
		filters={"parent": doctype, "role": role},
		pluck="name",
	):
		frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)


def delete_disposable_app_permission_user(role_name: str, user_email: str) -> None:
	frappe.set_user("Administrator")
	for employee in frappe.get_all("Employee", filters={"user_id": user_email}, pluck="name"):
		frappe.delete_doc("Employee", employee, force=True, ignore_permissions=True)
	if frappe.db.exists("User", user_email):
		frappe.delete_doc("User", user_email, force=True, ignore_permissions=True)
	if role_name and frappe.db.exists("Role", role_name):
		frappe.delete_doc("Role", role_name, force=True, ignore_permissions=True)
	frappe.clear_cache()


def insert_disposable_test_user(
	email: str,
	*,
	first_name: str,
	last_name: str,
	roles: tuple[str, ...],
) -> str:
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"send_welcome_email": 0,
			"enabled": 1,
		}
	)
	for role in roles:
		user.append("roles", {"role": role})
	user.insert(ignore_permissions=True)
	return email


def insert_linked_employee(user_email: str, *, first_name: str) -> None:
	frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": first_name,
			"gender": "Female",
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2020-01-01",
			"company": "_Test Company",
			"user_id": user_email,
			"status": "Active",
		}
	).insert(ignore_permissions=True)


@contextlib.contextmanager
def app_permission_test_user(
	testcase: TestCase,
	*,
	email: str,
	role: str,
	first_name: str,
	last_name: str,
	insert_role: bool = False,
	custom_docperm_doctype: str | None = None,
):
	"""Disposable **User** / **Role** / **Custom DocPerm** for ``has_app_permission`` tests."""
	if insert_role:
		frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_if_duplicate=True)
	if custom_docperm_doctype:
		add_permission(custom_docperm_doctype, role, 0, ptype="read")

	insert_disposable_test_user(email, first_name=first_name, last_name=last_name, roles=(role,))
	if role == "Employee":
		# ERPNext removes the Employee role from users without a linked Employee.
		# Saving a linked Employee adds the role back.
		insert_linked_employee(email, first_name=first_name)

	def cleanup() -> None:
		if custom_docperm_doctype and insert_role:
			delete_custom_docperm(custom_docperm_doctype, role)
		delete_disposable_app_permission_user(role if insert_role else "", email)

	testcase.addCleanup(cleanup)
	yield email
