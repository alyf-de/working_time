"""Apps screen visibility for Working Time."""

from __future__ import annotations

import frappe

WORKING_TIME_MODULE = "Working Time"


def has_app_permission() -> bool:
	"""Return whether the session user may open Working Time on the apps screen."""
	if frappe.session.user == "Guest":
		return False

	user = frappe.get_user()
	if not user.allow_modules:
		user.build_permissions()

	return WORKING_TIME_MODULE in user.allow_modules
