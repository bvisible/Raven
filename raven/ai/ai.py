import frappe

# Import agents integration - no fallback needed
from raven.ai.agents_integration import handle_ai_request_sync
from raven.ai.google_ai import run_document_ai_processor

# Keep old handler import for fallback
from raven.ai.handler import stream_response
from raven.ai.openai_client import (
	code_interpreter_file_types,
	file_search_file_types,
	get_open_ai_client,
)


def handle_bot_dm(message, bot):
	"""
	Function to handle direct messages to the bot.

	#//// Neoffice - Nora as a model provider (6375b651f, 2026-01-04 "feat: Add Nora as model provider option").
	Routes to:
	- Nora handler for bots with model_provider="Nora"
	- Agents SDK for bots with model_provider in ["OpenAI", "Local LLM"]
	- Assistants API for legacy bots with openai_assistant_id
	"""

	# //// Neoffice - Nora as a model provider (6375b651f, 2026-01-04 "feat: Add Nora as model provider option"). Upstream knows OpenAI and
	# //// "Local LLM"; a Neoffice bot can instead delegate the whole turn to NORA, which owns the
	# //// prompt, the RAG and the ERP tools. Raven then only stores and renders the messages.
	# Check if bot uses Nora integration
	if bot.model_provider == "Nora":
		return handle_bot_dm_with_nora(message, bot)
	# Check if bot uses new Agents SDK
	# //// Neoffice - if -> elif, because the Nora branch above now comes first (6375b651f, 2026-01-04 "feat: Add Nora as model provider option").
	elif bot.model_provider in ["OpenAI", "Local LLM"] and not bot.openai_assistant_id:
		return handle_bot_dm_with_agents(message, bot)
	else:
		# Use old Assistants API for legacy bots
		return handle_bot_dm_with_assistants(message, bot)


# //// Neoffice - Nora DM handler (6375b651f, 2026-01-04 "feat: Add Nora as model provider option"): hands the message to NORA and lets it
# //// answer in the thread. No upstream equivalent.
def handle_bot_dm_with_nora(message, bot):
	"""
	Handle direct messages using NORA AI engine.

	Routes all AI processing (prompt, RAG, code execution) to Nora.
	Raven only handles the chat UI and message storage.
	"""

	# If the message is a poll, send a message to the user that we don't support polls for AI yet
	if message.message_type == "Poll":
		bot.send_message(
			channel_id=message.channel_id,
			text="Sorry, I don't support polls yet. Please send a text message or file.",
		)
		return

	# Create thread channel for the conversation FIRST (or get existing one)
	if frappe.db.exists("Raven Channel", message.name):
		thread_channel = frappe.get_doc("Raven Channel", message.name)
		# Ensure it has the correct AI thread settings
		if not thread_channel.is_ai_thread:
			thread_channel.is_ai_thread = 1
			thread_channel.is_dm_thread = 1
			thread_channel.thread_bot = bot.name
			thread_channel.save()
	else:
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
	message.save()
	# Manual commit required: AI processing happens in background job that needs the message to exist in DB
	frappe.db.commit()  # nosemgrep

	# Send event to open the thread FIRST
	publish_ai_thread_created_event(message, message.channel_id)

	# Send thinking message for new DM threads
	frappe.publish_realtime(
		"ai_event",
		{
			"text": "Nora is thinking...",
			"channel_id": message.name,  # For new DM threads, use the message ID
			"bot": bot.name,
		},
		user=message.owner,
		after_commit=False,
	)

	# Process message with Nora
	process_message_with_nora(
		message=message,
		bot=bot,
		channel_id=thread_channel.name,
		is_new_conversation=True,
		thread_message_id=message.name,
	)


