# //// Neoffice — added file (no upstream equivalent). The product ships as Synk, and the
# //// workspace upstream creates is literally named "Raven" (patches/v2_0/create_default_workspace.py,
# //// which we also changed). That name is what every user reads in the workspace switcher.
import frappe

OLD_NAME = "Raven"
NEW_NAME = "Synk"


def execute():
	"""Rename the default workspace from Raven to Synk on existing sites.

	`Raven Workspace` uses `autoname: field:workspace_name`, so the record's name IS the label:
	writing the field would be silently reset at save, and the channels that point at it through
	`Raven Channel.workspace` would keep the old target. Only `rename_doc` does the job, and it
	updates the links for us.

	Idempotent and defensive on purpose: this runs on every instance of the fleet, some of which
	may already have been renamed by hand, renamed to something else entirely, or may carry a
	real workspace already called Synk.
	"""
	if not frappe.db.exists("Raven Workspace", OLD_NAME):
		return

	if frappe.db.exists("Raven Workspace", NEW_NAME):
		# Both exist: merging two workspaces moves channels and memberships around and is not a
		# decision a patch gets to make silently. Leave it to a human.
		frappe.log_error(
			"Synk rename skipped",
			f"Both '{OLD_NAME}' and '{NEW_NAME}' workspaces exist on this site. "
			f"The rename was skipped so no channel is moved without a decision.",
		)
		return

	frappe.rename_doc("Raven Workspace", OLD_NAME, NEW_NAME, force=True, show_alert=False)
	frappe.db.commit()
