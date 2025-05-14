import base64
import io
from mimetypes import guess_type

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
	fileExt = ["jpg", "JPG", "jpeg", "JPEG", "png", "PNG", "gif", "GIF", "webp", "WEBP"]
	thumbnailExt = ["jpg", "JPG", "jpeg", "JPEG", "png", "PNG"]

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

	# Check if a thread_message_id was provided (for attaching files to existing messages)
	thread_message_id = frappe.form_dict.get("thread_message_id")
	
	# Debug logging
	frappe.log_error("File upload", f"Upload file with parameters: {frappe.form_dict}")
	frappe.log_error("File upload", f"Thread message ID: {thread_message_id}")
	
	if thread_message_id and thread_message_id.strip():
		# Attach file to existing message instead of creating a new one
		# Get a fresh copy of the document to avoid timestamp mismatch
		message_doc = frappe.get_doc("Raven Message", thread_message_id)
		message_doc.message_type = "File" # Update to File type
		
		# Update caption if provided
		if frappe.form_dict.caption:
			message_doc.text = frappe.form_dict.caption
		else:
			# Get the filename as caption
			try:
				filename = frappe.request.files["file"].filename
			except Exception:
				filename = "File"
			message_doc.content = filename
			
		# Save changes to avoid race conditions
		try:
			# Set a flag to indicate this is not a new upload but an attachment to an existing message
			message_doc.flags.is_new_upload = False
			message_doc.save(ignore_version=True)
		except frappe.exceptions.TimestampMismatchError:
			# Get a fresh copy and retry
			frappe.log_error("File upload", "TimestampMismatchError occurred, retrying with fresh copy")
			message_doc = frappe.get_doc("Raven Message", thread_message_id)
			message_doc.message_type = "File"
			
			# Update caption if provided again
			if frappe.form_dict.caption:
				message_doc.text = frappe.form_dict.caption
			# Set a flag to indicate this is not a new upload but an attachment to an existing message
			message_doc.flags.is_new_upload = False
			message_doc.save(ignore_version=True, ignore_permissions=True)
	else:
		# Create a new message as usual
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
	
	# Force submission to RAG for file processing (important for AI search)
	try:
		# This is critical for ensuring file search works correctly with all files
		frappe.log_error("File upload RAG", f"Initiating direct RAG processing for: {file_doc.file_name}")
		
		# Get the file's physical path
		import os
		file_real_path = frappe.get_site_path(file_doc.file_url.lstrip("/")) if file_doc.file_url.startswith("/") else None
		
		if file_real_path and os.path.exists(file_real_path):
			# Import and process the file immediately
			from raven.ai.rag import process_uploaded_file_immediately
			
			frappe.log_error("File upload RAG", f"Processing file: {file_real_path}")
			
			# Process synchronously - this is important to ensure the file is available 
			# immediately for the next AI request
			result = process_uploaded_file_immediately(
				file_path=file_real_path,
				filename=file_doc.file_name,
				file_id=file_doc.name,
				channel_id=message_doc.channel_id
			)
			
			frappe.log_error("File upload RAG", f"Direct processing result: {result}")
			
			# Store the file ID for reference
			message_doc.file_processed_for_rag = 1
			message_doc.file_id_for_rag = file_doc.name
		else:
			frappe.log_error("File upload RAG", f"File not found at path: {file_real_path}")
	except Exception as e:
		frappe.log_error("File upload RAG", f"Error in RAG processing: {str(e)}")

	if file_doc.file_type in fileExt:

		message_doc.message_type = "Image"

		image, filename, extn = get_local_image(file_doc.file_url)
		width, height = image.size

		MAX_WIDTH = 480
		MAX_HEIGHT = 320

		# If it's a landscape image, then the thumbnail needs to be 480px wide
		if width > height:
			thumbnail_width = min(width, MAX_WIDTH)
			thumbnail_height = int(height * thumbnail_width / width)

		else:
			thumbnail_height = min(height, MAX_HEIGHT)
			thumbnail_width = int(width * thumbnail_height / height)

		# thumbnail_size = thumbnail_width, thumbnail_height

		# if extn in thumbnailExt:

		# TODO: Generate thumbnail of the image

		# Need to add a provision in Frappe to generate thumbnails for all images - not just public files
		# Generated thumbnail here throws a permissions error when trying to access.
		# thumbnail_url = f"{filename}_small.{extn}"

		# path = os.path.abspath(frappe.get_site_path(thumbnail_url.lstrip("/")))
		# image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

		# try:
		#     image.save(path)
		# except OSError:
		#     frappe.msgprint(_("Unable to write file format for {0}").format(path))
		#     thumbnail_url = file_doc.file_url

		message_doc.image_width = width
		message_doc.image_height = height
		# message_doc.file_thumbnail = thumbnail_url
		message_doc.thumbnail_width = thumbnail_width
		message_doc.thumbnail_height = thumbnail_height

	try:
		message_doc.save(ignore_version=True)
	except frappe.exceptions.TimestampMismatchError:
		# Get a fresh copy and retry
		frappe.log_error("File upload", "TimestampMismatchError occurred on final save, retrying with fresh copy")
		message_doc = frappe.get_doc("Raven Message", message_doc.name)
		
		# Set properties again
		message_doc.file = file_doc.file_url
		
		if file_doc.file_type in fileExt:
			message_doc.message_type = "Image"
			message_doc.image_width = width
			message_doc.image_height = height
			message_doc.thumbnail_width = thumbnail_width
			message_doc.thumbnail_height = thumbnail_height
			
		message_doc.save(ignore_version=True, ignore_permissions=True)

	return message_doc
