# //// Neoffice — added file (no upstream equivalent). We configure the Frappe HR integration
# //// centrally and hide its settings panel, so the values have to be set rather than offered.
import frappe

DEFAULT_WORKSPACE = "Synk"


def execute():
	"""Turn the Frappe HR integration on, on every instance.

	Three things have to happen, in this order, and the order is not cosmetic:

	1. `company_workspace_mapping` must be filled FIRST. `Raven Settings.validate` throws
	   "Please map the companies to the workspace before enabling this feature." when
	   `auto_create_department_channel` is set with an empty mapping. Upstream's own
	   patches/v2_0/create_default_company_workspace_mapping.py fills it, but it returns early
	   when the flag is off — which it is on every instance of ours — and it hardcodes the
	   workspace name "Raven", which no longer exists since we renamed it to Synk.
	2. `department_channel_type` must be non-empty. The stored single can hold NULL on a site
	   that never opened the panel, and a NULL type means no channel is ever created — the
	   feature looks enabled and does nothing.
	3. only then the flag itself.

	A field default would reach none of this: it only applies to a NEW record, so an existing
	site keeps whatever the single already holds. Measured on osiris 2026-09-22: 0 / NULL / 0,
	all three against the field defaults.

	⚠️ Nothing here may raise. A patch that throws aborts `bench migrate` for the whole site —
	the first version of this patch did exactly that on osiris, and on the fleet that is an
	instance marked Failed for a setting. Every failure is logged and swallowed.
	"""
	try:
		settings = frappe.get_doc("Raven Settings")

		if not settings.company_workspace_mapping:
			workspace = (
				DEFAULT_WORKSPACE
				if frappe.db.exists("Raven Workspace", DEFAULT_WORKSPACE)
				else frappe.db.get_value("Raven Workspace", {"type": "Public"}, "name")
			)
			if not workspace:
				# No workspace to map to: leave the integration alone rather than half-enable it.
				return

			companies = (
				frappe.get_all("Company", pluck="name") if "erpnext" in frappe.get_installed_apps() else []
			)
			for company in companies:
				settings.append(
					"company_workspace_mapping", {"company": company, "raven_workspace": workspace}
				)

		if not settings.department_channel_type:
			settings.department_channel_type = "Private"

		# The "this person is on leave" warning when you mention someone.
		if not settings.show_if_a_user_is_on_leave:
			settings.show_if_a_user_is_on_leave = 1

		# Only now, and only if there is something to map it to.
		if settings.company_workspace_mapping and not settings.auto_create_department_channel:
			settings.auto_create_department_channel = 1

		settings.save(ignore_permissions=True)
		frappe.db.commit()

	except Exception:
		frappe.db.rollback()
		frappe.log_error(
			"Synk: HR integration not enabled",
			f"raven.patches.neoffice.enable_hr_integration could not apply its settings.\n\n"
			f"{frappe.get_traceback()}",
		)
