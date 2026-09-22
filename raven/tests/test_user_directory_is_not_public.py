# //// Neoffice — added file (no upstream equivalent).
# ////
# //// THE USER DIRECTORY, AND WHO MAY ENUMERATE IT.
# ////
# //// Upstream's `raven_user_has_permission` answers True to any read, which is
# //// right for a team messenger: colleagues see each other. What it does not
# //// cover is a LIST — `get_list` never consults `has_permission` — and there
# //// was no `permission_query_conditions` on the doctype, so a list came back
# //// whole: every name and e-mail address on the instance.
# ////
# //// That only bites because we give the role to accounts upstream never
# //// imagined: portal customers. So this file pins the line rather than the
# //// mechanism — a colleague still sees everyone, a customer sees only what a
# //// conversation needs. Both directions are tested, because a fix that hid
# //// the directory from staff would break the messenger instead of securing it.

import frappe
from frappe.tests import IntegrationTestCase

from raven.api.raven_users import get_list
from raven.permissions import is_portal_account, raven_users_visible_to

EXTRA_TEST_RECORD_DEPENDENCIES = ["User", "Raven User"]

COLLEAGUE = "raven-dir-staff@yopmail.com"
CUSTOMER = "raven-dir-portal@yopmail.com"
STRANGER = "raven-dir-stranger@yopmail.com"


def _user(email, user_type):
	if not frappe.db.exists("User", email):
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"user_type": user_type,
				"send_welcome_email": 0,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
	doc = frappe.get_doc("User", email)
	wanted = ["Raven User"]
	#: 🔴 `user_type` is DERIVED from the roles, not from what we declared
	#: above: a user holding only "Raven User" is stored as a Website User on
	#: every instance where that role does not open the desk — which is ours,
	#: deliberately. Declaring "System User" and stopping there produced a
	#: fixture that was a customer, so the half this file exists to protect
	#: passed for the wrong reason.
	if user_type == "System User":
		wanted.append("System Manager")
	have = {r.role for r in doc.roles}
	for role in wanted:
		if role not in have:
			doc.append("roles", {"role": role})
	doc.save(ignore_permissions=True)
	if not frappe.db.exists("Raven User", {"user": email}):
		frappe.get_doc({"doctype": "Raven User", "user": email, "type": "User"}).insert(
			ignore_permissions=True
		)
	return email


