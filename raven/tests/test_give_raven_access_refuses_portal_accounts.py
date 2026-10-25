# //// Neoffice - added file (no upstream equivalent)
# A portal account must never be given Raven: "Raven User" is created with desk_access=1, so the
# save turns a Website User into a System User, which takes a paid licence seat (WI-00353).
import frappe
from frappe.tests import IntegrationTestCase

from raven.api.raven_users import add_users_to_raven, give_raven_access, invite_user

PORTAL = "raven-portal-guard@yopmail.com"


class TestGiveRavenAccessRefusesPortalAccounts(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._delete_portal_user()
		frappe.get_doc(
			{
				"doctype": "User",
				"email": PORTAL,
				"first_name": "Portal",
				"user_type": "Website User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		self._delete_portal_user()

	def _delete_portal_user(self):
		frappe.db.delete("Raven User", {"user": PORTAL})
		if frappe.db.exists("User", PORTAL):
			frappe.delete_doc("User", PORTAL, force=True, ignore_permissions=True)

	def _stays_a_portal_account(self):
		self.assertEqual(frappe.db.get_value("User", PORTAL, "user_type"), "Website User")
		self.assertFalse(frappe.db.exists("Has Role", {"parent": PORTAL, "role": "Raven User"}))
		self.assertFalse(frappe.db.exists("Raven User", {"user": PORTAL}))

	def test_the_shared_function_refuses(self):
		with self.assertRaises(frappe.ValidationError):
			give_raven_access(frappe.get_doc("User", PORTAL))
		self._stays_a_portal_account()

	def test_the_dialog_lists_the_account_as_failed(self):
		result = add_users_to_raven([PORTAL])
		self.assertEqual([user.name for user in result["failed_users"]], [PORTAL])
		self.assertEqual(result["success_users"], [])
		self._stays_a_portal_account()

	def test_an_invitation_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			invite_user(PORTAL)
		self._stays_a_portal_account()
