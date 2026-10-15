# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from raven.api.raven_channel import create_direct_message_channel

EXTRA_TEST_RECORD_DEPENDENCIES = ["User", "Raven User"]


class TestRavenChannel(FrappeTestCase):
	def setUp(self):
		frappe.get_doc("User", "test1@example.com").add_roles("Raven User")
		frappe.get_doc("User", "test3@example.com").add_roles("Raven User")

	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def test_dm_with_more_than_two_users_is_rejected(self):
		# The audit's case: test1 sets up test3's notes-to-self channel with test1 in it.
		frappe.set_user("test1@example.com")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "Raven Channel",
					"channel_name": "test3@example.com _ test3@example.com _ test1@example.com",
					"is_direct_message": 1,
				}
			).insert()

	def test_dm_between_two_users_still_works(self):
		frappe.set_user("test1@example.com")
		channel = frappe.get_doc("Raven Channel", create_direct_message_channel("test3@example.com"))
		self.assertEqual(
			{channel.dm_user_1, channel.dm_user_2}, {"test1@example.com", "test3@example.com"}
		)
