import frappe


def after_uninstall():
	remove_standard_navbar_items()


def remove_standard_navbar_items():

	frappe.db.delete(
		"Navbar Item",
		# //// Neoffice - rebrand (1d6dea095, 2026-01-03 "feat: Rebrand app from Raven to Synk"): the navbar item is created with the new label.
		# //// TO REVIEW: an instance that installed the app before the rebrand has a "Raven" navbar item
		# //// that this uninstall no longer removes.
		{"item_label": "Synk", "is_standard": 1, "item_type": "Route", "route": "/raven"},
	)
	# This will run in a post uninstall hook hence needs to be committed manually
	frappe.db.commit()  # nosemgrep
