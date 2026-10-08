# //// Neoffice — added file (no upstream equivalent): the patch that gives the system messages written before
# //// Raven v3 their structured event, so that the client translates them and shows the member's current name
# //// (maintenance#1324).
import json

import frappe

# //// Neoffice - Frappe v15 has no frappe.tests.IntegrationTestCase (v16): its FrappeTestCase plays it.
try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from raven.patches.neoffice.legacy_system_messages_carry_their_event import execute

JOINER = "raven-legacy-joiner@yopmail.com"
RENAMED = "raven-legacy-renamed@yopmail.com"


def _user(email, first_name):
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
	return email


class TestLegacySystemMessagesCarryTheirEvent(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		_user(JOINER, "Legacy Joiner")
		_user(RENAMED, "Renamed Since")
		workspace = frappe.db.get_value(
			"Raven Workspace", {"workspace_name": "Legacy System Test Workspace"}
		)
		if not workspace:
			workspace = (
				frappe.get_doc(
					{
						"doctype": "Raven Workspace",
						"workspace_name": "Legacy System Test Workspace",
						"type": "Public",
					}
				)
				.insert()
				.name
			)
		self.channel = frappe.get_doc(
			{
				"doctype": "Raven Channel",
				"channel_name": f"legacy-system-{frappe.generate_hash(length=6)}",
				"type": "Public",
				"workspace": workspace,
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Raven Message", {"channel_id": self.channel.name})
		frappe.delete_doc("Raven Channel", self.channel.name, force=True)

	def _legacy(self, text, owner):
		"""A system message as Raven v2 stored it: English text, no structured event."""
		doc = frappe.get_doc(
			{
				"doctype": "Raven Message",
				"channel_id": self.channel.name,
				"message_type": "System",
				"text": text,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Raven Message", doc.name, {"owner": owner, "json": None}, update_modified=False
		)
		return doc.name

	def _event(self, name):
		value = frappe.db.get_value("Raven Message", name, "json")
		return json.loads(value) if value else None

	def test_a_join_message_takes_the_event_of_the_member_who_wrote_it(self):
		message = self._legacy("Legacy Joiner joined.", JOINER)
		execute()
		self.assertEqual(self._event(message), {"event": "user_joined", "user": JOINER})

	def test_a_member_renamed_since_is_still_the_one_who_joined(self):
		# The text keeps the name of the day (« admin joined. »); the owner is who joined.
		message = self._legacy("admin joined.", RENAMED)
		execute()
		self.assertEqual(self._event(message), {"event": "user_joined", "user": RENAMED})

	def test_a_departure_takes_its_event(self):
		message = self._legacy("Legacy Joiner left.", JOINER)
		execute()
		self.assertEqual(self._event(message), {"event": "user_left", "user": JOINER})

	def test_a_message_written_by_administrator_for_someone_else_names_that_member(self):
		frappe.get_doc(
			{"doctype": "Raven Channel Member", "channel_id": self.channel.name, "user_id": JOINER}
		).insert(ignore_permissions=True)
		message = self._legacy("Legacy Joiner joined.", "Administrator")
		execute()
		self.assertEqual(self._event(message), {"event": "user_joined", "user": JOINER})

	def test_what_it_cannot_attribute_keeps_its_text(self):
		message = self._legacy("Nobody Known joined.", "Administrator")
		other = self._legacy("Legacy Joiner added Renamed Since.", JOINER)
		execute()
		self.assertIsNone(self._event(message))
		self.assertIsNone(self._event(other))
