import json

import frappe
from frappe.utils.telemetry import capture

SETUP_ADMIN_ROLES = ("System Manager", "Raven Admin")


def is_setup_pending() -> bool:
	"""The first-admin setup flow should open for the session user."""
	if not frappe.db.get_single_value("Raven Settings", "setup_pending"):
		return False
	return bool(set(SETUP_ADMIN_ROLES) & set(frappe.get_roles()))


@frappe.whitelist(methods=["POST"])
def complete_setup(
	completed_steps: list[str] | str | None = None, skipped_steps: list[str] | str | None = None
):
	"""Ends the setup flow. A second admin finishing later is a no-op."""
	frappe.only_for(SETUP_ADMIN_ROLES)

	frappe.db.set_single_value("Raven Settings", "setup_pending", 0)
	capture(
		"setup_completed",
		"raven",
		properties={
			"completed_steps": _as_list(completed_steps),
			"skipped_steps": _as_list(skipped_steps),
		},
	)


def _as_list(value) -> list:
	"""Whitelisted list args arrive as JSON strings from form posts."""
	if isinstance(value, str):
		value = json.loads(value)
	return value or []
