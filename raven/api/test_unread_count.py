# //// Neoffice - added file (no upstream equivalent)
# The unread counter must count exactly what the channel list can show. Direct messages with
# Administrator are hidden from Raven (raven_channel.get_all_channels), so their messages must not be
# counted either: the header read « 2 unread » about a conversation that is in no list, and no row
# could ever carry the count.

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from raven.api.raven_message import get_unread_count_for_channels

READER = "test@example.com"
PEER = "test1@example.com"
PREFIX = "nl-unread-"


def make_dm(name, channel_name, dm_user_1, dm_user_2, writer, count):
	"""A direct message channel the reader belongs to, with `count` unread messages from `writer`."""
	# db_insert writes no timestamps of its own, and the counter compares them.
	now = now_datetime()
	stamps = {"creation": now, "modified": now}
	frappe.get_doc(
		{
			"doctype": "Raven Channel",
			"name": name,
			"channel_name": channel_name,
			"type": "Private",
			"is_direct_message": 1,
			"dm_user_1": dm_user_1,
			"dm_user_2": dm_user_2,
			**stamps,
		}
	).db_insert()
	frappe.get_doc(
		{
			"doctype": "Raven Channel Member",
			"name": f"{name}-member",
			"channel_id": name,
			"user_id": READER,
			**stamps,
		}
	).db_insert()
	for i in range(count):
		frappe.get_doc(
			{
				"doctype": "Raven Message",
				"name": f"{name}-{i}",
				"owner": writer,
				"text": f"Unread {i}",
				"content": f"Unread {i}",
				"channel_id": name,
				"message_type": "Text",
				**stamps,
			}
		).db_insert()


def unread_by_channel():
	return {row.name: row.unread_count for row in get_unread_count_for_channels()}


class TestUnreadCount(IntegrationTestCase):
	def setUp(self):
		self.clean()
		frappe.set_user(READER)

	def tearDown(self):
		frappe.set_user("Administrator")
		self.clean()

	def clean(self):
		for doctype, field in (
			("Raven Message", "channel_id"),
			("Raven Channel Member", "channel_id"),
			("Raven Channel", "name"),
		):
			frappe.db.delete(doctype, {field: ["like", f"{PREFIX}%"]})

	def test_dm_with_administrator_is_not_counted(self):
		make_dm(f"{PREFIX}admin-dm", f"Administrator _ {READER}", READER, "Administrator", "Administrator", 2)

		self.assertNotIn(f"{PREFIX}admin-dm", unread_by_channel())

	def test_dm_named_after_administrator_is_not_counted(self):
		# A DM keeps the name it was created with, and the peer ids may not be filled in on old rows.
		make_dm(f"{PREFIX}named-dm", f"Administrator _ {READER}", None, None, "Administrator", 1)

		self.assertNotIn(f"{PREFIX}named-dm", unread_by_channel())

	def test_dm_with_a_colleague_is_still_counted(self):
		make_dm(f"{PREFIX}peer-dm", f"{PEER} _ {READER}", PEER, READER, PEER, 3)

		self.assertEqual(unread_by_channel().get(f"{PREFIX}peer-dm"), 3)

	def test_dm_without_peer_ids_is_still_counted(self):
		# NULL peer ids must not make the row vanish through a three-valued NOT.
		make_dm(f"{PREFIX}legacy-dm", f"{PEER} _ {READER}", None, None, PEER, 1)

		self.assertEqual(unread_by_channel().get(f"{PREFIX}legacy-dm"), 1)
