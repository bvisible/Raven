# //// Neoffice — added file (no upstream equivalent): a person of the messaging is a member of every workspace anyone
# //// may join, from the day they get the messaging (Jérémy, 13.10.2026, « automatiquement », maintenance#1553). A
# //// workspace's channels show only to its members: on osiris, 51 of the 55 people of the messaging saw no channel at
# //// all, and a channel made from the phone stayed out of their sight. A private workspace, or one that asks for an
# //// invitation, stays as it is. Joining makes a member row and nothing else: a message notifies the members of its
# //// channel only (raven/notification.py).
import frappe

from raven.utils import delete_workspace_members_cache


def open_workspaces() -> list[str]:
	"""The workspaces anyone may join: public, and not « on invitation only »."""
	return frappe.get_all(
		"Raven Workspace",
		filters={"type": "Public", "can_only_join_via_invite": 0},
		pluck="name",
		order_by="creation asc",
	)


def join_open_workspaces(
	user: str, workspaces: list[str] | None = None, invalidate: bool = True
) -> list[str]:
	"""Puts the user in each open workspace they are not in yet; returns the workspaces joined."""
	joined = []
	for workspace in open_workspaces() if workspaces is None else workspaces:
		if frappe.db.exists("Raven Workspace Member", {"workspace": workspace, "user": user}):
			continue
		member = frappe.get_doc(
			{"doctype": "Raven Workspace Member", "workspace": workspace, "user": user}
		)
		member.flags.ignore_cache_invalidation = not invalidate
		# //// Neoffice - upstream 3.2 made (workspace, user) unique in the database: two processes that join the
		# //// same person at the same moment (an invitation and the account's own insert) both pass the check
		# //// above, and the second one hits the constraint. They are in the workspace either way.
		try:
			member.insert(ignore_permissions=True)
		except frappe.DuplicateEntryError:
			continue
		joined.append(workspace)
	return joined


def is_person_of_the_messaging(raven_user) -> bool:
	"""A person's account, enabled: not a bot."""
	return raven_user.type != "Bot" and bool(raven_user.user) and bool(raven_user.enabled)


def join_open_workspaces_on_insert(doc, method=None):
	"""Raven User after_insert: the person who just got the messaging joins the open workspaces."""
	if is_person_of_the_messaging(doc):
		join_open_workspaces(doc.name)


def join_everyone_once() -> dict[str, int]:
	"""Every person already in the messaging joins the open workspaces (the patch); returns the count per workspace."""
	workspaces = open_workspaces()
	if not workspaces:
		return {}
	counts = {workspace: 0 for workspace in workspaces}
	people = frappe.get_all(
		"Raven User", filters={"type": "User", "enabled": 1}, fields=["name", "type", "user", "enabled"]
	)
	for person in people:
		if not is_person_of_the_messaging(person):
			continue
		for workspace in join_open_workspaces(person.name, workspaces, invalidate=False):
			counts[workspace] += 1
	for workspace in workspaces:
		delete_workspace_members_cache(workspace)
	return counts
