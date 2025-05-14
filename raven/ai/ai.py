import frappe
import asyncio

from raven.ai.sdk_handler import stream_response as sdk_stream_response
from raven.ai.sdk_agents import AGENTS_SDK_AVAILABLE


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
	# Get the bot for this thread
	bot = frappe.get_doc("Raven Bot", channel.thread_bot)

	# Check file search capability for file messages
	if message.message_type in ["File", "Image"] and message.message_type == "File":
		if not check_if_bot_has_file_search(bot, channel.name):
			return

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
		# Use SDK Agents for all models
		file_data = None
		if message.message_type in ["File", "Image"]:
			file_doc = frappe.get_doc("File", {"file_url": message.file})
			file_data = [{"file_path": file_doc.get_full_path(), "file_name": file_doc.file_name}]
		
		# Get response from SDK and send message
		response_text = asyncio.run(sdk_stream_response(
			bot=bot, 
			channel_id=channel.name, 
			message=message.content,
			files=file_data
		))
		
		# Send the message if we got a response
		if response_text:
			bot.send_message(
				channel_id=channel.name,
				text=response_text,
				markdown=True,
			)
	else:
		# SDK not available - inform the user
		bot.send_message(
			channel_id=channel.name,
			text="OpenAI Agents SDK is not installed. Please run 'pip install openai-agents' on the server.",
		)


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
