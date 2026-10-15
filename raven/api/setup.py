from contextlib import suppress

import frappe
from frappe.utils.telemetry import capture

SETUP_ADMIN_ROLES = ("System Manager", "Raven Admin")
SETUP_STEPS = ("invite", "workspace", "channel", "hr")


def is_setup_admin() -> bool:
	"""Only these roles run the first-admin setup flow."""
	return bool(set(SETUP_ADMIN_ROLES) & set(frappe.get_roles()))


@frappe.whitelist(methods=["POST"])
def complete_setup(
	completed_steps: list[str] | str | None = None, skipped_steps: list[str] | str | None = None
):
	"""Ends the setup flow. A second admin finishing later is a no-op."""
	frappe.only_for(SETUP_ADMIN_ROLES)

	frappe.db.set_single_value("Raven Settings", "setup_pending", 0)
	# Boot is cached per user and carries the flag; every admin's copy is now stale.
	frappe.cache.delete_key("bootinfo")

	# Telemetry is best-effort: a malformed step list must not fail the request and undo the flag.
	with suppress(ValueError, TypeError):
		capture(
			"setup_completed",
			"raven",
			properties={
				"completed_steps": _known_steps(completed_steps),
				"skipped_steps": _known_steps(skipped_steps),
			},
		)


def _known_steps(value) -> list[str]:
	"""Step names from a list or its JSON string; anything unknown is dropped."""
	return [step for step in frappe.parse_json(value) or [] if step in SETUP_STEPS]
