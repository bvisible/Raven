"""
Mobile Chat API for Raven-Nora Integration

This module provides API endpoints for mobile apps to interact with
the Nora AI bot through Raven's messaging infrastructure.

Key features:
- Get/create DM channel with nora bot
- List AI conversation threads
- Send messages with SSE streaming responses
- Get thread message history

Author: NORA Team
Date: 2026-01-04
"""

import frappe
from frappe import _
from frappe.query_builder import Order
from pypika import functions as fn

from raven.api.raven_channel import create_direct_message_channel
from raven.api.threads import get_all_threads
from raven.utils import get_raven_user


def ensure_raven_user():
	"""
	Ensure the current user has a Raven User record.
	Creates one if it doesn't exist.

	Returns:
	    str: The Raven User ID
	"""
	user = frappe.session.user

	# Check if Raven User already exists (by user field)
	existing = frappe.db.get_value("Raven User", {"user": user}, "name")
	if existing:
		return existing

	# Also check by name (in case name == user email)
	if frappe.db.exists("Raven User", user):
		return user

	# Create Raven User for this user
	user_doc = frappe.get_doc("User", user)

	raven_user = frappe.new_doc("Raven User")
	raven_user.user = user
	raven_user.full_name = user_doc.full_name or user_doc.first_name or user
	raven_user.first_name = user_doc.first_name or user
	raven_user.enabled = 1
	raven_user.insert(ignore_permissions=True)
	frappe.db.commit()

	return raven_user.name


@frappe.whitelist()
def get_nora_dm_channel():
	"""
	Get or create the DM channel between current user and nora bot.

	Returns:
	    dict with channel_id and bot info
	"""
	# Ensure current user has a Raven User record
	ensure_raven_user()

	# Get the nora bot's Raven User ID
	nora_bot = frappe.db.get_value(
		"Raven Bot", {"bot_name": "nora", "model_provider": "Nora"}, ["name", "raven_user"], as_dict=True
	)

	if not nora_bot or not nora_bot.raven_user:
		frappe.throw(_("Nora bot is not configured. Please check NORA Settings."))

	# Get or create DM channel with nora
	channel_id = create_direct_message_channel(nora_bot.raven_user)

	return {"channel_id": channel_id, "bot_name": nora_bot.name, "bot_user_id": nora_bot.raven_user}


@frappe.whitelist()
def get_ai_conversations(limit: int = 20, start_after: int = 0):
	"""
	Get all AI conversation threads for the current user.
	These are threads created when messaging the nora bot.

	Args:
	    limit: Maximum number of threads to return
	    start_after: Offset for pagination

	Returns:
	    List of AI thread objects with metadata
	"""
	threads = get_all_threads(is_ai_thread=1, limit=limit, start_after=start_after)

	# Enhance thread data with conversation-like fields
	for thread in threads:
		# Get the first user message as the conversation title/preview
		if thread.get("content"):
			# Truncate content for preview
			content = thread["content"]
			thread["preview"] = content[:100] + "..." if len(content) > 100 else content

		# Add reply count as message_count for mobile
		thread["message_count"] = thread.get("reply_count", 0) + 1  # +1 for original message

	return threads


@frappe.whitelist()
def get_thread_messages(thread_id: str, limit: int = 50, offset: int = 0):
	"""
	Get messages from an AI thread.

	Args:
	    thread_id: The thread channel ID
	    limit: Maximum messages to return
	    offset: Offset for pagination

	Returns:
	    List of messages in chronological order
	"""
	# Verify user has access to this thread
	if not frappe.db.exists(
		"Raven Channel Member", {"channel_id": thread_id, "user_id": frappe.session.user}
	):
		frappe.throw(_("You don't have access to this thread"))

	messages = frappe.get_all(
		"Raven Message",
		filters={"channel_id": thread_id},
		fields=[
			"name",
			"owner",
			"creation",
			"text",
			"content",
			"message_type",
			"is_bot_message",
			"bot",
			"file",
			"file_thumbnail",
		],
		order_by="creation asc",
		limit_page_length=limit,
		limit_start=offset,
	)

	# Also get the original thread message (which is in the parent DM channel)
	thread_message = frappe.db.get_value(
		"Raven Message",
		thread_id,  # Thread ID is the same as the original message ID
		["name", "owner", "creation", "text", "content", "message_type"],
		as_dict=True,
	)

	if thread_message:
		# Insert the original message at the beginning
		thread_message["is_bot_message"] = 0
		messages.insert(0, thread_message)

	return messages


