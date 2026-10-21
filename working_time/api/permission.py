"""Apps screen visibility for Working Time."""

from __future__ import annotations

import frappe

_APP_ROLES = frozenset({"Employee", "Freelancer", "System Manager"})


def has_app_permission() -> bool:
	"""Return whether the session user may open Working Time on the apps screen."""
	if frappe.session.user == "Administrator":
		return True
	if frappe.session.user == "Guest":
		return False
	return bool(_APP_ROLES.intersection(frappe.get_roles()))
