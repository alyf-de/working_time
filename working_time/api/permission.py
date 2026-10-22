"""Apps screen visibility for Working Time."""

from __future__ import annotations

import frappe


def has_app_permission() -> bool:
	"""Return whether the session user may open Working Time on the apps screen."""
	if frappe.session.user == "Guest":
		return False
	return frappe.has_permission("Working Time") or frappe.has_permission("Freelancer Time")
