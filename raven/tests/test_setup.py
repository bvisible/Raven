from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from raven.api.setup import (
	add_users_without_workspace,
	complete_setup,
	get_company,
	get_users_without_workspace,
)
from raven.boot import boot_session
from raven.install import after_install, should_create_default_workspace

EXTRA_TEST_RECORD_DEPENDENCIES = ["User", "Raven User"]

MEMBER = "setup-member@example.com"
LONER = "setup-loner@example.com"


def _make_raven_user(email: str, first_name: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"send_welcome_email": 0,
				"roles": [{"role": "Raven User"}],
			}
		).insert(ignore_permissions=True)


def _make_workspace(name: str):
	return frappe.get_doc(
		{"doctype": "Raven Workspace", "workspace_name": name, "type": "Public"}
	).insert()


def _make_channel(workspace: str, name: str, type: str = "Public"):
	return frappe.get_doc(
		{"doctype": "Raven Channel", "channel_name": name, "type": type, "workspace": workspace}
	).insert()


class TestSetup(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_make_raven_user(MEMBER, "Setup Member")
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
		complete_setup(["workspace", "team"], ["channel"])
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

	def test_complete_setup_drops_cached_boot(self):
		# Boot is cached per user; a stale copy would still open the setup flow.
		frappe.cache.hset("bootinfo", "some-admin@example.com", {"raven_setup_pending": 1})
		complete_setup([], [])
		self.assertIsNone(frappe.cache.hget("bootinfo", "some-admin@example.com"))

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

	def _forget_settings(self):
		# A fresh install has no stored Raven Settings yet.
		frappe.db.delete("Singles", {"doctype": "Raven Settings"})
		frappe.clear_document_cache("Raven Settings", "Raven Settings")
		frappe.local.db.value_cache.pop("Raven Settings", None)

	def test_install_stores_settings_defaults(self):
		self._forget_settings()
		with patch("frappe.__version__", "16.0.0"):
			after_install()
		# Frappe only fills defaults for singles with nothing stored, and the flag above stores one.
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "auto_add_system_users"), 1)
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "show_raven_on_desk"), 1)
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 1)

	def test_install_below_v16_stores_defaults_without_setup(self):
		self._forget_settings()
		with (
			patch("frappe.__version__", "15.42.1"),
			patch("raven.install.create_default_workspace_and_channel"),
		):
			after_install()
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "auto_add_system_users"), 1)
		self.assertEqual(frappe.db.get_single_value("Raven Settings", "setup_pending"), 0)


class TestUsersWithoutWorkspace(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_make_raven_user(LONER, "Loner")
		frappe.db.delete("Raven Workspace Member", {"user": LONER})
		self.workspace = _make_workspace("Setup Test Workspace")
		self.channel = _make_channel(self.workspace.name, "setup-test")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _listed(self):
		return [row["user"] for row in get_users_without_workspace()]

	def test_lists_people_in_no_workspace(self):
		self.assertIn(LONER, self._listed())

	def test_leaves_out_workspace_members_and_the_caller(self):
		frappe.get_doc(
			{"doctype": "Raven Workspace Member", "workspace": self.workspace.name, "user": LONER}
		).insert()
		listed = self._listed()
		self.assertNotIn(LONER, listed)
		self.assertNotIn("Administrator", listed)

	def test_leaves_out_disabled_people(self):
		frappe.db.set_value("Raven User", {"user": LONER}, "enabled", 0)
		self.assertNotIn(LONER, self._listed())

	def test_add_puts_them_in_the_workspace_and_channel(self):
		self.assertGreaterEqual(add_users_without_workspace(self.workspace.name, self.channel.name), 1)
		self.assertTrue(
			frappe.db.exists("Raven Workspace Member", {"workspace": self.workspace.name, "user": LONER})
		)
		self.assertTrue(
			frappe.db.exists("Raven Channel Member", {"channel_id": self.channel.name, "user_id": LONER})
		)
		# Everyone is in a workspace now, so a second call has no one to add.
		self.assertEqual(add_users_without_workspace(self.workspace.name, self.channel.name), 0)

	def test_add_without_a_channel(self):
		add_users_without_workspace(self.workspace.name)
		self.assertTrue(
			frappe.db.exists("Raven Workspace Member", {"workspace": self.workspace.name, "user": LONER})
		)
		self.assertFalse(frappe.db.exists("Raven Channel Member", {"user_id": LONER}))

	def test_add_to_an_open_channel_adds_no_member_rows(self):
		# Everyone in the workspace is in an Open channel; rows are made on first visit.
		general = _make_channel(self.workspace.name, "setup-general", type="Open")
		add_users_without_workspace(self.workspace.name, general.name)
		self.assertTrue(
			frappe.db.exists("Raven Workspace Member", {"workspace": self.workspace.name, "user": LONER})
		)
		self.assertFalse(frappe.db.exists("Raven Channel Member", {"user_id": LONER}))

	def test_add_refuses_a_channel_from_another_workspace(self):
		other = _make_workspace("Setup Other Workspace")
		elsewhere = _make_channel(other.name, "setup-elsewhere")
		with self.assertRaises(frappe.ValidationError):
			add_users_without_workspace(self.workspace.name, elsewhere.name)

	def test_members_cannot_list_or_add(self):
		frappe.set_user(LONER)
		with self.assertRaises(frappe.PermissionError):
			get_users_without_workspace()
		with self.assertRaises(frappe.PermissionError):
			add_users_without_workspace(self.workspace.name)


class TestCompanyDefaults(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")

	def test_none_without_a_default_company(self):
		with patch("frappe.defaults.get_global_default", return_value=None):
			self.assertIsNone(get_company())

	def test_name_and_public_logo_of_the_default_company(self):
		with (
			patch("frappe.defaults.get_global_default", return_value="Acme"),
			patch.object(frappe.db, "table_exists", return_value=True),
			patch.object(frappe.db, "exists", return_value=True),
			patch.object(frappe.db, "get_value", return_value="/files/acme.png"),
		):
			self.assertEqual(get_company(), {"name": "Acme", "logo": "/files/acme.png"})

	def test_leaves_out_a_private_logo(self):
		# Every member sees the workspace logo; a private file wouldn't load for them.
		with (
			patch("frappe.defaults.get_global_default", return_value="Acme"),
			patch.object(frappe.db, "table_exists", return_value=True),
			patch.object(frappe.db, "exists", return_value=True),
			patch.object(frappe.db, "get_value", return_value="/private/files/acme.png"),
		):
			self.assertEqual(get_company(), {"name": "Acme", "logo": None})

	def test_members_cannot_read_it(self):
		_make_raven_user(MEMBER, "Setup Member")
		frappe.set_user(MEMBER)
		with self.assertRaises(frappe.PermissionError):
			get_company()