def handle_bot_dm_with_agents(message, bot):
	"""
	Handle direct messages using Agents SDK.
	"""

	# If the message is a poll, send a message to the user that we don't support polls for AI yet
	if message.message_type == "Poll":
		bot.send_message(
			channel_id=message.channel_id,
			text="Sorry, I don't support polls yet. Please send a text message or file.",
		)
		return

	# //// Neoffice - fd5440747, 2026-02-17 "fix: prevent DuplicateEntryError when thread channel already exists". Upstream always inserts a new Raven Channel named after
	# //// the message; when the same message is processed twice (a retry, a double realtime event) the
	# //// insert raised DuplicateEntryError and the whole answer was lost. Reuse the existing channel
	# //// and repair its AI-thread flags instead.
	# Create thread channel for the conversation FIRST (or get existing one)
	if frappe.db.exists("Raven Channel", message.name):
		thread_channel = frappe.get_doc("Raven Channel", message.name)
		# Ensure it has the correct AI thread settings
		if not thread_channel.is_ai_thread:
			thread_channel.is_ai_thread = 1
			thread_channel.is_dm_thread = 1
			thread_channel.thread_bot = bot.name
			thread_channel.save()
	else:
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
	message.save()
	# We need to commit here since the response will be processed asynchronously
	# Manual commit required: AI processing happens in background job that needs the message to exist in DB
	frappe.db.commit()  # nosemgrep

	# //// Neoffice - the thread-created event is published BEFORE the thinking message (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
	# //// The client opens the thread on that event; publishing the thinking message first sent it to a
	# //// screen nobody was looking at yet, so the user stared at an empty thread.
	# Send event to open the thread FIRST
	publish_ai_thread_created_event(message, message.channel_id)

	# Send thinking message for new DM threads
	frappe.publish_realtime(
		"ai_event",
		{
			# //// Neoffice - the assistant is called Nora here, not "Raven AI" (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"); and the
			# //// event is addressed with the parent message id, which is what the client subscribes to for a
			# //// brand-new DM thread.
			"text": "Nora is thinking...",
			"channel_id": message.name,  # For new DM threads, use the message ID
			"bot": bot.name,
		},
		# //// Neoffice - the event is sent to the USER rather than broadcast on the Raven Channel document
		# //// (5a7db4919, 2025-08-07 "fix: Add room parameter to publish_realtime to avoid broadcasting to all users"), and without after_commit so it arrives while the answer is still
		# //// being computed - that is the whole point of a "thinking" indicator.
		user=message.owner,
		after_commit=False,
	)
	# //// Neoffice - moved above, before the thinking message (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").

	# Process message with Agents SDK
	# Pass both thread channel ID and message ID for proper event handling
	process_message_with_agent(
		# //// Neoffice - thread_message_id is threaded through so the "stop thinking" event can be
		# //// addressed to the same id the client subscribed to (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
		message=message,
		bot=bot,
		channel_id=thread_channel.name,
		is_new_conversation=True,
		thread_message_id=message.name,
	)


def handle_bot_dm_with_assistants(message, bot):
	"""
	Legacy function to handle direct messages using OpenAI Assistants API.
	"""

	client = get_open_ai_client()

	# If the message is a poll, send a message to the user that we don't support polls for AI yet
	if message.message_type == "Poll":
		bot.send_message(
			channel_id=message.channel_id,
			text="Sorry, I don't support polls yet. Please send a text message or file.",
		)
		return

	if message.message_type in ["File", "Image"]:

		if message.message_type == "File" and not check_if_bot_has_file_search(bot, message.channel_id):
			return

		# If the file has an "fid" query parameter, we need to remove that from the file_url
		if "fid" in message.file:
			file_url = message.file.split("?fid=")[0]
		else:
			file_url = message.file

		# Upload the file to OpenAI
		file = create_file_in_openai(file_url, message.message_type, client)

		content, attachments = get_content_attachment_for_file(
			message.message_type, file.id, file_url, bot
		)

		ai_thread = client.beta.threads.create(
			messages=[
				{
					"role": "user",
					"content": content,
					"metadata": {"user": message.owner, "message": message.name},
					"attachments": attachments,
				}
			],
			metadata={
				"bot": bot.name,
				"channel": message.channel_id,
				"user": message.owner,
				"message": message.name,
			},
		)

	else:
		ai_thread = client.beta.threads.create(
			messages=[
				{
					"role": "user",
					"content": message.content,
					"metadata": {"user": message.owner, "message": message.name},
				}
			],
			metadata={
				"bot": bot.name,
				"channel": message.channel_id,
				"user": message.owner,
				"message": message.name,
			},
		)

	# //// Neoffice - fd5440747, 2026-02-17 "fix: prevent DuplicateEntryError when thread channel already exists", same reuse as in the DM path above.
	# Create thread channel or get existing one to avoid DuplicateEntryError
	if frappe.db.exists("Raven Channel", message.name):
		thread_channel = frappe.get_doc("Raven Channel", message.name)
		# Ensure it has the correct AI thread settings
		if not thread_channel.is_ai_thread or not thread_channel.openai_thread_id:
			thread_channel.is_ai_thread = 1
			thread_channel.is_dm_thread = 1
			thread_channel.thread_bot = bot.name
			thread_channel.openai_thread_id = ai_thread.id
			thread_channel.save()
	else:
		thread_channel = frappe.get_doc(
			{
				"doctype": "Raven Channel",
				"channel_name": message.name,
				"type": "Private",
				"is_thread": 1,
				"is_ai_thread": 1,
				"is_dm_thread": 1,
				"openai_thread_id": ai_thread.id,
				"thread_bot": bot.name,
			}
		).insert()

	# Update the message to mark it as a thread
	message.is_thread = 1
	message.save()
	# nosemgrep We need to commit here since the response will be streamed, and hence might take a while
	frappe.db.commit()

	# //// Neoffice - the thinking message moves after the thread-created event here too (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
	# Send event to open the thread
	publish_ai_thread_created_event(message, message.channel_id)

	# Note: The thinking message is already sent from raven_message.py before enqueueing

	stream_response(ai_thread_id=ai_thread.id, bot=bot, channel_id=thread_channel.name)


