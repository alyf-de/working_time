# Copyright (c) 2026, ALYF GmbH and Contributors

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from working_time.api.permission import has_app_permission
from working_time.tests.helpers import app_permission_test_user

WORKING_TIME_DOCTYPE = "Working Time"


class IntegrationTestWorkingTimeAppPermission(IntegrationTestCase):
	def test_has_app_permission_for_shipped_roles(self):
		cases = (
			("Employee", "wt.appperm.employee@example.com"),
			("Freelancer", "wt.appperm.freelancer@example.com"),
		)
		for role, email in cases:
			with self.subTest(role=role):
				with app_permission_test_user(
					self,
					email=email,
					role=role,
					first_name="WT",
					last_name=role,
				) as user_email:
					frappe.set_user(user_email)
					self.assertTrue(has_app_permission())

	def test_has_app_permission_with_custom_docperm(self):
		with app_permission_test_user(
			self,
			email="wt.appperm.custom@example.com",
			role="WT AppPerm Custom Role",
			first_name="WT",
			last_name="Custom",
			insert_role=True,
			custom_docperm_doctype=WORKING_TIME_DOCTYPE,
		) as user_email:
			frappe.set_user(user_email)
			self.assertTrue(has_app_permission())

	def test_has_app_permission_denied_without_read(self):
		with app_permission_test_user(
			self,
			email="wt.appperm.denied@example.com",
			role="WT AppPerm Denied Role",
			first_name="WT",
			last_name="Denied",
			insert_role=True,
		) as user_email:
			frappe.set_user(user_email)
			self.assertFalse(has_app_permission())
