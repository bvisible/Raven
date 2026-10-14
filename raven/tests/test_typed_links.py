# //// Neoffice — added file (no upstream equivalent): an address typed in a message's words is one of its links, so
# //// that it gets its preview like an anchor does (raven_message.parse_html_content, 14.10.2026).
import frappe
from frappe.tests.utils import FrappeTestCase


class TestTypedLinks(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.get_doc("User", "test@example.com").add_roles("Raven User")
		frappe.set_user("test@example.com")
		suffix = frappe.generate_hash(length=8)
		cls.workspace = frappe.get_doc(
			{
				"doctype": "Raven Workspace",
				"workspace_name": f"Typed Links Workspace {suffix}",
				"type": "Public",
			}
		).insert()
		cls.channel = frappe.get_doc(
			{
				"doctype": "Raven Channel",
				"channel_name": f"typed-links-{suffix}",
				"type": "Private",
				"workspace": cls.workspace.name,
			}
		).insert()

	def setUp(self):
		frappe.set_user("test@example.com")

	def tearDown(self):
		frappe.set_user("Administrator")

	def message(self, text: str):
		return frappe.get_doc(
			{
				"doctype": "Raven Message",
				"channel_id": self.channel.name,
				"message_type": "Text",
				"text": text,
			}
		).insert()

	def test_an_address_typed_in_the_words_is_a_link(self):
		message = self.message("<p>Le plan est en ligne : https://neoffice.ch/plan.</p>")
		self.assertEqual([row.url for row in message.links_table], ["https://neoffice.ch/plan"])
		self.assertEqual(message.links_table[0].normalized_url, "https://neoffice.ch/plan")
		self.assertEqual(message.links.strip(), "https://neoffice.ch/plan")

	def test_an_anchor_is_not_listed_twice(self):
		message = self.message(
			'<p><a href="https://neoffice.ch">https://neoffice.ch</a> et https://example.com/a</p>'
		)
		self.assertEqual(
			[row.url for row in message.links_table], ["https://neoffice.ch", "https://example.com/a"]
		)

	def test_an_address_in_code_is_no_link(self):
		message = self.message("<p><code>curl https://example.com/api</code></p>")
		self.assertEqual(message.links_table, [])

	def test_an_edit_reads_its_typed_links_again(self):
		message = self.message("<p>https://example.com/one</p>")
		message.text = "<p>https://example.com/two</p>"
		message.save()
		message.reload()
		self.assertEqual([row.url for row in message.links_table], ["https://example.com/two"])
