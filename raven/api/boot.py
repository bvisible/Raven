"""Mini-boot for the Frappe Desk shell (sidebar + navbar) embedded in /raven.

Frappe Desk bundles (billing.bundle.js, nora_debug.js, etc.) expect certain
keys on `frappe.boot` at `$(document).ready` time. Since we do NOT load those
bundles in our website page (pattern copied from Builder/CRM/LMS + the Mint
and Neoconstruction integrations), we instead inject a curated subset of the
bootinfo just large enough for the navbar/sidebar to render correctly and for
defensive reads to never hit `undefined`.

The full `frappe.sessions.get()` payload is ~150 KB and can change shape
between Frappe versions; this curated view is ~10-20 KB and exposes a stable
contract the React components depend on.
"""
from __future__ import annotations

import frappe

# Curated boot keys consumed by FrappeNavbar / FrappeSidebar React components.
# Anything not listed here is dropped from `frappe.boot` to keep the payload
# small and the contract stable. Add new keys here whenever the UI needs them.
NAVBAR_BOOT_KEYS = (
	"user",
	"user_info",
	"navbar_settings",
	"desk_settings",
	"sysdefaults",
	"sitename",
	"lang",
	"letter_heads",
	"app_data",
	"apps_data",
	"allowed_workspaces",
	"home_page",
	"notification_settings",
	"energy_points_enabled",
	"points",
	"app_logo_url",
	"changelog_feed",
	"time_zone",
	"timezone_info",
	"is_fc_site",
	"developer_mode",
	"lang_dict",
	# Sidebar-specific keys (consumed by FrappeSidebar React component).
	# `sidebar_pages` carries the workspace tree (parent_page, public flag,
	# icon, indicator_color, sequence_id, is_hidden, ...).
	"sidebar_pages",
	"workspace_to_app_map",
	"module_app",
	# NoraLearn integration relies on these keys when the popup is mounted.
	"neoffice_settings",
	# `docs` carries the metadocs (DocType/Role/User/etc.) preloaded by Frappe.
	# main.tsx may call `frappe.model.sync(frappe.boot.docs)` so this MUST be
	# set otherwise React never mounts (Object.sync throws on undefined.docs).
	"docs",
	# Raven-specific keys consumed by frappe-react-sdk and Raven providers.
	"versions",
	"server_script_enabled",
	"push_relay_server_url",
)


def _load_ui_translations() -> dict:
	"""Load translations for the apps whose strings the embedded Frappe shell
	uses (sidebar + navbar labels). Without `desk.bundle.js`, Frappe never
	pushes these strings into `frappe._messages` so we have to bake them in
	the mini-boot ourselves, otherwise translation calls always return EN.
	"""
	from frappe.translate import get_all_translations

	try:
		# `get_all_translations(lang)` returns the merged dict for ALL apps
		# in the user's language. It is cached internally by Frappe, so the
		# cost is paid once per worker.
		return get_all_translations(frappe.local.lang) or {}
	except Exception:
		return {}


def get_navbar_boot() -> dict:
	"""Return the curated bootinfo subset used by FrappeNavbar/FrappeSidebar.

	Always sets `is_fc_site` and `developer_mode` (even if missing upstream)
	so that downstream JS bundles never see `undefined` on a defensive read.

	Bakes the UI translations directly into `__messages` so the embedded
	shell's `t()` calls resolve in the user's language without needing
	desk.bundle.js.

	Adds Raven-specific keys (push_relay_server_url, server_script_enabled)
	so the Raven SPA keeps the behaviour it had with the full bootinfo.
	"""
	from frappe.boot import get_bootinfo

	full = get_bootinfo()
	boot = {k: full.get(k) for k in NAVBAR_BOOT_KEYS}
	boot.setdefault("is_fc_site", False)
	boot.setdefault("developer_mode", bool(frappe.conf.get("developer_mode")))

	# Raven-specific defensive defaults.
	boot["push_relay_server_url"] = frappe.conf.get("push_relay_server_url")
	if "server_script_enabled" in frappe.conf:
		boot["server_script_enabled"] = frappe.conf.server_script_enabled
	else:
		boot["server_script_enabled"] = True

	# Merge boot's stock `__messages` (country names, etc.) with the full
	# translation dict of every installed app so the embedded shell can
	# translate any UI string it ships.
	messages = dict(full.get("__messages") or {})
	messages.update(_load_ui_translations())
	boot["__messages"] = messages
	return boot


@frappe.whitelist()
def get_navbar_boot_api() -> dict:
	"""HTTP endpoint to refresh navbar boot from the SPA (post settings change)."""
	return get_navbar_boot()
