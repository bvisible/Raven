# raven/ai/ai_new.py
import frappe
import asyncio

from raven.ai.handler import stream_response
from raven.ai.agent_handler import process_message_with_agent
from raven.ai.migration_helper import use_legacy_system
from raven.ai.openai_client import (
	code_interpreter_file_types,
	file_search_file_types,
	get_open_ai_client,
)


def handle_bot_dm(message, bot):
	"""
	Function to handle direct messages to the bot.
	
	We need to start a new thread with the message and create a new conversation
	"""
	
	# Determine which system to use
	if not use_legacy_system(bot.name):
		# Use the new agent system
		return handle_bot_dm_with_agent(message, bot)
	
	# Use the legacy system (existing code below)
	return handle_bot_dm_legacy(message, bot)


def handle_bot_dm_with_agent(message, bot):
	"""
	Handle direct messages with the new agent system
	"""
	
	# If the message is a poll, send an error message
	if message.message_type == "Poll":
		bot.send_message(
			channel_id=message.channel_id,
			text="Sorry, I don't support polls yet. Please send a text message or file.",
		)
		return
	
	# Prepare the context
	context = {
		"user": message.owner,
		"message_name": message.name,
		"message_type": message.message_type
	}
	
	# Handle files
	if message.message_type in ["File", "Image"]:
		if message.message_type == "File" and not check_if_bot_has_file_search(bot, message.channel_id):
			return
		
		# Extract the file URL
		file_url = message.file.split("?fid=")[0] if "fid" in message.file else message.file
		
		# If RAG is enabled, index the file
		if bot.use_local_rag:
			from raven.ai.file_manager import FileManager
			file_manager = FileManager(bot)
			
			# Download and index the file asynchronously
			try:
				loop = asyncio.new_event_loop()
				asyncio.set_event_loop(loop)
				loop.run_until_complete(file_manager.process_file(file_url))
				
				# Add a message to confirm indexing
				bot.send_message(
					channel_id=message.channel_id,
					text=f"File indexed successfully. You can now ask questions about it.",
				)
			except Exception as e:
				frappe.log_error(f"Error indexing file: {e}")
				bot.send_message(
					channel_id=message.channel_id,
					text="Error processing file. Please try again.",
				)
				return
		
		# Add the file to the message context
		message_text = f"[File: {file_url}]\n{message.text or 'Process this file'}"
	else:
		message_text = message.text
	
	# Start a new conversation thread
	ai_thread_id = frappe.generate_hash(length=10)
	
	# Process the message asynchronously
	try:
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(
			process_message_with_agent(
				message=message_text,
				bot=bot,
				channel_id=message.channel_id,
				ai_thread_id=ai_thread_id,
				context=context
			)
		)
	except Exception as e:
		frappe.log_error(f"Error processing message with agent: {e}")
		if bot.debug_mode:
			bot.send_message(
				channel_id=message.channel_id,
				text=f"Error: {str(e)}",
				markdown=True
			)
		else:
			bot.send_message(
				channel_id=message.channel_id,
				text="An error occurred while processing your message. Please try again.",
			)


