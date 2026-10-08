# //// Neoffice — added file (no upstream equivalent). The accounts created before the 24-hour default
# //// (raven_user.json, 2026-09-22) kept upstream's 12-hour; /raven could not even read the preference until
# //// maintenance#1324, so nobody has seen it in effect. Our customers read a 24-hour clock.
import frappe


def execute():
	"""Move to the 24-hour clock every Raven User left on 12-hour whose language is not English.

	The account's language, or the site's when the account has none: English keeps 12 hours.
	"""
	site_language = frappe.db.get_single_value("System Settings", "language") or "en"
	rows = frappe.db.sql(
		"""
		SELECT ru.name, COALESCE(NULLIF(u.language, ''), %(site)s) AS language
		FROM `tabRaven User` ru
		LEFT JOIN `tabUser` u ON u.name = ru.user
		WHERE ru.time_format = '12-hour'
		""",
		{"site": site_language},
		as_dict=True,
	)
	names = [row.name for row in rows if not (row.language or "en").lower().startswith("en")]
	if names:
		frappe.db.sql(
			"UPDATE `tabRaven User` SET time_format = '24-hour' WHERE name IN %(names)s",
			{"names": tuple(names)},
		)
