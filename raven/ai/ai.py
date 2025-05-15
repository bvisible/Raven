import frappe
import asyncio

from raven.ai.sdk_handler import stream_response as sdk_stream_response
from raven.ai.sdk_agents import AGENTS_SDK_AVAILABLE
from raven.ai.handler import stream_response
from raven.ai.openai_client import (
	code_interpreter_file_types,
	file_search_file_types,
	get_open_ai_client,
)


def handle_bot_dm(message, bot):
	"""
	Function to handle direct messages to the bot.
	
	Creates a thread channel and processes the message with the SDK Agent.
	"""
	# If the message is a poll, send a message to the user that we don't support polls for AI yet
	if message.message_type == "Poll":
		bot.send_message(
			channel_id=message.channel_id,
			text="Sorry, I don't support polls yet. Please send a text message or file.",
		)
		return

	# Check if file search is enabled for file messages
	if message.message_type in ["File", "Image"]:
		if message.message_type == "File" and not check_if_bot_has_file_search(bot, message.channel_id):
			return

	# Create a thread channel for the conversation
	thread_channel = frappe.get_doc(
		{
			"doctype": "Raven Channel",
			"channel_name": message.name,
			"type": "Private",
			"is_thread": 1,
			"is_ai_thread": 1,
			"is_dm_thread": 1,
			"thread_bot": bot.name,
		}
	).insert()

	# Update the message to mark it as a thread
	message.is_thread = 1
	message.save(ignore_version=True)
	
	# Commit changes before processing the message
	frappe.db.commit()

	# Publish thinking state
	frappe.publish_realtime(
		"ai_event",
		{
			"text": "Raven AI is thinking...",
			"channel_id": thread_channel.name,
			"bot": bot.name,
		},
		doctype="Raven Channel",
		docname=thread_channel.name,
		after_commit=True,
	)

	# Check if the SDK is available
	if AGENTS_SDK_AVAILABLE:
		# Use SDK Agents for all models
		file_data = None
		if message.message_type in ["File", "Image"]:
			file_doc = frappe.get_doc("File", {"file_url": message.file})
			file_data = [{"file_path": file_doc.get_full_path(), "file_name": file_doc.file_name}]
		
		# Get response from SDK and send message
		response_text = asyncio.run(sdk_stream_response(
			bot=bot, 
			channel_id=thread_channel.name, 
			message=message.content,
			files=file_data
		))
		
		# Send the message if we got a response
		if response_text:
			bot.send_message(
				channel_id=thread_channel.name,
				text=response_text,
				markdown=True,
			)
	else:
		# SDK not available - inform the user
		bot.send_message(
			channel_id=thread_channel.name,
			text="OpenAI Agents SDK is not installed. Please run 'pip install openai-agents' on the server.",
		)

