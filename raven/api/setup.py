from contextlib import suppress

import frappe
from frappe import _
from frappe.utils.telemetry import capture

from raven.api.raven_channel_member import add_channel_members
from raven.api.workspaces import add_workspace_members

SETUP_ADMIN_ROLES = ("System Manager", "Raven Admin")
SETUP_STEPS = ("profile", "workspace", "channel", "team", "hr")


def is_setup_admin() -> bool:
	"""Only these roles run the first-admin setup flow."""
	return bool(set(SETUP_ADMIN_ROLES) & set(frappe.get_roles()))


def _users_without_workspace() -> list[dict]:
	"""Enabled people in Raven who belong to no workspace, except whoever is asking."""
	raven_user = frappe.qb.DocType("Raven User")
	member = frappe.qb.DocType("Raven Workspace Member")
	in_a_workspace = frappe.qb.from_(member).select(member.user)
	return (
		frappe.qb.from_(raven_user)
		.select(raven_user.user, raven_user.full_name, raven_user.user_image)
		.where(raven_user.type == "User")
		.where(raven_user.enabled == 1)
		.where(raven_user.user != frappe.session.user)
		.where(raven_user.user.notin(in_a_workspace))
		.orderby(raven_user.full_name)
	).run(as_dict=True)


@frappe.whitelist(methods=["GET"])
def get_users_without_workspace() -> list[dict]:
	"""For setup's "already have Raven" box: people imported on install that no one has added yet."""
	frappe.only_for(SETUP_ADMIN_ROLES)
	return _users_without_workspace()


@frappe.whitelist(methods=["GET"])
def get_company() -> dict | None:
	"""
	The site's default company, which ERPNext's setup wizard creates, to start the workspace from.
	Only a public logo is returned: every member sees the workspace logo.
	"""
	frappe.only_for(SETUP_ADMIN_ROLES)
	company = frappe.defaults.get_global_default("company")
	if (
		not company or not frappe.db.table_exists("Company") or not frappe.db.exists("Company", company)
	):
		return None
	logo = frappe.db.get_value("Company", company, "company_logo")
	return {"name": company, "logo": logo if logo and logo.startswith("/files/") else None}


@frappe.whitelist(methods=["POST"])
def add_users_without_workspace(workspace: str, channel: str | None = None) -> int:
	"""
	Adds everyone in no workspace to setup's workspace and channel. The list is worked out
	here, not taken from the client, so it can't be used to add arbitrary people.
	"""
	frappe.only_for(SETUP_ADMIN_ROLES)
	frappe.has_permission("Raven Workspace", doc=workspace, ptype="write", throw=True)
	channel_type = None
	if channel:
		channel_workspace, channel_type = frappe.db.get_value(
			"Raven Channel", channel, ["workspace", "type"]
		) or (None, None)
		if channel_workspace != workspace:
			frappe.throw(_("This channel is not in the workspace."))

	users = [row["user"] for row in _users_without_workspace()]
	if not users:
		return 0
	add_workspace_members(workspace, users)
	# Everyone in the workspace is in an Open channel; its rows are made on first visit.
	# Otherwise one batch, so the channel gets one "added" message, not one per person.
	if channel and channel_type != "Open":
		add_channel_members(channel, users)
	return len(users)


@frappe.whitelist(methods=["POST"])
def complete_setup(
	completed_steps: list[str] | str | None = None, skipped_steps: list[str] | str | None = None
):
	"""Ends the setup flow. A second admin finishing later is a no-op."""
	frappe.only_for(SETUP_ADMIN_ROLES)

	finish_frappe_setup()
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


def finish_frappe_setup():
	"""
	A Frappe Cloud signup opens Raven before the Framework's setup wizard. Frappe Cloud already
	stored the region and made the first user, so the wizard is finished here with those values.
	Apps with wizard stages of their own, like ERPNext, still need the real wizard.
	"""
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
	from frappe.integrations.frappe_providers.frappecloud_billing import is_fc_site

	if frappe.is_setup_complete() or not is_fc_site() or frappe.get_hooks("setup_wizard_stages"):
		return
	result = setup_complete(frappe_setup_args())
	if result.get("status") != "ok":
		# Raven's setup still ends; the Framework wizard stays available in Desk.
		frappe.log_error(
			title="Raven: could not finish the Framework setup wizard", message=result.get("fail")
		)


def frappe_setup_args() -> dict:
	"""What the wizard's first slide would have sent, from the values Frappe Cloud stored."""
	settings = frappe.get_single("System Settings")
	language = frappe.db.get_value("Language", settings.language, "language_name") or "English"
	return {
		"language": language,
		"lang": language,
		"country": settings.country,
		"timezone": settings.time_zone,
		"currency": settings.currency,
		"enable_telemetry": settings.enable_telemetry,
	}


def _known_steps(value) -> list[str]:
	"""Step names from a list or its JSON string; anything unknown is dropped."""
	return [step for step in frappe.parse_json(value) or [] if step in SETUP_STEPS]