def handle_ai_thread_message(message, channel):
	"""
	Function to handle messages in an AI thread.

	#//// Neoffice - Nora as a model provider (6375b651f, 2026-01-04 "feat: Add Nora as model provider option"), thread path.
	Routes to:
	- Nora handler for bots with model_provider="Nora"
	- Agents SDK for bots with model_provider in ["OpenAI", "Local LLM"]
	- Assistants API for legacy bots with openai_assistant_id
	"""

	bot = frappe.get_cached_doc("Raven Bot", channel.thread_bot)

	# //// Neoffice - Nora as a model provider (6375b651f, 2026-01-04 "feat: Add Nora as model provider option"), thread path.
	# Check if bot uses Nora integration
	if bot.model_provider == "Nora":
		return handle_ai_thread_message_with_nora(message, channel, bot)
	# Check if bot uses new Agents SDK
	# //// Neoffice - if -> elif, because the Nora branch above now comes first (6375b651f, 2026-01-04 "feat: Add Nora as model provider option").
	elif bot.model_provider in ["OpenAI", "Local LLM"] and not bot.openai_assistant_id:
		return handle_ai_thread_message_with_agents(message, channel, bot)
	else:
		# Use old Assistants API for legacy bots
		return handle_ai_thread_message_with_assistants(message, channel, bot)


# //// Neoffice - Nora thread handler (6375b651f, 2026-01-04 "feat: Add Nora as model provider option"). No upstream equivalent.
def handle_ai_thread_message_with_nora(message, channel, bot):
	"""
	Handle thread messages using NORA AI engine.
	"""

	# Skip file/image messages without text - they'll be handled when the user sends a follow-up
	if message.message_type in ["File", "Image"] and not message.text and not message.content:
		return

	# Send thinking message for existing threads
	frappe.publish_realtime(
		"ai_event",
		{
			"text": "Nora is thinking...",
			"channel_id": channel.channel_name,
			"bot": bot.name,
		},
		user=message.owner,
		after_commit=False,
	)

	# Process message with Nora
	process_message_with_nora(
		message=message, bot=bot, channel_id=channel.name, is_new_conversation=False, channel=channel
	)


def handle_ai_thread_message_with_agents(message, channel, bot):
	"""
	Handle thread messages using Agents SDK.
	"""

	# Skip file/image messages without text - they'll be handled when the user sends a follow-up
	# //// Neoffice - TO REVIEW - SILENT FAILURE: upstream logs the skipped file-only message; that log
	# //// is gone (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
	if message.message_type in ["File", "Image"] and not message.text and not message.content:
		return

	# Send thinking message for existing threads
	# We need to use channel.channel_name which is the thread ID that frontend expects
	frappe.publish_realtime(
		"ai_event",
		{
			# //// Neoffice - "Nora is thinking...", addressed with channel_name (the parent message id the
			# //// client listens on), not the channel document name (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
			"text": "Nora is thinking...",
			"channel_id": channel.channel_name,  # This is the thread message ID that frontend uses
			"bot": bot.name,
		},
		# //// Neoffice - user-addressed, immediate event (5a7db4919, 2025-08-07 "fix: Add room parameter to publish_realtime to avoid broadcasting to all users"), as in the DM path.
		user=message.owner,
		after_commit=False,
	)

	# Process message with Agents SDK
	process_message_with_agent(
		message=message, bot=bot, channel_id=channel.name, is_new_conversation=False, channel=channel
	)


