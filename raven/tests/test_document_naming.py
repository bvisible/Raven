# //// Neoffice — added file (no upstream equivalent): the type of a linked document named in the reader's language,
# //// and whether its id means anything (raven.api.document_link.get_doctype_naming, 14.10.2026).
import frappe
from frappe.tests.utils import FrappeTestCase

from raven.api.document_link import get_doctype_naming


class TestDocumentNaming(FrappeTestCase):
	def tearDown(self):
		frappe.local.lang = "en"
		frappe.set_user("Administrator")

	def test_the_type_is_named_in_the_readers_language(self):
		frappe.local.lang = "fr"
		self.assertEqual(get_doctype_naming("Project")["label"], frappe._("Project"))
		self.assertNotEqual(get_doctype_naming("Project")["label"], "Project")

	def test_a_hashed_id_is_said_random_and_a_numbered_one_is_not(self):
		self.assertTrue(get_doctype_naming("ToDo")["random_id"])
		self.assertFalse(get_doctype_naming("Sales Invoice")["random_id"])

	def test_a_type_the_reader_may_not_read_is_refused(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_doctype_naming("Sales Invoice")
