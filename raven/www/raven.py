# //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): module docstring for the
# //// rewritten controller.
"""Controller Jinja for the /raven website page (and all its sub-routes).

Populates the context with:
  - boot               -> window.frappe.boot for FrappeSidebar/Navbar + frappe-react-sdk
  - csrf_token         -> for POST calls to /api/method/*
  - desk_css_url       -> hashed asset `desk.bundle.css` (Frappe core)
  - neoffice_theme_css_url -> `neoffice-theme.css` (theme shell)
  - PWA metadata       -> kept from the original Raven controller (icons,
                          splash screens, app_name, preload_links).

Pattern aligned with mint/www/mint.py and the Frappe Shell Native doc.
"""
import json
import re

import frappe
import frappe.sessions
from frappe import _
from frappe.utils.telemetry import capture

# //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): the curated mini-boot.
from raven.api.boot import get_navbar_boot

no_cache = 1

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")


# //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): resolves desk.bundle.css and
# //// neoffice-theme.css to their hashed URLs, so the embedded chrome is styled without loading
# //// desk.bundle.js (whose boot sequence fights the SPA's).
def _get_asset_url(asset_path: str) -> str:
	"""Resolve `<bundle>.bundle.css|js` to its hashed URL via Frappe's assets map.

	Returns an empty string when no hashed URL is found, so the caller can fall
	back to a non-hashed path.
	"""
	if ".bundle." not in asset_path:
		return ""
	try:
		from frappe.utils.jinja_globals import bundled_asset

		resolved = bundled_asset(asset_path) or ""
		if resolved and ".bundle." in resolved and resolved != asset_path:
			return resolved
		return ""
	except Exception:
		return ""


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	# Manually commit the CSRF token here
	frappe.db.commit()  # nosemgrep

	if frappe.session.user == "Guest":
		boot = frappe.website.utils.get_boot_data()
	else:
		try:
			# //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): frappe.sessions.get() ships the whole
			# //// desk bootinfo - large, and full of keys the SPA never reads. get_navbar_boot() returns the
			# //// ~28 keys the embedded sidebar/navbar actually need, guarantees the defensive ones exist and
			# //// bakes the UI translations into __messages (without them the chrome renders in English).
			# Curated mini-boot designed for FrappeNavbar/FrappeSidebar rather
			# than the full frappe.sessions.get() payload. Keeps surface small
			# and stable, guarantees defensive keys (is_fc_site, developer_mode)
			# are always set, and bakes UI translations into __messages so the
			# embedded shell renders in the user's language.
			boot = get_navbar_boot()
		except Exception as e:
			raise frappe.SessionBootFailed from e
			# //// Neoffice - push_relay_server_url and server_script_enabled now come from get_navbar_boot()
			# //// (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"), so the copies here are gone.

	boot_json = frappe.as_json(boot, indent=None, separators=(",", ":"))
	boot_json = SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = CLOSING_SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = json.dumps(boot_json)

	context.update(
		# //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): the two CSS URLs are added to the
		# //// template context here.
		{
			"build_version": frappe.utils.get_build_version(),
			"boot": boot_json,
			"csrf_token": csrf_token,
		}
	)

	# Frappe Desk CSS bundles for the embedded shell. Loading the CSS is enough
	# to render the navbar/sidebar markup correctly; we do NOT load
	# desk.bundle.js (timing + dependency hell with billing/nora).
	context["desk_css_url"] = _get_asset_url("desk.bundle.css")
	context["neoffice_theme_css_url"] = (
		_get_asset_url("neoffice-theme.css") or "/assets/neoffice_theme/css/neoffice-theme.css"
	)

	app_name = frappe.get_website_settings("app_name") or frappe.get_system_settings("app_name")

	if app_name and app_name != "Frappe":
		# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): page title.
		context["app_name"] = app_name + " | " + "Synk"
	else:
		# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): page title fallback.
		context["app_name"] = "Synk"

	favicon = frappe.get_website_settings("favicon")

	context["icon_96"] = favicon or "/assets/raven/manifest/favicon-96x96.png"
	context["apple_touch_icon"] = favicon or "/assets/raven/manifest/apple-touch-icon.png"
	context["mask_icon"] = favicon or "/assets/raven/manifest/safari-pinned-tab.svg"
	context["favicon_svg"] = favicon or "/assets/raven/manifest/favicon.svg"
	context["favicon_ico"] = favicon or "/assets/raven/manifest/favicon.ico"
	context["sitename"] = boot.get("sitename")

	if frappe.session.user != "Guest":
		capture("active_site", "raven")

		context[
			"preload_links"
		] = """
			<link rel="preload" href="/api/method/frappe.auth.get_logged_user" as="fetch" crossorigin="use-credentials">
			<link rel="preload" href="/api/method/raven.api.workspaces.get_list" as="fetch" crossorigin="use-credentials">
			<link rel="preload" href="/api/method/raven.api.raven_users.get_list" as="fetch" crossorigin="use-credentials">
			<link rel="preload" href="/api/method/raven.api.raven_channel.get_all_channels?hide_archived=false" as="fetch" crossorigin="use-credentials">
			"""
	else:
		context["preload_links"] = ""

	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return json.loads(get_boot())


def get_boot():
	try:
		# //// Neoffice - Frappe Shell Native (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven"): the dev-server context must return the
		# //// same mini-boot as production, or the chrome behaves differently in dev.
		# Curated mini-boot — same payload as get_context() so dev parity is kept.
		boot = get_navbar_boot()
	except Exception as e:
		raise frappe.SessionBootFailed from e
		# //// Neoffice - same removal as L65, dev path (1c1c81edc, 2026-05-11 "feat(frappe-shell): integrate native Frappe sidebar+navbar in /raven").

	boot_json = frappe.as_json(boot, indent=None, separators=(",", ":"))
	boot_json = SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = CLOSING_SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = json.dumps(boot_json)

	return boot_json