def handle_ai_thread_message_with_assistants(message, channel, bot):
	"""
	Legacy function to handle thread messages using OpenAI Assistants API.
	"""

	client = get_open_ai_client()

	if message.message_type in ["File", "Image"]:

		file_url = message.file
		if "fid" in file_url:
			file_url = file_url.split("?fid=")[0]

		if message.message_type == "File" and not check_if_bot_has_file_search(bot, channel.name):
			return
		# Upload the file to OpenAI
		try:
			file = create_file_in_openai(file_url, message.message_type, client)
		except Exception as e:
			frappe.log_error("Raven AI Error", frappe.get_traceback())
			bot.send_message(
				channel_id=channel.name,
				text="Sorry, there was an error in processing your file. Please try again.<br/><br/>Error: "
				+ str(e),
			)
			return

		content, attachments = get_content_attachment_for_file(
			message.message_type, file.id, file_url, bot
		)

		try:
			client.beta.threads.messages.create(
				thread_id=channel.openai_thread_id,
				role="user",
				content=content,
				metadata={"user": message.owner, "message": message.name},
				attachments=attachments,
			)
		except Exception as e:
			frappe.log_error("Raven AI Error", frappe.get_traceback())
			bot.send_message(
				channel_id=channel.name,
				text="Sorry, there was an error in processing your file. Please try again.<br/><br/>Error: "
				+ str(e),
			)
			return

	else:

		client.beta.threads.messages.create(
			thread_id=channel.openai_thread_id,
			role="user",
			content=message.content,
			metadata={"user": message.owner, "message": message.name},
		)

	# Send thinking message for existing threads with Assistants API
	frappe.publish_realtime(
		"ai_event",
		{
			# //// Neoffice - same thinking message and addressing, third call site (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
			"text": "Nora is thinking...",
			"channel_id": channel.channel_name,  # This is the thread message ID that frontend uses
			"bot": bot.name,
		},
		# //// Neoffice - user-addressed, immediate event (5a7db4919, 2025-08-07 "fix: Add room parameter to publish_realtime to avoid broadcasting to all users"), third call site.
		user=message.owner,
		after_commit=False,
	)

	stream_response(ai_thread_id=channel.openai_thread_id, bot=bot, channel_id=channel.name)


def extract_file_content_for_agent(file_url: str, file_extension: str, bot, file_handler):
	"""
	Extract content from a file for agent processing.

	Tries Google Document AI first if enabled, falls back to basic extraction.
	"""
	extracted_content = ""

	# Try Google Document AI first if enabled
	if hasattr(bot, "use_google_document_parser") and bot.use_google_document_parser:
		if hasattr(bot, "google_document_processor_id") and bot.google_document_processor_id:
			if file_extension in ["jpg", "jpeg", "png", "pdf"]:
				try:
					extracted_content = run_document_ai_processor(
						bot.google_document_processor_id, file_url, file_extension
					)
					if extracted_content:
						return extracted_content
				except Exception as e:
					frappe.log_error(
						f"Error extracting content with Google Document AI: {str(e)}\nFile: {file_url}",
						"Google Document AI Error",
					)

	# Fallback to basic extraction
	if not extracted_content:
		try:
			file_doc = frappe.get_doc("File", {"file_url": file_url})
			file_path = file_doc.get_full_path()

			if file_extension == "pdf":
				extracted_content = file_handler._extract_pdf_content(file_path)
			elif file_extension in ["txt", "md", "json"]:
				with open(file_path, encoding="utf-8") as f:
					extracted_content = f.read()
			elif file_extension in ["xlsx", "xls", "csv"]:
				extracted_content = file_handler._convert_spreadsheet_to_markdown(file_path, file_extension)
			# For images, return empty - Google AI should handle them

		except Exception as e:
			frappe.log_error(
				f"Error extracting file content: {str(e)}\nFile: {file_url}", "File Extraction Error"
			)

	return extracted_content


