# //// Neoffice — added file (no upstream equivalent). We configure the Frappe HR integration
# //// centrally and hide its settings panel, so the values have to be set rather than offered.
import frappe

DEFAULTS = {
	# A channel per department, which is what customers expect from the integration.
	# Note this only ever fires on `Department.after_insert` — no channel is created
	# retroactively for departments that already exist.
	"auto_create_department_channel": 1,
	# The field's own default, but the stored Single can hold NULL on a site that never
	# opened the panel, and a NULL type means no channel gets created at all.
	"department_channel_type": "Private",
	# The "this person is on leave" warning when you mention someone. The field defaults to 1
	# but the stored value is 0 on sites created before it existed.
	"show_if_a_user_is_on_leave": 1,
}


def execute():
	"""Turn the Frappe HR integration on, on every instance.

	The doctype default only applies to a NEW site: an existing one carries whatever the Single
	already holds, so a default change alone would never reach the fleet. Measured on osiris
	2026-09-22: auto_create_department_channel=0, department_channel_type=NULL and
	show_if_a_user_is_on_leave=0, all three against the field defaults.

	Idempotent, and it does not fight a deliberate choice: each value is only written when it is
	empty or falsy, never when someone has already set something else.
	"""
	settings = frappe.get_single("Raven Settings")
	changed = []

	for field, value in DEFAULTS.items():
		if not settings.get(field):
			settings.set(field, value)
			changed.append(field)

	if changed:
		settings.save(ignore_permissions=True)
		frappe.db.commit()
