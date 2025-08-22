"""
LM Studio SDK Handler for Raven
Redirects to enhanced_handler for better function calling support
"""

from typing import Any, Dict

import frappe

from .enhanced_handler import EnhancedLMStudioHandler, process_with_lmstudio

# Export for backward compatibility
LMStudioClient = EnhancedLMStudioHandler


def lmstudio_sdk_handler(
	bot, message: str, channel_id: str = None, conversation_history: list = None
) -> dict:
	"""
	Main handler for LM Studio SDK integration.

	Args:
	    bot: Raven AI Bot document
	    message: User message
	    channel_id: Raven channel ID
	    conversation_history: Previous messages

	Returns:
	    Dict with response or error
	"""

	# Build context
	context = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"channel_id": channel_id,
		"thread_id": frappe.flags.get("raven_thread_id"),
		"conversation_history": conversation_history or [],
	}

	# Use enhanced handler
	return process_with_lmstudio(bot, message, context)


def test_lmstudio_connection():
	"""Test LM Studio connection."""
	try:
		import lmstudio as lms

		model = lms.llm()
		return {"status": "success", "message": "LM Studio connected"}
	except Exception as e:
		return {"status": "error", "message": str(e)}
