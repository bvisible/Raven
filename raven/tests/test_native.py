from contextlib import contextmanager
from unittest.mock import patch

import frappe
import frappe.boot
import frappe.sessions

# //// Neoffice - Frappe v15 has no frappe.tests.IntegrationTestCase (v16): its FrappeTestCase plays it.
try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from werkzeug.wrappers import Response

from raven.api.native import APP_HEADER, APP_ORIGINS, add_cors_headers, app_boot, boot, set_cors
# //// Neoffice - SYNK_REDIRECT_URI: the redirect of our Synk app, whose OAuth client the tests
# //// below expect get_client_id to hand out (30.09.2026, upstream #2266 hid it).
from raven.api.raven_mobile import (
	MIN_APP_VERSION,
	NATIVE_REDIRECT_URI,
	SYNK_REDIRECT_URI,  # //// Neoffice - see below
	create_oauth_client,
	get_client_id,
)
from raven.patches.v3_0.add_native_oauth_redirect import execute as run_redirect_patch

# Frappe 15 and 16 have no such field; there every client is public.
HAS_AUTH_METHOD = frappe.get_meta("OAuth Client").has_field("token_endpoint_auth_method")

# Every boot field the app reads (apps/web: window.frappe.boot). Add one here when the app starts reading it.
APP_READS = (
	"user.name",
	"user.roles",
	"user.defaults",
	"user.can_read",
	"user.can_write",
	"user.can_create",
	"user.can_delete",
	"user.can_cancel",
	"user.can_search",
	"user.can_import",
	"user.can_export",
	"user_info",
	"sitename",
	"sysdefaults",
	"lang",
	"__messages",
	"versions",
	"time_zone",
	"max_file_size",
	"file_chunk_size",
	"chat_style",
	"raven_time_format",
	"raven_hide_read_receipts",
	"raven_quiet_hours_nudge",
	"quiet_hours",
	"link_preview_blocked_domains",
	"frappe_meet_hosted_urls",
	"push_notification_service",
	"vapid_public_key",
	"firebase_client_config",
	"server_script_enabled",
)


def read(boot, path):
	"""A dotted field of a boot, None when any part is missing."""
	for key in path.split("."):
		boot = (boot or {}).get(key)
	return boot


