# //// Neoffice — added file (no upstream equivalent).
# ////
# //// /raven READS THE USER'S RAVEN PREFERENCES (maintenance#1324).
# ////
# //// The mini-boot of /raven (raven.api.boot.get_navbar_boot) keeps the keys of its list, and the
# //// keys Raven's own boot hook (raven.boot.boot_session) sets were not on it: the time format, the
# //// chat style, read receipts, quiet hours, the push and preview settings. /raven read « 12-hour »
# //// and the default chat style whatever the user had chosen (seen on the hub, 08.10).

import frappe

# //// Neoffice - Frappe v15 has no frappe.tests.IntegrationTestCase (v16): its FrappeTestCase plays it.
try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from raven.api.boot import get_navbar_boot
from raven.boot import boot_session

USER = "raven-boot-prefs@yopmail.com"


class TestRavensOwnBootKeysReachRaven(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", USER):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": USER,
					"first_name": "Raven prefs",
					"send_welcome_email": 0,
					"roles": [{"role": "Raven User"}],
				}
			).insert(ignore_permissions=True)
		raven_user = frappe.db.get_value("Raven User", {"user": USER})
		# The fixture is what the test says it is, or the test proves nothing.
		assert raven_user, "the Raven User role did not create the Raven User"
		frappe.db.set_value(
			"Raven User", raven_user, {"time_format": "24-hour", "chat_style": "Left-Right"}
		)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_the_users_raven_preferences_reach_raven(self):
		frappe.set_user(USER)
		boot = get_navbar_boot()
		self.assertEqual(boot.get("raven_time_format"), "24-hour")
		self.assertEqual(boot.get("chat_style"), "Left-Right")

	def test_every_key_ravens_boot_hook_sets_reaches_raven(self):
		frappe.set_user(USER)
		own = frappe._dict()
		boot_session(own)
		self.assertGreater(len(own), 3)
		self.assertEqual(set(own) - set(get_navbar_boot()), set())
