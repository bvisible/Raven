import click
import frappe
from frappe.desk.page.setup_wizard.setup_wizard import add_all_roles_to, make_records


def after_install():
	try:
		print("Setting up Raven...")
		add_all_roles_to("Administrator")
		create_raven_user_for_administrator()
		create_general_channel()
		create_native_oauth_client()

		click.secho("Thank you for installing Raven!", fg="green")

	except Exception as e:
		BUG_REPORT_URL = "https://github.com/frappe/Raven/issues/new"
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


def create_general_channel():
	default_workspace = frappe.get_doc(
		{
			"doctype": "Raven Workspace",
			"workspace_name": "Raven",
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
