# //// Neoffice — added file (no upstream equivalent): a photo is an image by the extension of its name, whatever an
# //// app wrote into File.file_type (Suite's Drive writes « Image »), and the patch types the photos sent as files
# //// again (maintenance#1538).
import io
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from PIL import Image

from raven.api.upload_file import is_image_file
from raven.patches.neoffice import images_sent_as_files_are_images

# Its own user, created here and rolled back: the clone of a live site has none of the framework's test users.
TEST_USER = "raven-1538-test@example.com"


def png_bytes(width: int, height: int) -> bytes:
	buffer = io.BytesIO()
	Image.new("RGB", (width, height), "red").save(buffer, format="PNG")
	return buffer.getvalue()


class TestIsImageFile(IntegrationTestCase):
	def test_an_image_by_the_extension_of_its_name_whatever_the_case(self):
		for name in ("IMG_0004.jpeg", "photo.JPG", "/private/files/plan.png", "anim.gif", "x.WebP"):
			self.assertTrue(is_image_file(name), name)

	def test_anything_else_is_not(self):
		for name in (
			"devis.pdf",
			"notes.txt",
			"archive.tar.gz",
			"README",
			"",
			None,
			"/private/files/jpg",
		):
			self.assertFalse(is_image_file(name), name)


class TestImagesSentAsFilesAreImages(IntegrationTestCase):
	def setUp(self):
		# No e-mail leaves the run: the fork sends at once and commits, a rollback would not take it back.
		self.sendmail = patch("frappe.sendmail")
		self.sendmail.start()
		if not frappe.db.exists("User", TEST_USER):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": TEST_USER,
					"first_name": "Raven 1538 Test",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.get_doc("User", TEST_USER).add_roles("Raven User")
		# A workspace is an administrator's to make; the test user is put in it, then makes the channel.
		workspace = frappe.get_doc(
			{"doctype": "Raven Workspace", "workspace_name": "Images Test Workspace", "type": "Public"}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{"doctype": "Raven Workspace Member", "workspace": workspace.name, "user": TEST_USER}
		).insert(ignore_permissions=True)
		frappe.set_user(TEST_USER)
		self.channel = frappe.get_doc(
			{
				"doctype": "Raven Channel",
				"channel_name": "images-test-channel",
				"type": "Private",
				"workspace": workspace.name,
			}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		self.sendmail.stop()

	def _file_message(self, file_name: str, content: bytes):
		"""A message typed « File » the way the upload left it while Drive wrote its category into file_type."""
		message = frappe.get_doc(
			{
				"doctype": "Raven Message",
				"channel_id": self.channel.name,
				"message_type": "File",
				"content": file_name,
			}
		).insert()
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": file_name,
				"content": content,
				"is_private": 1,
				"attached_to_doctype": "Raven Message",
				"attached_to_name": message.name,
			}
		).insert()
		frappe.db.set_value("File", file_doc.name, "file_type", "Image", update_modified=False)
		message.db_set("file", file_doc.file_url, update_modified=False)
		return message

	def test_a_photo_sent_as_a_file_becomes_an_image_with_its_size_and_blurhash(self):
		message = self._file_message("photo-test-1538.png", png_bytes(64, 32))

		images_sent_as_files_are_images.execute()

		message.reload()
		self.assertEqual(message.message_type, "Image")
		# The sizes are Data fields of Raven Message: they come back as text.
		self.assertEqual((message.image_width, message.image_height), ("64", "32"))
		self.assertEqual((message.thumbnail_width, message.thumbnail_height), ("64", "32"))
		self.assertTrue(message.blurhash)

	def test_a_file_that_is_not_an_image_stays_a_file(self):
		message = self._file_message("devis-test-1538.txt", b"Devis du chantier")

		images_sent_as_files_are_images.execute()

		message.reload()
		self.assertEqual(message.message_type, "File")
