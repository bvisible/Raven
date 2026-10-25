import frappe

from raven.api import raven_mobile


def execute():
	"""Every site gets a usable OAuth client for the app: created where none exists, repaired otherwise."""
	# //// Neoffice - skipped: the OAuth client of our instances serves the Neoffice mobile app (io.neoffice.app:),
	# //// made by neoffice_theme.mobile.ensure_all_oauth_clients. Registering upstream's redirect on it, or
	# //// creating a second client ("Raven Mobile"), would let upstream's native app sign in to our sites.
	return
	client_id = frappe.db.get_single_value("Raven Settings", "oauth_client")
	if raven_mobile.usable_client_id(client_id):
		return
	if not client_id or not frappe.db.exists("OAuth Client", client_id):
		raven_mobile.create_oauth_client()
		return
	# A client from the React Native app: add this app's redirect URI, and make it public.
	client = frappe.get_doc("OAuth Client", client_id)
	uris = (client.redirect_uris or "").split()
	if raven_mobile.NATIVE_REDIRECT_URI not in uris:
		client.redirect_uris = " ".join([*uris, raven_mobile.NATIVE_REDIRECT_URI])
	raven_mobile.make_public(client)
	client.save(ignore_permissions=True)
