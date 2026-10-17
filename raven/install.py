import click
import frappe
from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to


def after_install():
	try:
		print("Setting up Raven...")
		add_all_roles_to("Administrator")
		create_raven_user_for_administrator()
		# The first admin makes the first workspace and channel in the setup flow.
		init_settings()
		import_existing_system_users()
		create_native_oauth_client()

		click.secho("Thank you for installing Raven!", fg="green")

	except Exception as e:
		BUG_REPORT_URL = "https://github.com/frappe/raven/issues/new"
		click.secho(
			"Installation for Raven failed due to an error."
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


def init_settings():
	"""
	Stores Raven Settings with its defaults and the setup flag on. Frappe fills a single's
	defaults only after after_install, and only if nothing is stored yet, so writing just the
	flag would leave every other setting (auto-add system users, …) reading as unset.
	"""
	settings = frappe.get_single("Raven Settings")
	settings.setup_pending = 1
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_validate = True
	settings.save(ignore_permissions=True)


def import_existing_system_users():
	"""
	System users made before Raven was installed are otherwise only added the next time
	their User is saved. "Automatically add system users" means now.
	"""
	if not frappe.db.get_single_value("Raven Settings", "auto_add_system_users"):
		return

	users = frappe.get_all(
		"User",
		filters={
			"user_type": "System User",
			"enabled": 1,
			"name": ["not in", ["Administrator", "Guest"]],
		},
		pluck="name",
	)
	already_in_raven = set(frappe.get_all("Raven User", filters={"type": "User"}, pluck="user"))
	for name in users:
		if name in already_in_raven:
			continue
		user = frappe.get_doc("User", name)
		# Their roles come from a role profile; it would drop a role added here.
		if user.role_profile_name or getattr(user, "role_profiles", None):
			continue
		# The role's save-time hook creates the Raven User. One user that fails to save must
		# not fail the install; they're added the next time their User is saved.
		frappe.db.savepoint("raven_import_user")
		try:
			user.add_roles("Raven User")
		except Exception:
			frappe.db.rollback(save_point="raven_import_user")
			frappe.log_error(title=f"Raven: could not add {name} on install")


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
