# //// Neoffice — added file (no upstream equivalent): a person who gets the messaging joins the workspaces anyone may
# //// join, never a private one nor one on invitation only, and the patch puts the people already there, once
# //// (raven/open_workspaces.py, maintenance#1553).
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from raven.open_workspaces import (
	join_everyone_once,
	join_open_workspaces,
	join_open_workspaces_on_insert,
	open_workspaces,
)

# Its own account, created here and rolled back: the clone of a live site has none of the framework's test users.
NEW_PERSON = "raven-1553-test@example.com"


class TestOpenWorkspaces(IntegrationTestCase):
	def setUp(self):
		# No e-mail leaves the run: the fork sends at once and commits, a rollback would not take it back.
		self.sendmail = patch("frappe.sendmail")
		self.sendmail.start()
		frappe.set_user("Administrator")
		self.open = self._workspace("Open Workspace 1553", "Public", 0)
		self.on_invitation = self._workspace("Invitation Workspace 1553", "Public", 1)
		self.private = self._workspace("Private Workspace 1553", "Private", 0)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		self.sendmail.stop()

	def _workspace(self, name: str, kind: str, on_invitation: int) -> str:
		return (
			frappe.get_doc(
				{
					"doctype": "Raven Workspace",
					"workspace_name": name,
					"type": kind,
					"can_only_join_via_invite": on_invitation,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def _is_member(self, workspace: str, person: str) -> bool:
		return bool(frappe.db.exists("Raven Workspace Member", {"workspace": workspace, "user": person}))

	def _new_person(self) -> str:
		"""An account that gets the messaging role: Raven makes its Raven User, whose creation runs the hook."""
		frappe.get_doc(
			{
				"doctype": "User",
				"email": NEW_PERSON,
				"first_name": "Raven 1553 Test",
				"send_welcome_email": 0,
				"roles": [{"role": "Raven User"}],
			}
		).insert(ignore_permissions=True)
		person = frappe.db.get_value("Raven User", {"user": NEW_PERSON}, "name")
		self.assertTrue(person, "Raven made no Raven User for an account with the messaging role")
		return person

	def test_the_open_workspaces_are_the_public_ones_that_ask_no_invitation(self):
		workspaces = open_workspaces()
		self.assertIn(self.open, workspaces)
		self.assertNotIn(self.on_invitation, workspaces)
		self.assertNotIn(self.private, workspaces)

	def test_a_person_who_gets_the_messaging_joins_the_open_workspaces_only(self):
		person = self._new_person()
		self.assertTrue(self._is_member(self.open, person))
		self.assertFalse(self._is_member(self.on_invitation, person))
		self.assertFalse(self._is_member(self.private, person))

	def test_a_bot_or_a_disabled_account_joins_nothing(self):
		for doc in (
			frappe._dict(name="bot-1553", type="Bot", user=None, enabled=1),
			frappe._dict(name=NEW_PERSON, type="User", user=NEW_PERSON, enabled=0),
		):
			join_open_workspaces_on_insert(doc)
			self.assertFalse(self._is_member(self.open, doc.name))

	def test_the_patch_puts_the_people_already_there_once(self):
		person = self._new_person()
		# The account as it was before the hook: in no workspace.
		frappe.db.delete("Raven Workspace Member", {"workspace": self.open, "user": person})

		counts = join_everyone_once()
		self.assertTrue(self._is_member(self.open, person))
		self.assertGreaterEqual(counts[self.open], 1)
		self.assertFalse(self._is_member(self.on_invitation, person))
		self.assertFalse(self._is_member(self.private, person))

		# Run again, it adds nobody.
		again = join_everyone_once()
		self.assertEqual(again[self.open], 0)
		self.assertEqual(
			frappe.db.count("Raven Workspace Member", {"workspace": self.open, "user": person}), 1
		)

	def test_a_second_process_joining_the_same_person_meets_the_database_constraint_and_carries_on(self):
		# Two processes pass the "is not a member yet" check together; the second insert hits the unique
		# (workspace, user) constraint of upstream 3.2. Both checks are played blind here.
		person = self._new_person()
		self.assertTrue(self._is_member(self.open, person))
		real_exists = frappe.db.exists

		def blind(doctype, filters=None, *args, **kwargs):
			if doctype == "Raven Workspace Member":
				return None
			return real_exists(doctype, filters, *args, **kwargs)

		with (
			patch("frappe.db.exists", side_effect=blind),
			patch(
				"raven.raven.doctype.raven_workspace_member.raven_workspace_member.RavenWorkspaceMember.validate"
			),
		):
			joined = join_open_workspaces(person, [self.open])
		self.assertEqual(joined, [])
		self.assertEqual(
			frappe.db.count("Raven Workspace Member", {"workspace": self.open, "user": person}), 1
		)