def handle_bot_dm_legacy(message, bot):
	"""
	Existing code to handle bots with the Assistant API (legacy)
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

		content, attachments = get_content_attachment_for_file(message.message_type, file.id, file_url)

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
				"channel_id": message.channel_id,
			},
		)
	elif message.is_continuation:
		# If the message is a continuation, we need to add the message to the existing thread
		ai_thread = get_ai_thread(message.channel_id)
		client.beta.threads.messages.create(
			thread_id=ai_thread.name,
			role="user",
			content=message.text,
			metadata={"user": message.owner, "message": message.name},
		)
	else:
		# Create the thread
		ai_thread = client.beta.threads.create(
			messages=[
				{
					"role": "user",
					"content": message.text,
					"metadata": {"user": message.owner, "message": message.name},
				}
			],
			metadata={
				"channel_id": message.channel_id,
			},
		)

	# Save the thread ID to the database
	if not message.is_continuation:
		save_ai_thread_to_db(ai_thread.id, message.channel_id)

	# Create the run
	run = create_run(ai_thread.id, bot, message.channel_id)
	stream_response(run.thread_id, bot, message.channel_id)


def handle_bot_message_in_channel(bot, channel_id: str, message):
	"""
	Function to handle messages to the bot in a channel.
	"""
	
	# Determine which system to use
	if not use_legacy_system(bot.name):
		# Use the new agent system
		return handle_bot_message_in_channel_with_agent(bot, channel_id, message)
	
	# Use the legacy system (existing code)
	return handle_bot_message_in_channel_legacy(bot, channel_id, message)


def handle_bot_message_in_channel_with_agent(bot, channel_id: str, message):
	"""
	Handle bot messages in a channel with the new system
	"""
	
	if message.message_type == "Poll":
		bot.send_message(
			channel_id=channel_id,
			text="Sorry, I don't support polls yet. Please send a text message.",
		)
		return
	
	if message.message_type in ["File", "Image"]:
		bot.send_message(
			channel_id=channel_id,
			text="Sorry, I don't support files or images in channels. Please send them in a direct message.",
		)
		return
	
	# Prepare the context
	context = {
		"user": message.owner,
		"message_name": message.name,
		"channel_type": "channel"
	}
	
	# Get a thread identifier for this channel
	ai_thread_id = f"channel_{channel_id}"
	
	# Process the message
	try:
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(
			process_message_with_agent(
				message=message.text,
				bot=bot,
				channel_id=channel_id,
				ai_thread_id=ai_thread_id,
				context=context
			)
		)
	except Exception as e:
		frappe.log_error(f"Error processing channel message with agent: {e}")
		if bot.debug_mode:
			bot.send_message(
				channel_id=channel_id,
				text=f"Error: {str(e)}",
				markdown=True
			)
		else:
			bot.send_message(
				channel_id=channel_id,
				text="An error occurred. Please try again.",
			)


def handle_bot_message_in_channel_legacy(bot, channel_id: str, message):
	"""
	Existing code to handle messages in channels (legacy)
	"""
	client = get_open_ai_client()

	# Get the AI thread for this channel/bot
	ai_thread = get_ai_thread(channel_id)

	if message.message_type == "Poll":
		bot.send_message(
			channel_id=channel_id,
			text="Sorry, I don't support polls yet. Please send a text message.",
		)
		return

	if message.message_type in ["File", "Image"]:
		bot.send_message(
			channel_id=channel_id,
			text="Sorry, I don't support files or images in channels. Please send them in a direct message.",
		)
		return

	# Add the message to the thread
	client.beta.threads.messages.create(
		thread_id=ai_thread.name,
		role="user",
		content=message.text,
		metadata={"user": message.owner, "message": message.name},
	)

	# Create the run
	run = create_run(ai_thread.name, bot, channel_id)
	stream_response(run.thread_id, bot, channel_id)


# Existing utility functions to keep
def check_if_bot_has_file_search(bot, channel_id: str):
	if not bot.enable_file_search:
		bot.send_message(
			channel_id=channel_id,
			text="Sorry, I don't support file search. Please enable file search in the bot settings to use this feature.",
		)
		return False
	return True


def get_content_attachment_for_file(message_type, file_id, file_url):
	"""
	Get the content and attachment for a file.
	"""
	if message_type == "File":
		return [
			{"type": "text", "text": f"I have uploaded a file for you to analyze: {file_url}"},
			{
				"type": "file_search",
				"file_search": {"file_id": file_id},
			},
		], [{"file_id": file_id, "tools": [{"type": "file_search"}]}]
	elif message_type == "Image":
		return [
			{"type": "text", "text": f"I have uploaded an image for you to analyze: {file_url}"},
			{
				"type": "file_search",
				"file_search": {"file_id": file_id},
			},
		], [{"file_id": file_id, "tools": [{"type": "file_search"}]}]
	else:
		return "", []


def create_file_in_openai(file_url, message_type, client):
	"""
	Upload the file to OpenAI
	"""
	import requests

	file = requests.get(file_url)
	file_name = "file.txt"
	if file_url:
		parsed_url = requests.utils.urlparse(file_url)
		file_name = parsed_url.path.split("/")[-1]
	
	purpose = get_purpose_for_file(message_type, file_url)

	file = client.files.create(file=(file_name, file.content), purpose=purpose)
	return file


def get_purpose_for_file(message_type, file_url):
	"""
	Get the purpose for the file being uploaded. We'll have to check supported mime types for the file.
	For now, assume that all images are for "vision" and the rest can be either assistants or vision
	"""
	if message_type == "Image":
		return "assistants"
	else:
		file_extension = file_url.split(".")[-1].lower()
		if file_extension in file_search_file_types:
			return "assistants"
		elif file_extension in code_interpreter_file_types:
			return "assistants"
		else:
			return "assistants"


def get_ai_thread(channel_id: str):
	"""
	Get the AI thread for the channel.
	"""
	thread = frappe.db.get_value(
		"Raven AI Thread", {"channel": channel_id}, ["name", "thread_data"], as_dict=True
	)
	if thread:
		return thread


def save_ai_thread_to_db(thread_id: str, channel_id: str):
	"""
	Save the thread ID to the database.
	"""
	if not frappe.db.exists("Raven AI Thread", {"name": thread_id}):
		frappe.get_doc(
			{
				"doctype": "Raven AI Thread",
				"name": thread_id,
				"channel": channel_id,
			}
		).insert()


def create_run(thread_id: str, bot, channel_id: str):
	"""
	Create a run for the thread.
	"""
	client = get_open_ai_client()
	tools = []
	
	# Add tools based on bot configuration
	if bot.enable_file_search:
		tools.append({"type": "file_search"})
	if bot.enable_code_interpreter:
		tools.append({"type": "code_interpreter"})
	
	run = client.beta.threads.runs.create(
		thread_id=thread_id,
		assistant_id=bot.openai_assistant_id,
		tools=tools,
		metadata={
			"channel_id": channel_id,
		},
	)
	return run