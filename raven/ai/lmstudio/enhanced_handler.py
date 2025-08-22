"""
Enhanced LM Studio SDK Handler with robust function calling
Handles multiple formats and provides fallback mechanisms
"""

import json
import time
from typing import Any, Callable, Dict, List, Optional

import frappe

from .function_parser import FunctionCallParser

try:
	import lmstudio as lms

	LMS_SDK_AVAILABLE = True
except ImportError:
	LMS_SDK_AVAILABLE = False
	frappe.log_error("LMStudio SDK Import", "lmstudio package not available")


class EnhancedLMStudioHandler:
	"""
	Enhanced handler with robust function calling support.
	"""

	def __init__(self, bot, context: dict[str, Any]):
		self.bot = bot
		self.context = context
		self.conversation_history = context.get("conversation_history", [])
		self.timeout = 60
		self.tools = []
		self.function_names = []

		if LMS_SDK_AVAILABLE:
			self._initialize_tools()

	def _initialize_tools(self):
		"""Initialize tools from bot configuration."""

		# Load Raven base functions
		self._load_raven_functions()

		# Load bot-specific functions
		self._load_bot_functions()

		# Store function names for parser
		self.function_names = [tool.__name__ for tool in self.tools if hasattr(tool, "__name__")]

		# Debug log commented - uncomment if needed
		# frappe.log_error(
		#     "Enhanced Handler Tools",
		#     f"Loaded {len(self.tools)} tools: {self.function_names}"
		# )

	def _load_raven_functions(self):
		"""Load core Raven functions."""
		# Context is now injected directly into the prompt
		# No specific functions to load here
		pass

	def _load_bot_functions(self):
		"""Load bot-specific functions from configuration."""
		if not self.bot or not self.bot.bot_functions:
			frappe.log_error(
				"Bot Functions", f"No bot functions configured for {self.bot.name if self.bot else 'No bot'}"
			)
			return

		frappe.log_error(
			"Loading Bot Functions", f"Found {len(self.bot.bot_functions)} functions to load"
		)

		for func_link in self.bot.bot_functions:
			try:
				func_doc = frappe.get_doc("Raven AI Function", func_link.function)

				frappe.log_error(
					f"Loading function: {func_doc.function_name}",
					f"Type: {func_doc.type}, Path: {func_doc.function_path}",
				)

				# Handle different function types
				if func_doc.type == "Custom Function" and func_doc.function_path:
					tool = self._create_tool_from_doc(func_doc)
					if tool:
						self.tools.append(tool)
						frappe.log_error(f"Loaded: {func_doc.function_name}", "Success")
				elif func_doc.type in ["Get List", "Get Document", "Create Document"]:
					# These are template functions that need special handling
					tool = self._create_template_function(func_doc)
					if tool:
						self.tools.append(tool)
						frappe.log_error(f"Loaded template: {func_doc.function_name}", "Success")

			except Exception as e:
				frappe.log_error(f"Failed to load {func_link.function}", str(e))

	def _wrap_function(self, func: Callable) -> Callable:
		"""Wrap a function with Frappe context management."""

		def wrapped(**kwargs):
			try:
				# Restore Frappe context
				import frappe

				frappe.init(site=self.context["site"])
				frappe.connect()

				if self.context.get("user"):
					frappe.set_user(self.context["user"])

				# Set flags
				if self.context.get("channel_id"):
					frappe.flags.raven_channel_id = self.context["channel_id"]
				if self.context.get("thread_id"):
					frappe.flags.raven_thread_id = self.context["thread_id"]

				# Execute function
				result = func(**kwargs)

				# Convert datetime objects for JSON
				result = self._serialize_result(result)

				# Commit and cleanup
				frappe.db.commit()
				frappe.destroy()

				return result

			except Exception as e:
				try:
					frappe.destroy()
				except Exception:
					pass
				return {"status": "error", "message": str(e)}

		# Copy metadata
		wrapped.__name__ = func.__name__
		wrapped.__doc__ = func.__doc__
		if hasattr(func, "__annotations__"):
			wrapped.__annotations__ = func.__annotations__

		return wrapped

	def _create_template_function(self, func_doc) -> Callable | None:
		"""Create a function from a template type (Get List, Get Document, etc.)."""
		try:
			from raven.ai import functions as raven_functions

			# Map function types to base functions
			function_map = {
				"Get List": raven_functions.get_list,
				"Get Document": raven_functions.get_document,
				"Get Multiple Documents": raven_functions.get_documents,
				"Create Document": raven_functions.create_document,
				"Update Document": raven_functions.update_document,
				"Delete Document": raven_functions.delete_document,
			}

			base_func = function_map.get(func_doc.type)
			if not base_func:
				frappe.log_error(f"Unknown template type: {func_doc.type}", func_doc.function_name)
				return None

			# Create a wrapper that includes the doctype
			def wrapped(**kwargs):
				# Add the reference_doctype to kwargs
				if func_doc.reference_doctype and "doctype" not in kwargs:
					kwargs["doctype"] = func_doc.reference_doctype

				# Restore Frappe context
				try:
					import frappe

					frappe.init(site=self.context["site"])
					frappe.connect()
					if self.context.get("user"):
						frappe.set_user(self.context["user"])

					# Call the base function
					result = base_func(**kwargs)

					# Serialize result
					result = self._serialize_result(result)

					frappe.db.commit()
					frappe.destroy()
					return result

				except Exception as e:
					try:
						frappe.destroy()
					except Exception:
						pass
					return {"status": "error", "message": str(e)}

			# Set metadata
			wrapped.__name__ = func_doc.function_name
			wrapped.__doc__ = func_doc.description or f"{func_doc.type} for {func_doc.reference_doctype}"

			return wrapped

		except Exception as e:
			frappe.log_error("Failed to create template function", str(e))
			return None

	def _create_tool_from_doc(self, func_doc) -> Callable | None:
		"""Create a tool from a Raven AI Function document."""
		try:
			# Import the function
			module_path, func_name = func_doc.function_path.rsplit(".", 1)
			module = __import__(module_path, fromlist=[func_name])
			original_func = getattr(module, func_name)

			# Wrap it
			wrapped = self._wrap_function(original_func)
			wrapped.__name__ = func_doc.function_name
			wrapped.__doc__ = func_doc.description

			return wrapped

		except Exception as e:
			frappe.log_error(f"Failed to create tool from {func_doc.function_name}", str(e))
			return None

	def _serialize_result(self, obj):
		"""Convert datetime objects to strings for JSON serialization."""
		from datetime import date, datetime

		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		elif isinstance(obj, dict):
			return {k: self._serialize_result(v) for k, v in obj.items()}
		elif isinstance(obj, list):
			return [self._serialize_result(item) for item in obj]
		return obj

	def process(self, message: str) -> dict:
		"""Process message with enhanced function calling."""

		if not LMS_SDK_AVAILABLE:
			return {"success": False, "error": "LM Studio SDK not available"}

		try:
			# Get LM Studio configuration
			# First check Raven Settings for local_llm_api_url
			lm_studio_url = None

			# Try to get from Raven Settings
			try:
				raven_settings = frappe.get_single("Raven Settings")
				if raven_settings.enable_local_llm and raven_settings.local_llm_api_url:
					lm_studio_url = raven_settings.local_llm_api_url
					# Debug log commented - uncomment if needed
					# frappe.log_error("LM Studio URL from Settings", lm_studio_url)
			except Exception:
				pass

			# Check if bot has custom endpoint configured
			if not lm_studio_url and self.bot and hasattr(self.bot, "llm_model_config"):
				try:
					import json

					config = json.loads(self.bot.llm_model_config or "{}")
					lm_studio_url = config.get("base_url") or config.get("endpoint")
				except Exception:
					pass

			# If still no URL, raise error
			if not lm_studio_url:
				raise Exception("No LM Studio URL configured in Raven Settings or bot config")

			# Clean up the URL for LM Studio SDK
			# The SDK works best with just the domain/host
			if lm_studio_url.startswith("https://"):
				# Remove https:// and /v1
				ws_url = lm_studio_url.replace("https://", "").replace("/v1", "")
			elif lm_studio_url.startswith("http://"):
				# Remove http:// and /v1
				ws_url = lm_studio_url.replace("http://", "").replace("/v1", "")
			elif lm_studio_url.startswith("wss://") or lm_studio_url.startswith("ws://"):
				# Remove protocol
				ws_url = lm_studio_url.replace("wss://", "").replace("ws://", "").replace("/v1", "")
			else:
				# Use as-is, but remove /v1 if present
				ws_url = lm_studio_url.replace("/v1", "")

			# Initialize client with custom host
			client = lms.Client(api_host=ws_url)

			# Get a model from the client
			try:
				# Try to get any loaded model
				loaded = client.llm.list_loaded()
				if loaded:
					model_id = loaded[0].identifier if hasattr(loaded[0], "identifier") else str(loaded[0])
					model = client.llm.model(model_id)
				else:
					# Fallback to getting any model
					model = client.llm._get_any()
			except Exception:
				# Last resort: try the convenience API with proper error handling
				try:
					import os

					os.environ["LMSTUDIO_HOST"] = ws_url  # Try to set env var
					model = lms.llm()
				except Exception:
					raise Exception(f"Cannot get model from LM Studio at {ws_url}")

			# Build system prompt
			system_prompt = self._build_system_prompt()

			# Create chat
			chat = lms.Chat(system_prompt)

			# Add conversation history
			self._add_history_to_chat(chat)

			# Add current message
			chat.add_user_message(message)

			# Track messages
			messages = []
			result = None

			def on_message(msg):
				messages.append(msg)
				chat.append(msg)

				# Debug log commented - uncomment if needed
				# msg_type = type(msg).__name__
				# frappe.log_error(
				#     f"Message #{len(messages)}",
				#     f"Type: {msg_type}"
				# )

			# First try: Use SDK tools
			try:
				result = model.act(
					chat, self.tools, on_message=on_message, max_prediction_rounds=5, max_parallel_tool_calls=1
				)

				# Extract response
				response_text = self._extract_response(messages)

				if response_text:
					return {"success": True, "response": response_text}

			except Exception as e:
				frappe.log_error("SDK Act Error", str(e))

			# Fallback: Parse function calls from text
			response_text = self._fallback_function_parsing(messages)

			if response_text:
				return {"success": True, "response": response_text}

			# Final fallback
			return {"success": False, "response": "Unable to process the request"}

		except Exception as e:
			frappe.log_error("Enhanced Handler Error", str(e))
			return {"success": False, "error": str(e)}

	def _build_system_prompt(self) -> str:
		"""Build the system prompt with context variables injected."""

		# Get base instruction
		instruction = None
		if self.bot:
			if hasattr(self.bot, "instruction") and self.bot.instruction:
				instruction = self.bot.instruction
			elif hasattr(self.bot, "prompt") and self.bot.prompt:
				instruction = self.bot.prompt

		if not instruction:
			instruction = """You are a helpful AI assistant.

IMPORTANT: To call functions, use this exact format:
FUNCTION_CALL: function_name(param1="value1", param2="value2")

Available functions:
- get_document(doctype="Type", document_id="ID"): Get a document
- get_documents(doctype="Type", document_ids=["ID1", "ID2"]): Get multiple documents
- get_list(doctype="Type", filters={}, fields=[], limit=20): List documents"""

		# Always inject context variables, even if dynamic_instructions is not enabled
		# This ensures Nora always has context
		from frappe.utils import now_datetime, nowdate

		from raven.ai.handler import get_variables_for_instructions

		try:
			context_vars = get_variables_for_instructions()

			# Format date and time for better readability if needed
			if context_vars.get("current_time"):
				# Convert datetime object to string if necessary
				from datetime import datetime

				if isinstance(context_vars["current_time"], datetime):
					context_vars["current_datetime"] = context_vars["current_time"].strftime("%Y-%m-%d %H:%M:%S")
					context_vars["current_time"] = context_vars["current_time"].strftime("%H:%M:%S")

			# Ensure first_name is set (already handled in get_variables_for_instructions but double check)
			if not context_vars.get("first_name") and context_vars.get("full_name"):
				context_vars["first_name"] = (
					context_vars["full_name"].split()[0] if context_vars["full_name"] else "User"
				)

			# Always render the template with context variables
			# This ensures variables are replaced even if dynamic_instructions is not enabled
			instruction = frappe.render_template(instruction, context_vars)

			# If dynamic instructions is not enabled, also add a context block
			if not (
				self.bot and hasattr(self.bot, "dynamic_instructions") and self.bot.dynamic_instructions
			):
				context_block = f"""
=== CURRENT CONTEXT ===
User: {context_vars.get('full_name', 'Unknown')} ({context_vars.get('user_id', 'Unknown')})
Email: {context_vars.get('email', 'Unknown')}
Company: {context_vars.get('company', 'Unknown')}
Currency: {context_vars.get('currency', 'USD')}
Language: {context_vars.get('lang', 'EN')}
Current Date: {context_vars.get('current_date')}
Current Time: {context_vars.get('current_time')}
======================

"""
				instruction = context_block + instruction

		except Exception as e:
			frappe.log_error("Context Injection Error", str(e))

		return instruction

	def _add_history_to_chat(self, chat):
		"""Add conversation history to chat."""
		if not self.conversation_history:
			return

		# Merge consecutive assistant messages
		merged_history = []
		last_role = None
		last_content = ""

		for msg in self.conversation_history:
			role = msg.get("role", "user")
			content = msg.get("content", "")

			if not content:
				continue

			if role in ["assistant", "bot"]:
				if last_role in ["assistant", "bot"]:
					last_content = last_content + "\n" + content
				else:
					if last_role and last_content:
						merged_history.append({"role": last_role, "content": last_content})
					last_role = "assistant"
					last_content = content
			else:
				if last_role and last_content:
					merged_history.append({"role": last_role, "content": last_content})
				last_role = role
				last_content = content

		# Add last message
		if last_role and last_content:
			merged_history.append({"role": last_role, "content": last_content})

		# Add to chat
		for msg in merged_history:
			if msg["role"] == "user":
				chat.add_user_message(msg["content"])
			else:
				chat.add_assistant_response(msg["content"])

	def _extract_response(self, messages: list) -> str | None:
		"""Extract response from messages."""
		for msg in reversed(messages):
			msg_type = type(msg).__name__

			if "AssistantResponse" in msg_type:
				if hasattr(msg, "content"):
					if isinstance(msg.content, str):
						return msg.content
					elif isinstance(msg.content, list):
						for item in msg.content:
							if hasattr(item, "text"):
								return item.text
							elif isinstance(item, dict) and "text" in item:
								return item["text"]

		return None

	def _fallback_function_parsing(self, messages: list) -> str | None:
		"""
		Fallback: Parse and execute function calls from text.
		"""
		for msg in messages:
			if hasattr(msg, "content"):
				content_text = str(msg.content)

				# Parse function calls
				parsed_calls = FunctionCallParser.extract_all_calls(content_text, self.function_names)

				for func_name, func_args in parsed_calls:
					frappe.log_error("Fallback Parser", f"Found: {func_name}({func_args})")

					# Execute function
					for tool in self.tools:
						if hasattr(tool, "__name__") and tool.__name__ == func_name:
							try:
								result = tool(**func_args)

								# Format result
								if isinstance(result, dict):
									if "message" in result:
										return result["message"]
									elif "data" in result:
										return json.dumps(result["data"], ensure_ascii=False, indent=2)
									else:
										return json.dumps(result, ensure_ascii=False, indent=2)
								else:
									return str(result)

							except Exception as e:
								frappe.log_error(f"Fallback execution failed for {func_name}", str(e))

		return None


def process_with_lmstudio(bot, message: str, context: dict[str, Any]) -> dict:
	"""
	Main entry point for processing with enhanced handler.
	"""
	handler = EnhancedLMStudioHandler(bot, context)
	return handler.process(message)
