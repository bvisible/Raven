from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from raven.api.workspaces import join_default_workspace

EXTRA_TEST_RECORD_DEPENDENCIES = ["User", "Raven User"]

JOINER = "default-joiner@example.com"


class TestJoinDefaultWorkspace(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", JOINER):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": JOINER,
					"first_name": "Default Joiner",
					"send_welcome_email": 0,
					"roles": [{"role": "Raven User"}],
				}
			).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _memberships(self):
		return frappe.get_all("Raven Workspace Member", {"user": JOINER}, pluck="workspace")

	def test_joins_the_oldest_public_open_workspace(self):
		frappe.get_doc(
			{"doctype": "Raven Workspace", "workspace_name": "Default Join Open", "type": "Public"}
		).insert()
		expected = frappe.db.get_value(
			"Raven Workspace",
			{"type": "Public", "can_only_join_via_invite": 0},
			"name",
			order_by="creation asc",
		)

		frappe.set_user(JOINER)
		self.assertEqual(join_default_workspace(), expected)
		frappe.set_user("Administrator")
		self.assertEqual(self._memberships(), [expected])

	def test_a_member_gets_their_workspace_back_without_joining_another(self):
		workspace = frappe.get_doc(
			{"doctype": "Raven Workspace", "workspace_name": "Default Join Mine", "type": "Private"}
		).insert()
		frappe.get_doc(
			{"doctype": "Raven Workspace Member", "workspace": workspace.name, "user": JOINER}
		).insert(ignore_permissions=True)

		frappe.set_user(JOINER)
		self.assertEqual(join_default_workspace(), workspace.name)
		self.assertEqual(join_default_workspace(), workspace.name)
		frappe.set_user("Administrator")
		self.assertEqual(self._memberships(), [workspace.name])

	def test_losing_a_race_returns_the_workspace_the_other_request_joined(self):
		workspace = frappe.get_doc(
			{"doctype": "Raven Workspace", "workspace_name": "Default Join Race", "type": "Public"}
		).insert()
		frappe.get_doc(
			{"doctype": "Raven Workspace Member", "workspace": workspace.name, "user": JOINER}
		).insert(ignore_permissions=True)

		frappe.set_user(JOINER)
		# The first lookup ran before the other request's insert landed.
		with (
			patch("raven.api.workspaces.get_first_membership", side_effect=[None, workspace.name]),
			patch("raven.api.workspaces.get_default_workspace", return_value=workspace.name),
		):
			self.assertEqual(join_default_workspace(), workspace.name)

	def test_returns_none_when_nothing_is_open_to_join(self):
		frappe.set_user(JOINER)
		with patch("raven.api.workspaces.get_default_workspace", return_value=None):
			self.assertIsNone(join_default_workspace())
		frappe.set_user("Administrator")
		self.assertEqual(self._memberships(), [])

	def test_refuses_users_outside_raven(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			join_default_workspace()

	def test_refuses_users_whose_raven_role_was_removed(self):
		frappe.get_doc("User", JOINER).remove_roles("Raven User")
		frappe.set_user(JOINER)
		with self.assertRaises(frappe.PermissionError):
			join_default_workspace()
