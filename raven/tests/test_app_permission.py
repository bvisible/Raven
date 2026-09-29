# //// Neoffice — added file (no upstream equivalent).
"""The app tile of Raven (Synk) is shown to an ENABLED Raven User only (#805).

`check_app_permission` used to test that a Raven User row exists for the account. The row of an account that
lost the Raven User role, or was disabled, is kept with `enabled = 0` (`add_user_to_raven`), and that account
still got the tile. The tests create their own accounts and the rollback removes them.
"""

import frappe
from frappe.tests import IntegrationTestCase

from raven.permissions import check_app_permission

EMAIL = "raven-app-tile@yopmail.com"


def _make_raven_user(email: str) -> None:
	"""A System User holding the Raven User role: `add_user_to_raven` creates its (enabled) Raven User row."""
	frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": "Tile",
			"send_welcome_email": 0,
			"roles": [{"role": "Raven User"}],
		}
	).insert(ignore_permissions=True)


class TestAppPermission(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_make_raven_user(EMAIL)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _tile_for(self, email: str) -> bool:
		frappe.set_user(email)
		return bool(check_app_permission())

	def test_an_enabled_raven_user_sees_the_tile(self):
		self.assertEqual(frappe.db.get_value("Raven User", EMAIL, "enabled"), 1)
		self.assertTrue(self._tile_for(EMAIL))

	def test_a_disabled_raven_user_does_not(self):
		frappe.db.set_value("Raven User", EMAIL, "enabled", 0)
		self.assertTrue(frappe.db.exists("Raven User", EMAIL), "the row is kept, only disabled")
		self.assertFalse(self._tile_for(EMAIL))

	def test_an_account_that_lost_the_raven_user_role_does_not(self):
		# what add_user_to_raven does when the role goes: the row stays, disabled
		user = frappe.get_doc("User", EMAIL)
		user.remove_roles("Raven User")
		self.assertEqual(frappe.db.get_value("Raven User", EMAIL, "enabled"), 0)
		self.assertFalse(self._tile_for(EMAIL))

	def test_an_account_with_no_raven_user_row_does_not(self):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": "raven-no-row@yopmail.com",
				"first_name": "NoRow",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("Raven User", "raven-no-row@yopmail.com"))
		self.assertFalse(self._tile_for("raven-no-row@yopmail.com"))

	def test_administrator_and_guest(self):
		self.assertTrue(self._tile_for("Administrator"))
		self.assertFalse(self._tile_for("Guest"))