def process_message_with_agent(
	# //// Neoffice - thread_message_id added (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"): see L166.
	message, bot, channel_id: str, is_new_conversation: bool, channel=None, thread_message_id=None
):
	"""
	Process a message using the Agents SDK.

	This function handles both new conversations and existing threads.
	"""

	# Track files in conversation
	from raven.ai.conversation_file_handler import ConversationFileHandler

	file_handler = ConversationFileHandler(channel_id=channel_id, bot=bot)

	# Check if this is a text message following a recent file upload
	# to combine them into a single AI request
	recent_file_message = None
	if message.message_type == "Text" and channel:
		# Look for a file message from the same user in the last 30 seconds
		from datetime import datetime, timedelta

		cutoff_time = datetime.now() - timedelta(seconds=30)

		recent_messages = frappe.get_all(
			"Raven Message",
			filters={
				"channel_id": channel.name,
				"owner": message.owner,
				"message_type": ["in", ["File", "Image"]],
				"creation": [">", cutoff_time],
				"is_bot_message": 0,
			},
			fields=["name", "file", "message_type", "text", "content"],
			order_by="creation desc",
			limit=1,
		)

		if recent_messages:
			recent_file = recent_messages[0]
			# Check if the file message had no text
			if not recent_file.text and not recent_file.content:
				recent_file_message = recent_file
				# Add this file to the file handler
				file_handler.add_conversation_file(recent_file)

	# Prepare the message content
	if message.message_type in ["File", "Image"]:
		# Add file to conversation context
		file_handler.add_conversation_file(message)

		# If it's just a file upload without any text, don't process it yet
		# Wait for the user to ask a question about it
		if not message.text and not message.content:
			return {"success": True, "response": None}

		# Extract file content immediately (like Assistants API does)
		if "fid" in message.file:
			file_url = message.file.split("?fid=")[0]
		else:
			file_url = message.file

		# Get file extension for processing
		file_extension = file_url.split(".")[-1].lower() if "." in file_url else ""

		# Extract file content using Google AI if enabled, or fallback to basic extraction
		extracted_content = extract_file_content_for_agent(file_url, file_extension, bot, file_handler)

		# Build message content with extracted text
		if message.message_type == "File":
			content = f"[User uploaded a file: {file_url}]"
			if extracted_content:
				content += f"\n\nExtracted content from the file:\n{extracted_content}"
			if message.text or message.content:
				content += f"\n\nUser's question: {message.text or message.content}"
		else:
			content = f"[User uploaded an image: {file_url}]"
			if extracted_content:
				content += f"\n\nExtracted content from the image:\n{extracted_content}"
			if message.text or message.content:
				content += f"\n\nUser's question: {message.text or message.content}"
	else:
		content = message.text or message.content or ""

		# If we found a recent file upload, extract and prepend its content
		if recent_file_message:
			file_url = recent_file_message.file
			if "fid" in file_url:
				file_url = file_url.split("?fid=")[0]

			# Extract content from recent file
			file_extension = file_url.split(".")[-1].lower() if "." in file_url else ""
			extracted_content = extract_file_content_for_agent(file_url, file_extension, bot, file_handler)

			file_prefix = f"[User uploaded a {'file' if recent_file_message.message_type == 'File' else 'image'}: {file_url}]"
			if extracted_content:
				file_prefix += f"\n\nExtracted content from the file:\n{extracted_content}\n\n"
			else:
				file_prefix += "\n"

			content = file_prefix + content

	# Get conversation history if this is an existing thread
	conversation_history = []
	if not is_new_conversation and channel:
		# Fetch previous messages from the channel
		messages = frappe.get_all(
			"Raven Message",
			filters={"channel_id": channel.name},
			fields=[
				"text",
				"content",
				"owner",
				"creation",
				"bot",
				"message_type",
				"file",
				"is_bot_message",
				# //// Neoffice - the message name is fetched too, to build the history below (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
				"name",  # Add message ID for debugging
			],
			# //// Neoffice - ordered DESC so the LAST 20 messages are kept (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"). Upstream
			# //// orders ASC with limit 20, i.e. it keeps the OLDEST twenty and a long thread loses its own
			# //// recent context - which is exactly what made the model repeat itself and invent facts.
			order_by="creation desc",
			limit=20,  # Keep last 20 messages for better context
		)

		# //// Neoffice - the message that OPENED the thread is pulled in explicitly (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"):
		# //// it lives in the parent channel, so the thread query never returns it, and the model answered
		# //// without ever seeing the question it was asked.
		# For AI threads, also get the initial message that created the thread
		# The channel_name is the message ID of the thread creator
		if channel.is_ai_thread and channel.channel_name:
			try:
				thread_creator_msg = frappe.get_doc("Raven Message", channel.channel_name)
				if thread_creator_msg:
					# Add thread creator message to the list
					# It will be sorted correctly since messages are in desc order
					messages.append(
						{
							"text": thread_creator_msg.text,
							"content": thread_creator_msg.content,
							"owner": thread_creator_msg.owner,
							"creation": thread_creator_msg.creation,
							"bot": thread_creator_msg.bot if hasattr(thread_creator_msg, "bot") else None,
							"message_type": thread_creator_msg.message_type,
							"file": thread_creator_msg.file if hasattr(thread_creator_msg, "file") else None,
							"is_bot_message": thread_creator_msg.is_bot_message
							if hasattr(thread_creator_msg, "is_bot_message")
							else 0,
							"name": thread_creator_msg.name,
						}
					)
			except Exception as e:
				frappe.log_error(
					"AI History Thread Creator Error", f"Could not get thread creator message: {str(e)}"
				)

		# Sort messages by creation time desc to ensure correct order after adding thread creator
		messages = sorted(messages, key=lambda x: x["creation"], reverse=True)

		# Exclude first message (current) and reverse to get chronological order
		# messages[0] is the current message, messages[1:] are the history
		messages = list(reversed(messages[1:] if messages else []))

		for msg in messages:
			# Use text field which contains the actual message content
			# //// Neoffice - dict access (get) instead of attribute access, because the history is now built
			# //// from frappe.get_all rows rather than documents (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"); and a bot answer is
			# //// stripped of its <details> thinking block before being fed back as context.
			msg_text = msg.get("text") or msg.get("content") or ""

			# For bot messages with HTML thinking sections, extract the actual response
			if msg.get("bot") or msg.get("is_bot_message"):
				import re

				# Check if message contains HTML thinking section
				if "<details" in msg_text and "</details>" in msg_text:
					# Extract text after </details> tag (the actual response)
					# Remove the details section and get the actual response
					actual_response = re.sub(
						r"<details[^>]*>.*?</details>", "", msg_text, flags=re.DOTALL
					).strip()
					if actual_response:
						msg_text = actual_response

				# Also clean any remaining HTML tags (like <p> tags)
				if "<" in msg_text and ">" in msg_text:
					msg_text = re.sub(r"<[^>]+>", "", msg_text).strip()
					# //// Neoffice - replaced by the msg.get() form above (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").

				conversation_history.append({"role": "assistant", "content": msg_text})
			else:
				# //// Neoffice - user messages arrive as TipTap HTML; the tags are stripped before the text reaches
				# //// the model (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"), which otherwise quoted them back.
				# For user messages, also clean HTML if present
				if "<p" in msg_text and "</p>" in msg_text:
					import re

					# Extract text from HTML paragraphs
					clean_text = re.sub(r"<[^>]+>", "", msg_text).strip()
					if clean_text:
						msg_text = clean_text

				if msg.get("message_type") in ["File", "Image"]:
					# DON'T add historical files - only the current message file should be analyzed
					# Just add a reference to the file in conversation history

					# //// Neoffice - dict access on the row (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
					file_url = (
						msg.get("file", "").split("?fid=")[0]
						if "fid" in msg.get("file", "")
						else msg.get("file", "")
					)
					msg_content = (
						# //// Neoffice - dict access on the row (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
						f"[User uploaded a {'file' if msg.get('message_type') == 'File' else 'image'}: {file_url}]"
					)
					if msg_text:
						msg_content += f"\n{msg_text}"
					conversation_history.append({"role": "user", "content": msg_content})
				else:
					conversation_history.append({"role": "user", "content": msg_text})

	# Use the improved sync handler
	try:
		# //// Neoffice - LM Studio has its own handler (7cdc45189, 2025-08-22 "Feat add SDK LM Studio"): the Agents SDK cannot drive
		# //// it (no native function calling), so Raven Settings.local_llm_provider routes the turn to
		# //// raven.ai.lmstudio instead. Everything else still goes through the SDK.
		# Check if we should use LM Studio SDK handler
		settings = frappe.get_single("Raven Settings")
		is_lm_studio = bot.model_provider == "Local LLM" and settings.local_llm_provider == "LM Studio"

		if is_lm_studio:
			# For LM Studio, use SDK-only handler
			from raven.ai.lmstudio import lmstudio_sdk_handler
			from raven.ai.response_formatter import format_ai_response

			response = lmstudio_sdk_handler(bot, content, channel_id, conversation_history)

			# Format the response if successful
			if response.get("success") and response.get("response"):
				response["response"] = format_ai_response(response["response"])

			# Debug logging is now handled inside the handler based on bot.debug_mode
			if not response.get("success"):
				# SDK handler failed completely
				response = {
					"success": False,
					"response": response.get("response", "Unable to process request with LM Studio SDK"),
				}
		else:
			# Use Agents SDK for OpenAI and other providers
			response = handle_ai_request_sync(
				bot=bot,
				message=content,
				channel_id=channel_id,
				conversation_history=conversation_history,
				file_handler=file_handler,
			)

		if response["success"]:
			# Only send a response if there is one
			if response["response"] is not None:
				# //// Neoffice - an answer that already carries a <details> thinking block is sent as HTML; running
				# //// it through the markdown converter escaped the tags and the block showed as raw text
				# //// (092d027d8, 2025-08-07 "markdown message").
				# Check if response contains details tag (thinking section)
				# If it does, send as HTML directly without markdown conversion
				has_thinking = "<details" in response["response"]
				bot.send_message(channel_id=channel_id, text=response["response"], markdown=not has_thinking)
			# If response is None (e.g., file-only upload), don't send anything
		else:
			# Send error message
			error_text = "Sorry, I encountered an error while processing your request."
			if bot.debug_mode and response.get("error"):
				error_text += f"\n\nError: {response['error']}"

			bot.send_message(channel_id=channel_id, text=error_text)

		# //// Neoffice - the "stop thinking" event must be addressed to the SAME id the client subscribed
		# //// to (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging"): the parent message id for an existing thread, thread_message_id
		# //// for a brand-new one. Upstream uses channel_id, which for a DM thread is not what the client
		# //// listens on - so the indicator never stopped.
		# Clear the "thinking" message immediately after sending the response
		# For existing threads, use channel.channel_name (the parent message ID)
		# For new conversations, use thread_message_id
		# Otherwise use channel_id
		if channel and hasattr(channel, "channel_name"):
			# Existing thread - use the parent message ID
			event_channel_id = channel.channel_name
		elif thread_message_id:
			# New conversation with thread
			event_channel_id = thread_message_id
		else:
			# Direct message or other
			event_channel_id = channel_id

		# Send clear event exactly like we send the thinking message
		frappe.publish_realtime(
			"ai_event_clear",
			{
				# //// Neoffice - addressed id, see L735 (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
				"channel_id": event_channel_id,
			},
			# //// Neoffice - user-addressed and immediate, like the thinking message (5a7db4919, 2025-08-07 "fix: Add room parameter to publish_realtime to avoid broadcasting to all users").
			user=message.owner,
			after_commit=False,  # Same as thinking message
		)

	except Exception as e:
		import traceback

		frappe.log_error(
			f"Error calling handle_ai_request_sync: {str(e)}\n\nTraceback:\n{traceback.format_exc()}",
			"Raven AI",
		)
		# Send error message
		error_text = "I encountered an error while processing your request."
		if bot.debug_mode:
			error_text += f"\n\nError: {str(e)}"

		bot.send_message(channel_id=channel_id, text=error_text)

		# Clear the "thinking" message even on error
		# //// Neoffice - same addressing on the error path (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
		event_channel_id = (
			thread_message_id if thread_message_id else (channel.channel_name if channel else channel_id)
		)
		frappe.publish_realtime(
			"ai_event_clear",
			{
				# //// Neoffice - addressed id, error path (4fad9cd58, 2025-08-07 "Fix LLM hallucinations and improve AI thread messaging").
				"channel_id": event_channel_id,
			},
			# //// Neoffice - scoped to the channel room instead of broadcasting the failure to every connected
			# //// user (5a7db4919, 2025-08-07 "fix: Add room parameter to publish_realtime to avoid broadcasting to all users").
			room=event_channel_id,  # Send only to users in this channel
			after_commit=False,  # Clear immediately
		)