class TestUserDirectoryIsNotPublic(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		for email, kind in (
			(COLLEAGUE, "System User"),
			(CUSTOMER, "Website User"),
			(STRANGER, "Website User"),
		):
			_user(email, kind)
		frappe.db.commit()
		frappe.clear_cache()

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	# ------------------------------------------------------- what it must keep
	def test_a_colleague_still_sees_the_whole_directory(self):
		"""🔴 The half that a careless fix breaks: this is a team messenger."""
		frappe.set_user("Administrator")
		everyone = frappe.db.count("Raven User")
		frappe.set_user(COLLEAGUE)
		try:
			self.assertFalse(is_portal_account(COLLEAGUE))
			seen = frappe.get_list("Raven User", limit_page_length=0, ignore_permissions=False)
			#: Administrator is hidden from the app's own endpoint, not from the
			#: doctype, so the list is the whole table for a colleague.
			self.assertEqual(len(seen), everyone)
		finally:
			frappe.set_user("Administrator")

	# --------------------------------------------------- what it must refuse
	def test_a_portal_account_cannot_enumerate_the_directory(self):
		"""A customer sees themselves, the bots, and nobody they never spoke to."""
		frappe.set_user(CUSTOMER)
		try:
			self.assertTrue(is_portal_account(CUSTOMER))
			seen = {
				r.name for r in frappe.get_list("Raven User", limit_page_length=0, ignore_permissions=False)
			}
			self.assertIn(CUSTOMER, seen)
			self.assertNotIn(COLLEAGUE, seen, "a customer must not read a colleague out of the directory")
			self.assertNotIn(STRANGER, seen, "nor another customer")
		finally:
			frappe.set_user("Administrator")

	def test_the_apps_own_endpoint_is_filtered_too(self):
		"""🔴 The path the SPA actually uses, and the one a query condition misses.

		`raven.api.raven_users.get_list` calls `frappe.db.get_all`, which consults
		neither permission layer. Fixing only the REST path would have left the
		real door open while the audit looked green.
		"""
		frappe.set_user(CUSTOMER)
		try:
			names = {u["name"] for u in get_list()}
			self.assertIn(CUSTOMER, names)
			self.assertNotIn(COLLEAGUE, names)
			self.assertNotIn(STRANGER, names)
		finally:
			frappe.set_user("Administrator")

		frappe.set_user(COLLEAGUE)
		try:
			names = {u["name"] for u in get_list()}
			self.assertIn(CUSTOMER, names, "a colleague still gets upstream's list")
			self.assertIn(STRANGER, names)
		finally:
			frappe.set_user("Administrator")

	def test_two_identities_in_a_row_do_not_share_one_cached_answer(self):
		"""🔴 The trap a future merge will walk into.

		`get_users()` is `@redis_cache()`d on NO argument, so its key does not
		carry the caller. Filter inside it and the first caller decides for
		everyone: a colleague who opens the directory first would serve their
		whole list to the next portal account, and nothing would look wrong —
		the number is plausible. The filter therefore lives in `get_list`,
		BEFORE the cached call, and this test is what says so.

		Two identities, back to back, in the same process.
		"""
		frappe.set_user(COLLEAGUE)
		try:
			staff_first = {u["name"] for u in get_list()}
		finally:
			frappe.set_user("Administrator")
		frappe.set_user(CUSTOMER)
		try:
			portal_after = {u["name"] for u in get_list()}
		finally:
			frappe.set_user("Administrator")
		self.assertNotEqual(
			len(staff_first),
			len(portal_after),
			"the portal account was served the colleague's cached list",
		)
		self.assertNotIn(COLLEAGUE, portal_after)

		#: And the other way round, because a cache poisoned by the portal
		#: account would shrink the directory for staff instead of widening it.
		frappe.set_user(CUSTOMER)
		try:
			get_list()
		finally:
			frappe.set_user("Administrator")
		frappe.set_user(COLLEAGUE)
		try:
			staff_after = {u["name"] for u in get_list()}
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(staff_first, staff_after, "the colleague lost rows to a portal call")

	def test_the_guard_holds_when_its_own_role_opens_the_desk(self):
		"""🔴 The silent failure this guard would otherwise have.

		Nothing here ships a `Role` document, so frappe auto-creates "Raven
		User" with `desk_access = 1` on a fresh site. `user_type` is derived
		from the roles, so holding it would promote a customer to System User
		— and a filter that keys on `user_type` would stop applying to exactly
		the accounts it exists for, with the directory looking perfectly
		normal. An instance that set `desk_access = 0` by hand is protected;
		one that never did is not, and the difference is invisible.
		"""
		before = frappe.db.get_value("Role", "Raven User", "desk_access")
		frappe.db.set_value("Role", "Raven User", "desk_access", 1)
		frappe.clear_cache()
		try:
			#: 🔴 The account is made AFTER the flip, which is the whole point.
			#: Flipping it around an account created while the role was still
			#: closed proves nothing: the promotion never happens, `Desk User`
			#: is never granted, and the test passes on a scenario that cannot
			#: occur. The real one is a fresh instance where the role already
			#: opens the desk when the customer is added to the messenger.
			late = _user("raven-dir-portal-late@yopmail.com", "Website User")
			frappe.db.commit()
			self.assertIn("Desk User", frappe.get_roles(late), "frappe promoted them, as it does")
			self.assertTrue(
				is_portal_account(late),
				"a promoted customer is still a customer: Desk User must not answer for the role",
			)
			self.assertTrue(
				is_portal_account(CUSTOMER),
				"the role opening the desk must not turn a customer into a colleague",
			)
			frappe.set_user(CUSTOMER)
			try:
				names = {u["name"] for u in get_list()}
			finally:
				frappe.set_user("Administrator")
			self.assertNotIn(COLLEAGUE, names)
		finally:
			frappe.db.set_value("Role", "Raven User", "desk_access", before)
			frappe.clear_cache()

	def test_a_bot_stays_visible_so_a_conversation_still_renders(self):
		"""Hiding the peer would leave a customer writing to a blank name."""
		if not frappe.db.exists("Raven User", {"type": "Bot"}):
			self.skipTest("no bot on this site")
		bot = frappe.db.get_value("Raven User", {"type": "Bot"}, "name")
		self.assertIn(bot, raven_users_visible_to(CUSTOMER))