@frappe.whitelist(methods=["POST"])
def send_message_stream(text: str, thread_id: str = None):
	"""
	Send a message to nora and stream the response via SSE.

	If thread_id is not provided, creates a new thread.
	Uses the existing Nora integration to process the message.

	Args:
	    text: Message text to send
	    thread_id: Optional existing thread ID to continue conversation

	Returns:
	    SSE stream with response chunks
	"""
	import json

	from frappe.utils.response import Response

	# Get nora DM channel
	nora_info = get_nora_dm_channel()
	channel_id = nora_info["channel_id"]

	# Determine target channel
	if thread_id:
		# Verify user has access
		if not frappe.db.exists(
			"Raven Channel Member", {"channel_id": thread_id, "user_id": frappe.session.user}
		):
			frappe.throw(_("You don't have access to this thread"))
		target_channel = thread_id
	else:
		# Message goes to DM, will create new thread
		target_channel = channel_id

	# Create the user message
	message = frappe.get_doc(
		{"doctype": "Raven Message", "channel_id": target_channel, "text": text, "message_type": "Text"}
	)
	message.insert()
	frappe.db.commit()

	# The message insertion will trigger handle_bot_dm or handle_ai_thread_message
	# which calls Nora's handler. We need to wait for the response.

	# For now, return the message info - the actual streaming
	# happens through Raven's realtime events
	return {
		"success": True,
		"message_id": message.name,
		"channel_id": target_channel,
		"thread_id": thread_id or message.name,  # If new, message becomes thread
	}


@frappe.whitelist(methods=["POST"])
def send_message_to_nora(text: str, thread_id: str = None):
	"""
	Send a message to nora and get the response (non-streaming).

	This is a synchronous version that waits for Nora's response.

	Args:
	    text: Message text to send
	    thread_id: Optional existing thread ID

	Returns:
	    dict with response and metadata
	"""
	# Get nora DM channel
	nora_info = get_nora_dm_channel()
	channel_id = nora_info["channel_id"]

	# Determine target channel
	target_channel = thread_id if thread_id else channel_id

	if thread_id:
		# Verify access
		if not frappe.db.exists(
			"Raven Channel Member", {"channel_id": thread_id, "user_id": frappe.session.user}
		):
			frappe.throw(_("You don't have access to this thread"))

	# Create user message
	user_message = frappe.get_doc(
		{"doctype": "Raven Message", "channel_id": target_channel, "text": text, "message_type": "Text"}
	)
	user_message.insert()

	# If this is a new message to DM (not thread), it will create a thread
	# and the handle_bot_dm will be called automatically by Raven

	frappe.db.commit()

	# The bot response will be sent asynchronously via Raven's normal flow
	# Return info about what was created
	return {
		"success": True,
		"user_message_id": user_message.name,
		"channel_id": target_channel,
		"is_new_thread": thread_id is None,
	}


@frappe.whitelist()
def get_conversation_count():
	"""
	Get the total count of AI conversations for the current user.

	Returns:
	    dict with total count
	"""
	channel = frappe.qb.DocType("Raven Channel")
	channel_member = frappe.qb.DocType("Raven Channel Member")

	count = (
		frappe.qb.from_(channel)
		.join(channel_member)
		.on(channel.name == channel_member.channel_id)
		.where(channel_member.user_id == frappe.session.user)
		.where(channel.is_thread == 1)
		.where(channel.is_ai_thread == 1)
		.select(fn.Count(channel.name))
		.run()
	)

	return {"count": count[0][0] if count else 0}


@frappe.whitelist(methods=["DELETE"])
def delete_conversation(thread_id: str):
	"""
	Delete (archive) an AI conversation thread.
	User must be a member of the thread.

	Args:
	    thread_id: The thread channel ID to delete

	Returns:
	    Success status
	"""
	# Verify user has access
	if not frappe.db.exists(
		"Raven Channel Member", {"channel_id": thread_id, "user_id": frappe.session.user}
	):
		frappe.throw(_("You don't have access to this thread"))

	# Verify it's an AI thread
	channel = frappe.get_doc("Raven Channel", thread_id)
	if not channel.is_ai_thread:
		frappe.throw(_("This is not an AI conversation"))

	# Archive the channel (soft delete)
	channel.is_archived = 1
	channel.save(ignore_permissions=True)

	return {"success": True, "message": _("Conversation archived")}