def handle_ai_thread_message(message, channel):
	"""
	Function to handle messages in an AI thread
	
	Processes the message using the SDK Agent.
	"""
	frappe.log_error("AI Thread Handler", f"Starting handle_ai_thread_message - Message type: {message.message_type}, Name: {message.name}")
	
	# Check if this message has already been processed to avoid duplicates
	# Use a database check to be persistent across requests
	processed_key = f"raven_ai_processed_{message.name}"
	if frappe.cache().get(processed_key):
		frappe.log_error("AI Thread Handler", f"Message {message.name} already processed, skipping")
		return
	
	# Mark this message as being processed for 60 seconds
	frappe.cache().setex(processed_key, 60, "true")
	
	# Get the bot for this thread
	bot = frappe.get_doc("Raven Bot", channel.thread_bot)

	# Check file search capability for file messages
	if message.message_type in ["File", "Image"] and message.message_type == "File":
		frappe.log_error("AI Thread Handler", f"File message detected - Checking bot file search capability")
		if not check_if_bot_has_file_search(bot, channel.name):
			frappe.log_error("AI Thread Handler", f"Bot does not have file search enabled, returning")
			return

	# For file messages, check if there was a text message just before that we should combine
	combined_message = message.content or ""
	file_data = None
	should_respond = True  # Flag to decide if we should respond
	
	if message.message_type in ["File", "Image"]:
		frappe.log_error("AI Thread Handler", f"Processing file message - File URL: {message.file}")
		
		file_doc = frappe.get_doc("File", {"file_url": message.file})
		file_path = file_doc.get_full_path()
		file_data = [{"file_path": file_path, "file_name": file_doc.file_name}]
		
		frappe.log_error("AI Thread Handler", f"File data prepared: {file_data}")
		
		# Check for recent text messages that might be related
		prev_messages = frappe.get_list(
			"Raven Message",
			filters={
				"channel_id": channel.name,
				"creation": ("<", message.creation),
				"message_type": "Text"
			},
			order_by="creation desc",
			limit=3  # Check last 3 messages
		)
		
		frappe.log_error("AI Thread Handler", f"Found {len(prev_messages)} previous text messages")
		
		for prev_msg in prev_messages:
			prev_message = frappe.get_doc("Raven Message", prev_msg)
			time_diff = (message.creation - prev_message.creation).total_seconds()
			
			# If the previous message is within 10 seconds and contains file-related keywords
			if time_diff < 10 and any(word in prev_message.content.lower() for word in ["facture", "invoice", "pdf", "document", "fichier", "upload", "total", "montant", "file", "cette", "this", "what"]):
				# Check if this text message was already processed
				if not frappe.cache().get(f"raven_ai_processed_{prev_message.name}"):
					combined_message = prev_message.content + "\n\n" + (message.content or f"[Uploaded file: {file_doc.file_name}]")
					frappe.log_error("AI Thread Handler", f"Combined with message {prev_message.name}: {combined_message}")
					
					# Mark the previous text message as processed
					frappe.cache().setex(f"raven_ai_processed_{prev_message.name}", 60, "true")
					break
		
		# If no combined message, use just the file info
		if not combined_message:
			combined_message = message.content or f"[Uploaded file: {file_doc.file_name}]"
	
	# For text messages, check if a file is coming immediately after
	elif message.message_type == "Text" and any(word in message.content.lower() for word in ["facture", "invoice", "pdf", "document", "fichier", "upload", "total", "montant", "file", "cette", "this", "what"]):
		frappe.log_error("AI Thread Handler", f"Text message with file keywords detected: {message.content}")
		
		# Wait up to 3 seconds for a file message
		import time
		max_wait = 3
		check_interval = 0.5
		waited = 0
		
		while waited < max_wait:
			time.sleep(check_interval)
			waited += check_interval
			
			# Check for file messages
			next_messages = frappe.get_list(
				"Raven Message",
				filters={
					"channel_id": channel.name,
					"creation": (">", message.creation),
					"message_type": ["in", ["File", "Image"]]
				},
				order_by="creation asc",
				limit=1
			)
			
			if next_messages:
				frappe.log_error("AI Thread Handler", f"File message found after {waited} seconds, delegating to file handler")
				should_respond = False
				break
		
		if should_respond:
			frappe.log_error("AI Thread Handler", f"No file message found after {max_wait} seconds, processing text alone")
	
	# If we should respond, process the message
	if should_respond:
		# Publish thinking state
		frappe.publish_realtime(
			"ai_event",
			{
				"text": "Raven AI is thinking...",
				"channel_id": channel.name,
				"bot": bot.name,
			},
			doctype="Raven Channel",
			docname=channel.name,
		)
	
		# Check if the SDK is available
		if AGENTS_SDK_AVAILABLE:
			frappe.log_error("AI Thread Handler", f"Calling SDK with message: {combined_message}, Files: {file_data}")
			
			# Get response from SDK and send message
			response_text = asyncio.run(sdk_stream_response(
				bot=bot, 
				channel_id=channel.name, 
				message=combined_message,
				files=file_data
			))
			
			frappe.log_error("AI Thread Handler", f"Got response from SDK: {response_text[:200] if response_text else 'None'}")
			
			# Send the message if we got a response
			if response_text:
				frappe.log_error("AI Thread Handler", f"Sending bot response")
				bot.send_message(
					channel_id=channel.name,
					text=response_text,
					markdown=True,
				)
			else:
				frappe.log_error("AI Thread Handler", f"No response from SDK")
		else:
			# SDK not available - inform the user
			frappe.log_error("AI Thread Handler", f"SDK not available")
			bot.send_message(
				channel_id=channel.name,
				text="OpenAI Agents SDK is not installed. Please run 'pip install openai-agents' on the server.",
			)
	else:
		frappe.log_error("AI Thread Handler", f"Not responding to this message, file handler will process it with context")


def check_if_bot_has_file_search(bot, channel_id):
	"""
	Checks if bot has file search. If not, send a message to the user. If yes, return True
	"""
	if not bot.enable_file_search:
		bot.send_message(
			channel_id=channel_id,
			text="Sorry, your bot does not support file search. Please enable it and try again.",
		)
		return False

	return True


def create_file_in_openai(file_url: str, message_type: str, client):
	"""
	Function to create a file in OpenAI

	We need to upload the file to OpenAI and return the file ID
	"""

	file_doc = frappe.get_doc("File", {"file_url": file_url})
	file_path = file_doc.get_full_path()

	file = client.files.create(
		file=open(file_path, "rb"), purpose="assistants" if message_type == "File" else "vision"
	)

	return file


def get_content_attachment_for_file(message_type: str, file_id: str, file_url: str):

	attachments = None

	if message_type == "File":
		content = f"Uploaded a file. URL of the file is '{file_url}'."

		file_extension = file_url.split(".")[-1].lower()

		if file_extension == "pdf":
			content += (
				" The file is a PDF. If it's not machine readable, you can extract the text via images."
			)

		attachments = []

		if file_extension in code_interpreter_file_types:
			attachments.append(
				{
					"file_id": file_id,
					"tools": [{"type": "code_interpreter"}],
				}
			)

		if file_extension in file_search_file_types:
			attachments.append(
				{
					"file_id": file_id,
					"tools": [{"type": "file_search"}],
				}
			)

	else:
		content = [
			{"type": "text", "text": f"Uploaded an image. URL of the image is '{file_url}'"},
			{"type": "image_file", "image_file": {"file_id": file_id}},
		]

	return content, attachments