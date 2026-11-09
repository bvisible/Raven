# //// Neoffice — added file (no upstream equivalent). The department channel of a new Employee: the
# //// person is added to it once, and the insert is not refused for it (neoffice-maintenance#1717).
"""An Employee created with a user and a department joins the department's channel.

Frappe's insert runs `after_insert`, then `on_update`, and sets `flags.in_insert` between the two. A document that
was never saved counts every value as changed, so `on_update` took the department for a new one and added the person
a second time; Raven Channel Member refused the duplicate and the whole insert of the Employee failed.

What the handlers call is replaced (the settings, the channel, the Raven User, the member row): the point is how
often and when they are called, in the order Frappe calls them. No HR app is needed.
"""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from raven.raven_integrations.controllers import employee as sync

CONTROLLER = "raven.raven_integrations.controllers.employee"
CHANNELS = {"Sales": "channel-sales", "Support": "channel-support"}


def an_employee(**over):
	doc = frappe._dict(
		name="HR-EMP-TEST-1717",
		user_id="member@example.com",
		department="Sales",
		flags=frappe._dict(),
	)
	# a document nobody saved before: no previous version, so every value counts as changed
	doc.has_value_changed = MagicMock(return_value=True)
	doc.get_doc_before_save = MagicMock(return_value=None)
	doc.update(over)
	return doc


def department_sync():
	"""The department sync is on, the departments have a channel, the user has a Raven User."""
	return (
		patch(f"{CONTROLLER}.is_department_sync_on", return_value=True),
		patch(f"{CONTROLLER}.get_channel_for_department", side_effect=CHANNELS.get),
		patch(f"{CONTROLLER}.get_raven_user_for_user", return_value="raven-member"),
	)


class TestANewEmployeeJoinsItsDepartmentOnce(IntegrationTestCase):
	def test_an_insert_adds_the_person_once(self):
		doc = an_employee()
		on, channel, raven_user = department_sync()
		with on, channel, raven_user, patch(f"{CONTROLLER}.create_channel_member") as create:
			# the order of Frappe's insert: after_insert (no flag yet), then the flag, then on_update
			sync.after_insert(doc, None)
			doc.flags.in_insert = True
			sync.on_update(doc, None)

		create.assert_called_once_with(
			channel_id="channel-sales", raven_user_id="raven-member", employee_id="HR-EMP-TEST-1717"
		)

	def test_on_update_of_a_document_being_inserted_touches_nothing(self):
		doc = an_employee()
		doc.flags.in_insert = True
		on, channel, raven_user = department_sync()
		with on as sync_on, channel as get_channel, raven_user as get_user:
			with patch(f"{CONTROLLER}.create_channel_member") as create, patch.object(
				frappe.db, "delete"
			) as delete:
				sync.on_update(doc, None)

		for call in (sync_on, get_channel, get_user, create, delete):
			call.assert_not_called()


class TestAnEmployeeWhoseDepartmentChanges(IntegrationTestCase):
	def test_the_person_leaves_the_old_channel_and_joins_the_new_one(self):
		doc = an_employee(department="Support")
		doc.get_doc_before_save = MagicMock(return_value=frappe._dict(department="Sales"))
		on, channel, raven_user = department_sync()
		with on, channel, raven_user, patch(f"{CONTROLLER}.create_channel_member") as create:
			with patch.object(frappe.db, "delete") as delete:
				sync.on_update(doc, None)

		delete.assert_called_once_with(
			"Raven Channel Member", {"channel_id": "channel-sales", "user_id": "raven-member"}
		)
		create.assert_called_once_with(
			channel_id="channel-support", raven_user_id="raven-member", employee_id="HR-EMP-TEST-1717"
		)

	def test_an_employee_without_a_user_is_left_alone(self):
		doc = an_employee(user_id=None)
		on, channel, raven_user = department_sync()
		with on, channel, raven_user, patch(f"{CONTROLLER}.create_channel_member") as create:
			sync.on_update(doc, None)
		create.assert_not_called()


class TestAPersonAlreadyInTheChannel(IntegrationTestCase):
	"""A department changed back, or a member added by hand: the second row is refused, so none is made."""

	def test_no_second_row_is_made(self):
		with patch.object(frappe.db, "exists", return_value=True) as exists:
			with patch.object(frappe, "get_doc") as get_doc:
				sync.create_channel_member("channel-sales", "raven-member", "HR-EMP-TEST-1717")

		exists.assert_called_once_with(
			"Raven Channel Member", {"channel_id": "channel-sales", "user_id": "raven-member"}
		)
		get_doc.assert_not_called()

	def test_a_new_member_is_made_as_before(self):
		with patch.object(frappe.db, "exists", return_value=False):
			with patch.object(frappe, "get_doc") as get_doc:
				sync.create_channel_member("channel-sales", "raven-member", "HR-EMP-TEST-1717")

		row = get_doc.call_args.args[0]
		self.assertEqual(
			(row["doctype"], row["channel_id"], row["user_id"], row["is_synced"]),
			("Raven Channel Member", "channel-sales", "raven-member", 1),
		)
		self.assertEqual(
			(row["linked_doctype"], row["linked_document"]), ("Employee", "HR-EMP-TEST-1717")
		)
		get_doc.return_value.insert.assert_called_once_with(ignore_permissions=True)
