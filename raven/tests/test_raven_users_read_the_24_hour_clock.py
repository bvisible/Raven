# //// Neoffice — added file (no upstream equivalent): the patch that moves the accounts left on upstream's
# //// 12-hour default to the 24-hour clock (maintenance#1324).
import frappe

# //// Neoffice - Frappe v15 has no frappe.tests.IntegrationTestCase (v16): its FrappeTestCase plays it.
try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	from frappe.tests.utils import FrappeTestCase as IntegrationTestCase

from raven.patches.neoffice.raven_users_read_the_24_hour_clock import execute

FRENCH = "raven-clock-fr@yopmail.com"
ENGLISH = "raven-clock-en@yopmail.com"


def _raven_user(email, language):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Raven clock",
				"language": language,
				"send_welcome_email": 0,
				"roles": [{"role": "Raven User"}],
			}
		).insert(ignore_permissions=True)
	name = frappe.db.get_value("Raven User", {"user": email})
	assert name, "the Raven User role did not create the Raven User"
	frappe.db.set_value("Raven User", name, "time_format", "12-hour")
	return name


class TestRavenUsersReadThe24HourClock(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.french = _raven_user(FRENCH, "fr")
		self.english = _raven_user(ENGLISH, "en")

	def test_an_account_left_on_upstreams_12_hour_default_reads_24_hours(self):
		execute()
		self.assertEqual(frappe.db.get_value("Raven User", self.french, "time_format"), "24-hour")

	def test_an_english_account_keeps_12_hours(self):
		execute()
		self.assertEqual(frappe.db.get_value("Raven User", self.english, "time_format"), "12-hour")
