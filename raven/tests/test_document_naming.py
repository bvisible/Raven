# //// Neoffice — added file (no upstream equivalent): the type of a linked document named in the reader's language,
# //// and whether its id means anything (raven.api.document_link.get_doctype_naming, 14.10.2026).
import frappe
from frappe.tests.utils import FrappeTestCase

from raven.api.document_link import get_doctype_naming


class TestDocumentNaming(FrappeTestCase):
	# Raven's own doctypes: their naming is Raven's JSON, which no other app's test rewrites (frappe's naming tests
	# change ToDo's autoname, and a site they ran on can keep it).

	def tearDown(self):
		frappe.local.lang = "en"
		frappe.set_user("Administrator")

	def test_the_type_is_named_in_the_readers_language(self):
		frappe.local.lang = "fr"
		self.assertEqual(get_doctype_naming("ToDo")["label"], frappe._("ToDo"))
		self.assertNotEqual(get_doctype_naming("ToDo")["label"], "ToDo")

	def test_a_hashed_id_is_said_random(self):
		self.assertTrue(get_doctype_naming("Raven Message")["random_id"])

	def test_a_random_naming_rule_without_autoname_is_said_random(self):
		self.assertIsNone(frappe.get_meta("Raven AI Pending Action").autoname)
		self.assertTrue(get_doctype_naming("Raven AI Pending Action")["random_id"])

	def test_an_id_people_chose_is_not_said_random(self):
		self.assertFalse(get_doctype_naming("Raven Workspace")["random_id"])

	def test_a_type_the_reader_may_not_read_is_refused(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_doctype_naming("Raven Message")
