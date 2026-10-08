# //// Neoffice — added file (no upstream equivalent). System messages written before Raven v3 carry only their
# //// English text (« Daniel joined. »): no structured event, so the client can neither translate them nor follow a
# //// rename, and a French reader saw them in English (maintenance#1324). A join or a departure was written by the
# //// member themselves, so its owner says who it was; the patch gives those messages the event v3 writes.
import re

import frappe

EVENTS = (
	("user_joined", re.compile(r"^(?P<name>.+) joined\.$")),
	("user_left", re.compile(r"^(?P<name>.+) left\.$")),
)
NOBODY = {"Administrator", "Guest", None, ""}


def execute():
	rows = frappe.db.sql(
		"""
		SELECT name, channel_id, owner, text
		FROM `tabRaven Message`
		WHERE message_type = 'System'
			AND (json IS NULL OR json = '' OR json = '{}')
			AND (text LIKE %(joined)s OR text LIKE %(left)s)
		""",
		{"joined": "% joined.", "left": "% left."},
		as_dict=True,
	)
	for row in rows:
		found = _event(row)
		if found:
			frappe.db.set_value(
				"Raven Message", row.name, "json", frappe.as_json(found), update_modified=False
			)


def _event(row):
	text = (row.text or "").strip()
	for event, pattern in EVENTS:
		match = pattern.match(text)
		if match:
			user = _who(match.group("name"), row.owner, row.channel_id)
			return {"event": event, "user": user} if user else None
	return None


def _who(name, owner, channel_id):
	"""The member the text names, or else the one who wrote it: a member renamed since keeps their own message."""
	if owner not in NOBODY and name in _names(owner):
		return owner
	members = frappe.get_all(
		"Raven Channel Member", filters={"channel_id": channel_id}, pluck="user_id"
	)
	named = [member for member in members if name in _names(member)]
	if len(named) == 1:
		return named[0]
	return owner if owner not in NOBODY else None


def _names(user):
	raven = (
		frappe.db.get_value("Raven User", {"user": user}, ["full_name", "first_name"], as_dict=True)
		or {}
	)
	account = frappe.db.get_value("User", user, ["full_name", "first_name"], as_dict=True) or {}
	return {value for value in (*raven.values(), *account.values()) if value}
