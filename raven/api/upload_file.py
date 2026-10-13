import base64
import io
from mimetypes import guess_type

import blurhash
import frappe
from frappe import _
from frappe.core.doctype.file.utils import get_local_image
from frappe.handler import upload_file
from frappe.utils.image import optimize_image
from PIL import Image, ImageOps


def upload_JPEG_wrt_EXIF(content, filename, optimize=False):
	"""
	When a user uploads a JPEG file, we need to transpose the image based on the EXIF data.
	This is because the image is rotated when it is uploaded to the server.
	"""
	content_type = guess_type(filename)[0]

	# if file format is JPEG, we need to transpose the image
	if content_type.startswith("image/jpeg"):
		with Image.open(io.BytesIO(content)) as image:
			# transpose the image
			transposed_image = ImageOps.exif_transpose(image)
			#  convert the image to bytes
			buffer = io.BytesIO()
			# save the image to the buffer
			transposed_image.save(buffer, format="JPEG")
			# get the value of the buffer
			buffer = buffer.getvalue()
	else:
		buffer = base64.b64decode(content)

	if optimize:
		buffer = optimize_image(buffer, content_type)

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": buffer,
			"attached_to_doctype": "Raven Message",
			"attached_to_name": frappe.form_dict.docname,
			"is_private": 1,
			"attached_to_field": "file",
		}
	).insert()

	return file_doc


# //// Neoffice — added: an image is told by the extension of its name, not by File.file_type. An app that overrides
# //// File may write its own category there: Suite's Drive writes « Image » for every upload made outside Drive (its
# //// #638), which matched none of the extensions upstream compared it with, and every photo sent in a conversation
# //// became a « File » message, drawn as a file and left out of the channel's images (maintenance#1538).
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def is_image_file(file_name_or_url: str | None) -> bool:
	"""True for a file whose name ends with an image extension, whatever the case."""
	name = (file_name_or_url or "").rsplit("/", 1)[-1]
	return "." in name and name.rsplit(".", 1)[-1].lower() in IMAGE_EXTENSIONS


# //// Neoffice — upstream's image branch of upload_file_with_message, unchanged, moved into a function so that the
# //// patch raven.patches.neoffice.images_sent_as_files_are_images types the photos sent as files again with it.
def set_image_details(message_doc, file_url: str) -> None:
	"""Makes the message an image: its size, the size of its thumbnail and its blurhash."""
	message_doc.message_type = "Image"

	image, filename, extn = get_local_image(file_url)
	width, height = image.size

	MAX_WIDTH = 480
	MAX_HEIGHT = 320
	is_landscape = width > height

	# If it's a landscape image, then the thumbnail needs to be 480px wide
	if is_landscape:
		thumbnail_width = min(width, MAX_WIDTH)
		thumbnail_height = int(height * thumbnail_width / width)

	else:
		thumbnail_height = min(height, MAX_HEIGHT)
		thumbnail_width = int(width * thumbnail_height / height)

	image.thumbnail((thumbnail_width, thumbnail_height))

	x_components = 4 if is_landscape else 3
	y_components = 3 if is_landscape else 4

	blurhash_string = blurhash.encode(image, x_components=x_components, y_components=y_components)

	message_doc.blurhash = blurhash_string
	message_doc.image_width = width
	message_doc.image_height = height
	message_doc.thumbnail_width = thumbnail_width
	message_doc.thumbnail_height = thumbnail_height


@frappe.whitelist()
def upload_file_with_message():
	"""
	When the user uploads a file on Raven, this API is called.
	Along with the file, the user also send additional information: the channel ID
	We need to do two things:

	1. Create a Raven Message Doc
	2. Upload the file
	3. If the file is an image, we need to measure it's dimensions
	4. Store the file URL and the dimensions in the Raven Message Doc
	"""
	# //// Neoffice — the image extensions are IMAGE_EXTENSIONS, read from the file's name (is_image_file).

	frappe.form_dict.doctype = "Raven Message"
	frappe.form_dict.fieldname = "file"

	if (
		frappe.form_dict.compressImages == "1"
		or frappe.form_dict.compressImages == True
		or frappe.form_dict.compressImages == "true"
	):
		frappe.form_dict.optimize = True
	else:
		frappe.form_dict.optimize = False

	message_doc = frappe.new_doc("Raven Message")
	message_doc.channel_id = frappe.form_dict.channelID
	message_doc.message_type = "File"
	message_doc.text = frappe.form_dict.caption

	# If no caption is provided, use the filename as the caption
	if not frappe.form_dict.caption:
		# Get the filename
		try:
			filename = frappe.request.files["file"].filename
		except Exception:
			filename = "File"
		message_doc.content = filename

	message_doc.is_reply = frappe.form_dict.is_reply
	if message_doc.is_reply == "1" or message_doc.is_reply == 1:
		message_doc.linked_message = frappe.form_dict.linked_message

	message_doc.insert()

	frappe.form_dict.docname = message_doc.name

	# Get the files
	files = frappe.request.files
	# Get the file & content
	if "file" in files:
		file = files["file"]
		filename = file.filename
		"""
        If the file is a JPEG, we need to transpose the image
        Else, we need to upload the file as is
        """
		if filename.endswith(".jpeg") or filename.endswith(".jpg"):
			content = file.stream.read()
			file_doc = upload_JPEG_wrt_EXIF(content, filename, frappe.form_dict.optimize)
		else:
			file_doc = upload_file()

	message_doc.reload()

	message_doc.file = file_doc.file_url

	# //// Neoffice — by the name's extension (is_image_file), not by file_doc.file_type; the branch itself is
	# //// set_image_details, upstream's code. Its commented thumbnail sketch (« TODO: Generate thumbnail ») went with it.
	if is_image_file(file_doc.file_name or file_doc.file_url):
		set_image_details(message_doc, file_doc.file_url)

	# TODO (video dimensions): for video uploads, probe width/height here
	# (e.g. ffprobe / moviepy) and store them on image_width/image_height the
	# same way images do above. The web client (MessageVideo) already reserves
	# a box from stored dimensions when present — without them it auto-sizes and
	# reflows once when metadata loads, which can shift scroll position for a
	# video above the viewport during older-message pagination. Storing dims
	# makes inline video height deterministic (and correct for portrait clips).

	message_doc.save()

	return message_doc
