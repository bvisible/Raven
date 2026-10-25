import click
import frappe
from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to

# //// Neoffice - make_records: used by create_general_channel below (the default workspace and its channel).
from frappe.desk.page.setup_wizard.setup_wizard import make_records


def after_install():
	try:
		# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): install output.
		print("Setting up Synk...")
		add_all_roles_to("Administrator")
		create_raven_user_for_administrator()
		# //// Neoffice - upstream leaves the workspace and the "general" channel to its first-admin setup
		# //// flow; we never show that flow (setup_completed is 1 from here on, see mark_setup_completed),
		# //// so the default workspace "Synk" and its channel are made here, as before the 3.1 merge.
		create_general_channel()
		create_role_profiles()
		# //// Neoffice - create_native_oauth_client() is not called: the OAuth client of our instances is
		# //// the "Neoffice Mobile" one made by neoffice_theme.mobile.ensure_all_oauth_clients; upstream's
		# //// would add a second client ("Raven Mobile") that its own native app signs in with.
		mark_setup_completed()

		# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): install output.
		click.secho("Thank you for installing Synk!", fg="green")

	except Exception as e:
		BUG_REPORT_URL = "https://github.com/frappe/raven/issues/new"
		click.secho(
			# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): install output. TO REVIEW: the BUG_REPORT_URL just
			# //// above still points at The-Commit-Company/Raven, so a Neoffice install failure is reported
			# //// upstream.
			"Installation for Synk failed due to an error."
			" Please try re-installing the app or"
			f" report the issue on {BUG_REPORT_URL} if not resolved.",
			fg="bright_red",
		)
		raise e


def create_raven_user_for_administrator():

	if not frappe.db.exists("Raven User", {"user": "Administrator"}):
		frappe.get_doc(
			{
				"doctype": "Raven User",
				"user": "Administrator",
				"full_name": "Administrator",
				"type": "User",
			}
		).insert(ignore_permissions=True)


# //// Neoffice - added with the default workspace below (see after_install): the first-admin setup
# //// screen of upstream is never shown. Raven Settings.setup_completed and Raven User.onboarded also
# //// default to 1 in their DocType, for a site whose settings row does not exist yet.
def mark_setup_completed():
	frappe.db.set_single_value("Raven Settings", "setup_completed", 1)


def create_general_channel():
	# //// Neoffice - idempotent: a second run of after_install (a re-install, the test of it) found the
	# //// workspace "Synk" there and died on its duplicate name, which failed the whole install.
	if frappe.db.exists("Raven Workspace", "Synk"):
		return
	default_workspace = frappe.get_doc(
		{
			"doctype": "Raven Workspace",
			# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): the default workspace is created as "Synk".
			# //// Instances set up before this still carry a "Raven" workspace, which is why the mobile app
			# //// maps the name at display time (apps/mobile/.../WorkspaceSwitcher.tsx).
			"workspace_name": "Synk",
			"type": "Public",
		}
	)
	default_workspace.insert(ignore_permissions=True)

	# Make all users a member of this workspace and set them as admins
	users = frappe.get_all("Raven User")
	for user in users:
		try:
			frappe.get_doc(
				{
					"doctype": "Raven Workspace Member",
					"workspace": default_workspace.name,
					"user": user.name,
					"is_admin": True,
				}
			).insert(ignore_permissions=True)
		except Exception as e:
			pass  # nosemgrep

	channel = [
		{
			"doctype": "Raven Channel",
			"name": "general",
			"type": "Open",
			"channel_name": "General",
			"workspace": default_workspace.name,
		}
	]

	make_records(channel)


RAVEN_USER_PROFILE = "Raven User"
RAVEN_ADMIN_PROFILE = "Raven Admin"
ROLE_PROFILES = {
	RAVEN_USER_PROFILE: ["Raven User"],
	RAVEN_ADMIN_PROFILE: ["Raven User", "Raven Admin"],
}


def create_role_profiles():
	"""
	Role profiles that put someone on Raven. A user whose roles come from a profile loses any
	role added directly on their next save, so Raven access is given through a profile of its
	own, next to the ones their other apps gave them. Profiles that already exist are left alone.
	"""
	for name, roles in ROLE_PROFILES.items():
		if frappe.db.exists("Role Profile", name):
			continue
		frappe.get_doc(
			{"doctype": "Role Profile", "role_profile": name, "roles": [{"role": role} for role in roles]}
		).insert(ignore_permissions=True)


def create_native_oauth_client():
	"""The OAuth client the native app signs in with, so a new site works with the app at once."""
	from raven.api.raven_mobile import create_oauth_client

	try:
		create_oauth_client()
	except Exception:
		# The install still succeeds: `bench execute raven.api.raven_mobile.create_oauth_client` repairs it.
		frappe.log_error(title="Raven: could not create the native app's OAuth client")
		click.secho(
			"Could not create the OAuth client for the Raven app; see the Error Log.", fg="yellow"
		)
