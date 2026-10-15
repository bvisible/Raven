from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from raven.install import import_existing_system_users

SYSTEM_USER = "import-system@example.com"
WEBSITE_USER = "import-website@example.com"
DISABLED_USER = "import-disabled@example.com"
PROFILE_USER = "import-profile@example.com"
ROLE_PROFILE = "Raven Import Test Profile"


class TestImportSystemUsers(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# Made "before Raven": the save-time hook must not add them.
		frappe.db.set_single_value("Raven Settings", "auto_add_system_users", 0)

		if not frappe.db.exists("Role Profile", ROLE_PROFILE):
			frappe.get_doc(
				{
					"doctype": "Role Profile",
					"role_profile": ROLE_PROFILE,
					"roles": [{"role": "System Manager"}],
				}
			).insert(ignore_permissions=True)

		self._user(SYSTEM_USER, roles=["System Manager"])
		self._user(WEBSITE_USER, roles=[])
		self._user(DISABLED_USER, roles=["System Manager"], enabled=0)
		self._user(PROFILE_USER, role_profile_name=ROLE_PROFILE)

		frappe.db.set_single_value("Raven Settings", "auto_add_system_users", 1)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _user(self, email, roles=None, enabled=1, role_profile_name=None):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"enabled": enabled,
				"send_welcome_email": 0,
				"roles": [{"role": role} for role in roles or []],
			}
		)
		if role_profile_name:
			user.role_profile_name = role_profile_name
		user.insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("Raven User", email))

	def test_adds_enabled_system_users(self):
		import_existing_system_users()
		self.assertTrue(frappe.db.exists("Raven User", SYSTEM_USER))
		self.assertIn("Raven User", frappe.get_roles(SYSTEM_USER))

	def test_skips_website_disabled_and_role_profile_users(self):
		import_existing_system_users()
		for email in (WEBSITE_USER, DISABLED_USER, PROFILE_USER):
			self.assertFalse(frappe.db.exists("Raven User", email), email)

	def test_does_nothing_when_auto_add_is_off(self):
		frappe.db.set_single_value("Raven Settings", "auto_add_system_users", 0)
		import_existing_system_users()
		self.assertFalse(frappe.db.exists("Raven User", SYSTEM_USER))

	def test_one_failing_user_does_not_stop_the_rest(self):
		real_add_roles = frappe.get_doc("User", SYSTEM_USER).__class__.add_roles

		def add_roles(user, *roles):
			if user.name == SYSTEM_USER:
				raise frappe.ValidationError("another app refused this save")
			return real_add_roles(user, *roles)

		other = "import-system-2@example.com"
		frappe.db.set_single_value("Raven Settings", "auto_add_system_users", 0)
		self._user(other, roles=["System Manager"])
		frappe.db.set_single_value("Raven Settings", "auto_add_system_users", 1)

		with patch("frappe.core.doctype.user.user.User.add_roles", add_roles):
			import_existing_system_users()
		self.assertFalse(frappe.db.exists("Raven User", SYSTEM_USER))
		self.assertTrue(frappe.db.exists("Raven User", other))
