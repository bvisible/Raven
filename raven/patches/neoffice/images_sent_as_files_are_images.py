# //// Neoffice — added file (no upstream equivalent): the photos sent as « File » messages while Suite's Drive wrote
# //// « Image » into File.file_type (its #638), which the upload compared with extensions: typed « Image » again, with
# //// their size, the size of their thumbnail and their blurhash, so that a conversation draws them as photos and the
# //// channel's images list them (maintenance#1538).
import frappe

from raven.api.upload_file import is_image_file, set_image_details

# Suite's #638 is of 14.08.2026: nothing before can have been typed wrong this way.
SINCE = "2026-08-01"


def execute():
	rows = frappe.get_all(
		"Raven Message",
		filters={"message_type": "File", "file": ["is", "set"], "creation": [">=", SINCE]},
		fields=["name", "file"],
	)
	for row in rows:
		if not is_image_file(row.file):
			continue
		try:
			message = frappe.get_doc("Raven Message", row.name)
			set_image_details(message, message.file)
			# The fields only: no hook, no notification, no realtime event for a message sent long ago.
			message.db_update()
		except Exception:
			frappe.log_error(
				"Raven: a photo sent as a file could not be typed as an image", frappe.get_traceback()
			)
