# //// Neoffice — added file (no upstream equivalent): the people already in the messaging join, once, the workspaces
# //// anyone may join (public, not « on invitation only »), as a person who gets the messaging now does on the day
# //// (raven/open_workspaces.py, maintenance#1553). Nobody is added twice; a private workspace is not touched.
import frappe

from raven.open_workspaces import join_everyone_once


def execute():
	if not frappe.db.table_exists("Raven Workspace Member"):
		return
	join_everyone_once()