def check_if_bot_has_file_search(bot, channel_id):
	"""
	Checks of bot has file search. If not, send a message to the user. If yes, return True
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


def get_content_attachment_for_file(message_type: str, file_id: str, file_url: str, bot):

	attachments = None

	if message_type == "File":
		content = f"Uploaded a file. URL of the file is '{file_url}'. Use this URL to attach the file to any document if requested."

		file_extension = file_url.split(".")[-1].lower()

		extracted_content = ""

		if bot.use_google_document_parser:
			extracted_content = run_document_ai_processor(
				bot.google_document_processor_id, file_url, file_extension
			)

			if extracted_content:
				content += f"\n\nThe document was parsed and the following content was extracted from it:\n {extracted_content}"

		if not extracted_content and file_extension == "pdf":
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

		main_content = f"Uploaded an image. URL of the image is '{file_url}'. Use this URL to attach the image to any document if requested."

		file_extension = file_url.split(".")[-1].lower()

		if bot.use_google_document_parser:
			extracted_content = run_document_ai_processor(
				bot.google_document_processor_id, file_url, file_extension
			)

			if extracted_content:
				main_content += f"\n\nThe document was parsed and the following content was extracted from it:\n {extracted_content}"

		content = [
			{
				"type": "text",
				"text": main_content,
			},
			{"type": "image_file", "image_file": {"file_id": file_id}},
		]

	return content, attachments


# //// Neoffice - Nora turn processing (6375b651f, 2026-01-04 "feat: Add Nora as model provider option" + 1cbe89844/6709a4438, 2026-02-17).
# //// Builds the conversation, calls NORA's handler and writes the answer back as the bot. No
# //// upstream equivalent - upstream has only the OpenAI and Local LLM paths.
def process_message_with_nora(
	message, bot, channel_id: str, is_new_conversation: bool, channel=None, thread_message_id=None
):
	"""
	Process a message using NORA's AI orchestration.

	This function routes all AI processing to Nora, including:
	- Prompt generation (from NORA Settings)
	- RAG context (from Haystack)
	- Code execution (31 Frappe tools)
	- OCR/Vision

	Raven only handles the chat UI and message storage.
	"""
	import json

	try:
		# Check if Nora app is installed
		if "nora" not in frappe.get_installed_apps():
			bot.send_message(
				channel_id=channel_id,
				text="Error: NORA app is not installed. Please install the NORA app to use this bot.",
			)
			return

		# Get the message content
		content = message.text or message.content or ""

		# Handle file/image messages
		files = []
		if message.message_type in ["File", "Image"]:
			file_url = message.file
			if "fid" in file_url:
				file_url = file_url.split("?fid=")[0]

			files.append(
				{"file_url": file_url, "file_type": message.message_type, "message_type": message.message_type}
			)

			# If there's text with the file, include it
			if content:
				pass  # content already set
			else:
				content = f"[User uploaded a {'file' if message.message_type == 'File' else 'image'}]"

		# Get conversation history from the channel
		conversation_history = []
		if not is_new_conversation and channel:
			messages = frappe.get_all(
				"Raven Message",
				filters={"channel_id": channel.name},
				fields=["text", "content", "owner", "bot", "is_bot_message", "creation"],
				order_by="creation desc",
				limit=10,  # Reduced from 20 to prevent token overflow
			)

			# Reverse to get chronological order and exclude current message
			for msg in reversed(messages[1:] if messages else []):
				msg_text = msg.get("text") or msg.get("content") or ""
				# Truncate very long messages to prevent token overflow
				# Bot messages might echo conversation history, causing exponential growth
				if len(msg_text) > 3000:
					msg_text = msg_text[:2000] + "... [truncated]"
				if msg.get("bot") or msg.get("is_bot_message"):
					conversation_history.append({"role": "assistant", "content": msg_text})
				else:
					conversation_history.append({"role": "user", "content": msg_text})

		# Call Nora handler
		from nora.api.raven_handler import handle_raven_message

		response = handle_raven_message(
			channel_id=channel_id,
			message_id=message.name,
			message_text=content,
			user=message.owner,
			thread_id=thread_message_id,
			files=json.dumps(files) if files else None,
			conversation_history=json.dumps(conversation_history) if conversation_history else None,
		)

		if response.get("success"):
			if response.get("response"):
				# Check if response contains details tag (thinking section)
				has_thinking = "<details" in response["response"]

				# Extract document link info if present (for doctype card display)
				link_doctype = None
				link_document = None
				pending_doc = response.get("pending_document")
				if pending_doc and isinstance(pending_doc, dict):
					link_doctype = pending_doc.get("doctype")
					link_document = pending_doc.get("name")

				bot.send_message(
					channel_id=channel_id,
					text=response["response"],
					markdown=not has_thinking,
					link_doctype=link_doctype,
					link_document=link_document,
				)
		else:
			error_text = "Sorry, I encountered an error while processing your request."
			if bot.debug_mode and response.get("error"):
				error_text += f"\n\nError: {response['error']}"
			bot.send_message(channel_id=channel_id, text=error_text)

		# Clear the "thinking" message
		event_channel_id = (
			thread_message_id if thread_message_id else (channel.channel_name if channel else channel_id)
		)
		frappe.publish_realtime(
			"ai_event_clear",
			{"channel_id": event_channel_id},
			user=message.owner,
			after_commit=False,
		)

	except Exception as e:
		import traceback

		frappe.log_error(
			f"Error in process_message_with_nora: {str(e)}\n\nTraceback:\n{traceback.format_exc()}",
			"Raven Nora Integration",
		)

		error_text = "I encountered an error while processing your request."
		if bot.debug_mode:
			error_text += f"\n\nError: {str(e)}"
		bot.send_message(channel_id=channel_id, text=error_text)

		# Clear the "thinking" message even on error
		event_channel_id = (
			thread_message_id if thread_message_id else (channel.channel_name if channel else channel_id)
		)
		frappe.publish_realtime(
			"ai_event_clear",
			{"channel_id": event_channel_id},
			user=message.owner,
			after_commit=False,
		)


def publish_ai_thread_created_event(message, channel_id):
	"""
	Publish an event when an AI thread is created for auto-opening in frontend
	"""
	frappe.publish_realtime(
		"ai_thread_created",
		{"thread_id": message.name, "channel_id": channel_id, "is_ai_thread": True},
		user=message.owner,
		after_commit=False,
	)
