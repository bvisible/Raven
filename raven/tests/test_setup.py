from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from raven.api.setup import complete_setup
from raven.boot import boot_session
from raven.install import after_install, should_create_default_workspace

EXTRA_TEST_RECORD_DEPENDENCIES = ["User", "Raven User"]

MEMBER = "setup-member@example.com"


class TestSetup(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", MEMBER):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": MEMBER,
					"first_name": "Setup Member",
					"send_welcome_email": 0,
					"roles": [{"role": "Raven User"}],
				}
			).insert(ignore_permissions=True)
		frappe.db.set_single_value("Raven Settings", "setup_pending", 1)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _boot_flag(self):
		bootinfo = frappe._dict()
		boot_session(bootinfo)
		return bootinfo.raven_setup_pending

	def test_boot_flags_pending_for_admin(self):
		self.assertEqual(self._boot_flag(), 1)

	def test_boot_not_pending_once_cleared(self):
		frappe.db.set_single_value("Raven Settings", "setup_pending", 0)
		self.assertEqual(self._boot_flag(), 0)

	def test_boot_not_pending_for_member(self):
		frappe.set_user(MEMBER)
		self.assertEqual(self._boot_flag(), 0)

	def test_complete_setup_clears_flag_and_is_idempotent(self):
		complete_setup(["invite", "workspace"], ["channel"])
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 0)
		complete_setup('["workspace"]', "[]")
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 0)

	def test_complete_setup_survives_malformed_steps(self):
		complete_setup("not json", '["hr", "<script>"]')
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 0)

	def test_complete_setup_refuses_guest(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			complete_setup([], [])

	def test_complete_setup_refuses_member(self):
		frappe.set_user(MEMBER)
		with self.assertRaises(frappe.PermissionError):
			complete_setup([], [])
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 1)

	def test_install_defaults_only_below_v16(self):
		for version, expected in (
			("15.42.1", True),
			("16.0.0", False),
			("17.0.0-dev", False),
			("custom", True),
		):
			with patch("frappe.__version__", version):
				self.assertEqual(should_create_default_workspace(), expected)

	def test_install_on_v16_flags_setup_instead_of_creating_workspace(self):
		frappe.db.set_single_value("Raven Settings", "setup_pending", 0)
		workspaces = frappe.db.count("Raven Workspace")
		channels = frappe.db.count("Raven Channel")

		with patch("frappe.__version__", "16.0.0"):
			after_install()

		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 1)
		self.assertEqual(frappe.db.count("Raven Workspace"), workspaces)
		self.assertEqual(frappe.db.count("Raven Channel"), channels)