class TestNative(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.previous_client = frappe.db.get_single_value("Raven Settings", "oauth_client")
		self.client = frappe.get_doc(
			{
				"doctype": "OAuth Client",
				"app_name": "Raven Native Test",
				"scopes": "all openid",
				"redirect_uris": f"raven.thecommit.company: {NATIVE_REDIRECT_URI}",
				"default_redirect_uri": "raven.thecommit.company:",
				"grant_type": "Authorization Code",
				"response_type": "Code",
			}
		)
		if HAS_AUTH_METHOD:
			self.client.token_endpoint_auth_method = "None"
		self.client.insert(ignore_permissions=True)
		frappe.db.set_single_value("Raven Settings", "oauth_client", self.client.name)

	def tearDown(self):
		frappe.db.set_single_value("Raven Settings", "oauth_client", self.previous_client)
		frappe.db.rollback()
		super().tearDown()

	def test_client_info_reports_client_and_versions(self):
		data = get_client_id()
		self.assertEqual(data["client_id"], self.client.name)
		self.assertEqual(data["min_app_version"], MIN_APP_VERSION)
		self.assertEqual(data["sitename"], frappe.local.site)
		self.assertTrue(data["raven_version"])
		self.assertTrue(data["app_name"])
		# No favicon of its own set: the app shows its initial, not Raven's artwork twice.
		self.assertIsNone(data["logo"])

	# //// Neoffice - upstream hides a client without its native redirect, or one that demands a secret
	# //// (and its patch makes both right); ours serves our own apps (Synk, Neoffice), whose redirects it
	# //// does not know, so the configured client is handed out whatever it lists.
	def test_client_info_hands_out_the_configured_client(self):
		self.client.redirect_uris = "io.neoffice.app:"
		self.client.save(ignore_permissions=True)
		# //// Neoffice - the client is handed out although its redirect is not upstream's.
		self.assertEqual(get_client_id()["client_id"], self.client.name)

	# //// Neoffice - the Synk app's client holds only its own redirect, and must be found.
	def test_client_info_reports_a_synk_client(self):
		self.client.redirect_uris = SYNK_REDIRECT_URI
		self.client.save(ignore_permissions=True)
		# //// Neoffice - found by its Synk redirect.
		self.assertEqual(get_client_id()["client_id"], self.client.name)

	# //// Neoffice - create_oauth_client is ours (the Synk redirect, not upstream's native one).
	def test_created_client_is_public(self):
		frappe.db.set_single_value("Raven Settings", "oauth_client", None)
		create_oauth_client()
		client = frappe.get_doc(
			"OAuth Client", frappe.db.get_single_value("Raven Settings", "oauth_client")
		)
		# //// Neoffice - the redirect is the Synk one, upstream's native one is not added.
		self.assertIn(SYNK_REDIRECT_URI, client.redirect_uris)
		self.assertNotIn(NATIVE_REDIRECT_URI, client.redirect_uris)
		if HAS_AUTH_METHOD:
			self.assertEqual(client.token_endpoint_auth_method, "None")
		self.assertEqual(get_client_id()["client_id"], client.name)

	# //// Neoffice - the patch is neutralised: the fleet's client (neoffice_theme.mobile) is left as it
	# //// is, no redirect of upstream's native app is added to it and no second client is made.
	def test_patch_leaves_the_clients_alone(self):
		self.client.redirect_uris = "io.neoffice.app:"
		self.client.save(ignore_permissions=True)
		# //// Neoffice - the patch changes neither the clients nor the one's redirects.
		clients = frappe.db.count("OAuth Client")
		run_redirect_patch()
		self.assertEqual(frappe.db.count("OAuth Client"), clients)
		self.client.reload()
		self.assertEqual(self.client.redirect_uris, "io.neoffice.app:")
		frappe.db.set_single_value("Raven Settings", "oauth_client", None)
		# //// Neoffice - and makes none where there is none.
		run_redirect_patch()
		self.assertEqual(frappe.db.count("OAuth Client"), clients)
		self.assertIsNone(get_client_id()["client_id"])

	def test_client_info_without_client(self):
		frappe.db.set_single_value("Raven Settings", "oauth_client", None)
		self.assertIsNone(get_client_id()["client_id"])

	@contextmanager
	def _request(self, origin=None, developer_mode=0, app=True, method="GET"):
		"""A request context like the one init_request builds, with a controlled conf."""
		headers = {"Origin": origin} if origin else {}
		# The app's marker: on the request itself, or in what a preflight asks to send.
		if origin and app:
			headers.update(
				{"Access-Control-Request-Headers": f"authorization, {APP_HEADER.lower()}"}
				if method == "OPTIONS"
				else {APP_HEADER: "1"}
			)
		frappe.local.request = frappe._dict(headers=headers, method=method)
		if hasattr(frappe.local, "allow_cors"):
			del frappe.local.allow_cors
		try:
			with patch("frappe.conf", frappe._dict(dict(frappe.conf), developer_mode=developer_mode)):
				yield
		finally:
			del frappe.local.request

	def test_boot_carries_session_and_raven_fields(self):
		frappe.cache.hdel("bootinfo", "Administrator")
		with self._request():
			data = boot()
		self.assertEqual(data["user"]["name"], "Administrator")
		self.assertIn("System Manager", data["user"]["roles"])
		self.assertIn("Administrator", data["user_info"])
		self.assertEqual(data["sitename"], frappe.local.site)
		self.assertIsInstance(data["lang"], str)
		self.assertIn("system", data["time_zone"])
		self.assertIn("raven", data["versions"])
		# //// Neoffice - the app is called Synk (hooks.py app_title).
		self.assertIn({"app_name": "raven", "app_title": "Synk"}, data["app_data"])
		self.assertIn("chat_style", data)
		self.assertIn("server_script_enabled", data)
		self.assertFalse(data["read_only"])
		self.assertNotIn("csrf_token", data)
		# Built for the app alone: Desk's cache stays for Desk to fill.
		self.assertIsNone(frappe.cache.hget("bootinfo", "Administrator"))
		frappe.as_json(data)

	def test_boot_reuses_desk_boot_when_cached(self):
		try:
			with self._request():
				frappe.sessions.get()
				data = boot()
		finally:
			frappe.cache.hdel("bootinfo", "Administrator")
		self.assertEqual(data["from_cache"], 1)
		# Raven's fields come from a hook Frappe runs on every boot, cached or not.
		self.assertIn("chat_style", data)
		self.assertFalse(data["read_only"])
		self.assertIn("server_script_enabled", data)

	def test_app_boot_matches_desk_boot_for_what_the_app_reads(self):
		# Fails when Frappe changes or moves a field, naming the one app_boot must follow.
		frappe.cache.hdel("bootinfo", "Administrator")
		try:
			with self._request():
				desk = frappe.sessions.get()
		finally:
			frappe.cache.hdel("bootinfo", "Administrator")
		app = app_boot()
		for field in APP_READS:
			with self.subTest(field=field):
				# //// Neoffice - sysdefaults: Desk's boot also runs the other apps' hooks, ERPNext's adds
				# //// its own defaults (quotation_valid_till); what the app builds must be in Desk's, no more.
				if field == "sysdefaults":
					for key, value in (read(app, field) or {}).items():
						self.assertEqual(frappe.as_json(value), frappe.as_json((read(desk, field) or {}).get(key)))
					continue
				self.assertEqual(frappe.as_json(read(app, field)), frappe.as_json(read(desk, field)))
		titles = {entry["app_name"]: entry.get("app_title") for entry in desk.get("app_data") or []}
		for entry in app["app_data"]:
			if entry["app_name"] in titles:
				self.assertEqual(entry["app_title"], titles[entry["app_name"]])

	def test_app_boot_falls_back_to_desk_boot_without_a_helper(self):
		with patch.dict(frappe.boot.__dict__), patch("frappe.sessions.get", return_value={"desk": 1}):
			del frappe.boot.__dict__["set_time_zone"]
			self.assertEqual(app_boot(), {"desk": 1})

	def test_boot_rejects_guest(self):
		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, boot)

	def _cors_for(self, origin, developer_mode=0, app=True, method="GET"):
		with self._request(origin, developer_mode, app, method):
			set_cors()
		return getattr(frappe.local, "allow_cors", None)

	def test_cors_allows_app_origins(self):
		for origin in APP_ORIGINS:
			self.assertEqual(self._cors_for(origin), origin)

	def test_cors_ignores_foreign_origin(self):
		self.assertIsNone(self._cors_for("https://evil.example"))

	def test_cors_needs_the_app_header(self):
		# A browser page at https://localhost sends the origin but cannot add the app's header.
		self.assertIsNone(self._cors_for("https://localhost", app=False))
		self.assertEqual(self._cors_for("https://localhost", method="OPTIONS"), "https://localhost")
		self.assertIsNone(self._cors_for("https://localhost", app=False, method="OPTIONS"))

	def _preflight_headers(self, frappe_version, allow_cors=None):
		"""CORS headers Raven adds to the app's preflight, on a given Frappe version and site allow_cors."""
		response = Response()
		with self._request("capacitor://localhost", method="OPTIONS"):
			set_cors()
			with (
				patch("frappe.__version__", frappe_version),
				patch("frappe.conf", frappe._dict(dict(frappe.conf), allow_cors=allow_cors)),
			):
				add_cors_headers(response=response, request=frappe.local.request)
		return response.headers

	def test_cors_headers_written_on_frappe_15(self):
		headers = self._preflight_headers("15.80.0")
		self.assertEqual(headers.get("Access-Control-Allow-Origin"), "capacitor://localhost")
		self.assertIn(APP_HEADER.lower(), headers.get("Access-Control-Allow-Headers"))

	def test_cors_headers_left_to_frappe_when_it_writes_them(self):
		# Frappe 16 answers the origin itself; on 15 a site allow_cors covering it does too. A second copy breaks CORS.
		for version, allow_cors in (
			("16.0.0", None),
			("15.80.0", "*"),
			("15.80.0", ["capacitor://localhost"]),
		):
			self.assertIsNone(
				self._preflight_headers(version, allow_cors).get("Access-Control-Allow-Origin")
			)

	def test_cors_allows_http_localhost_in_developer_mode_only(self):
		self.assertIsNone(self._cors_for("http://localhost"))
		self.assertEqual(self._cors_for("http://localhost", developer_mode=1), "http://localhost")
