"""
Improved agents integration with better import handling based on Desktop Raven approach.
"""

import asyncio
import json
import re
import traceback

import frappe
import openai

# Import agents SDK - the package is called 'agents' not 'openai_agents'
from agents import (
	Agent,
	CodeInterpreterTool,
	ComputerTool,
	FileSearchTool,
	HostedMCPTool,
	ImageGenerationTool,
	LocalShellTool,
	ModelSettings,
	OpenAIProvider,
	Runner,
	Tool,
	WebSearchTool,
	function_tool,
)
from frappe import _
from openai import AsyncOpenAI

from .functions import (
	cancel_document,
	create_document,
	delete_document,
	get_document,
	get_list,
	submit_document,
	update_document,
)

# //// Neoffice - the Raven AI Functions of a bot are run through function_executor, which replaced
# //// the deleted raven/ai/sdk_tools.py (7cdc45189, 2025-08-22 "Feat add SDK LM Studio"). See
# //// _create_function_tools() below.
from .function_executor import execute_raven_function


# //// Neoffice - local-LLM tool calling (6c5dfb539 + bbe50bc26, 2025-07-31/2025-08-05 "Fix: OpenAI Agents SDK Compatibility with Local LLMs").
# //// The OpenAI Agents SDK assumes native function calling. Models served by LM Studio / Ollama
# //// often do not have it, so this handler asks the model to emit <tool_call>{...}</tool_call> in
# //// plain text, parses it, runs the function and feeds the result back. Upstream has no such
# //// path: with a local model it simply produced an answer that mentioned a tool and did nothing.
async def _handle_local_llm_request(manager, agent, full_input, bot):
	"""
	Custom handler for Local LLMs that don't support native function calling.
	This implements a text-based tool calling mechanism.
	"""
	try:
		# Build messages for the API call
		# Decode HTML entities in instructions
		import html

		decoded_instructions = html.unescape(agent.instructions) if agent.instructions else ""
		messages = [{"role": "system", "content": decoded_instructions}]

		# Add conversation history
		if isinstance(full_input, list):
			messages.extend(full_input)
		else:
			messages.append({"role": "user", "content": full_input})

		# Make the initial API call
		response = await manager.client.chat.completions.create(
			model=bot.model,
			messages=messages,
			temperature=agent.model_settings.temperature,
			top_p=agent.model_settings.top_p,
			max_tokens=4096,
			# Don't include tools parameter for Local LLM
		)

		if not response or not response.choices:
			return {
				"response": "Failed to get response from Local LLM.",
				"success": False,
				"error": "No response from API",
			}

		# Extract the response
		choice = response.choices[0]
		raw_response = None

		# Try different fields where the content might be
		if hasattr(choice, "message") and choice.message:
			if hasattr(choice.message, "content") and choice.message.content:
				raw_response = choice.message.content
			elif hasattr(choice.message, "text"):
				raw_response = choice.message.text
		elif hasattr(choice, "text"):
			raw_response = choice.text

		if not raw_response:
			raw_response = ""
		else:
			# Convert HTML entities to their actual characters
			import html

			raw_response = html.unescape(raw_response)

		# If response only contains <think> tags without actual content, ask for action
		if raw_response and raw_response.strip().startswith("<think>") and "</think>" in raw_response:
			think_end = raw_response.find("</think>")
			if think_end != -1:
				content_after_think = raw_response[think_end + 8 :].strip()
				if not content_after_think or not ("<tool_call>" in content_after_think):
					# LLM only thought but didn't act
					# Ask for action
					messages.append({"role": "assistant", "content": raw_response})
					messages.append(
						{
							"role": "user",
							"content": "Please proceed with the tool calls needed to complete the user's request. Don't just think - act now using <tool_call>.",
						}
					)

					# Get new response
					action_response = await manager.client.chat.completions.create(
						model=bot.model,
						messages=messages,
						temperature=agent.model_settings.temperature,
						top_p=agent.model_settings.top_p,
						max_tokens=4096,
					)

					if action_response and action_response.choices:
						choice = action_response.choices[0]
						if hasattr(choice, "message") and choice.message and hasattr(choice.message, "content"):
							raw_response = choice.message.content
						elif hasattr(choice, "text"):
							raw_response = choice.text

		# Now handle tool calls in the response
		max_iterations = 10  # Increased to handle LLMs that retry with wrong parameters
		iteration = 0
		current_messages = messages.copy()

		while iteration < max_iterations and raw_response:
			# Check if response contains tool calls
			has_tool_call = "<tool_call>" in raw_response and "</tool_call>" in raw_response

			if has_tool_call:
				# Extract ALL tool calls from the response
				tool_call_matches = re.findall(
					r"<tool_call>\s*({.*?})\s*</tool_call>", raw_response, re.DOTALL
				)

				for tool_call_json in tool_call_matches:
					try:
						tool_call_data = json.loads(tool_call_json)
						tool_name = tool_call_data.get("name")
						tool_args = json.dumps(tool_call_data.get("arguments", {}))

						# Find and execute the tool
						tool_result = None
						tool_found = False
						for tool in manager.tools:
							if tool.name == tool_name:
								tool_found = True
								try:
									tool_result = await tool.on_invoke_tool(None, tool_args)
								except Exception as e:
									tool_result = f"Error executing tool: {str(e)}"
								break

						if not tool_result:
							tool_result = f"Tool '{tool_name}' not found or returned no result"

						# Add the exchange to messages
						current_messages.append({"role": "assistant", "content": raw_response})

						# Provide clear instruction to continue the workflow
						tool_result_msg = f"""Tool result for {tool_name}: {tool_result}

Now continue executing your workflow. According to your instructions, after getting context, you should proceed with the next step.

If you need to call another tool, use the <tool_call> format immediately. Do not just think about it - execute the next tool call now."""
						current_messages.append({"role": "user", "content": tool_result_msg})

						# Make another API call with the tool result
						follow_up = await manager.client.chat.completions.create(
							model=bot.model,
							messages=current_messages,
							temperature=agent.model_settings.temperature,
							top_p=agent.model_settings.top_p,
							max_tokens=4096,  # Increased to avoid truncation
						)

						if follow_up and follow_up.choices:
							choice = follow_up.choices[0]
							if hasattr(choice, "message") and choice.message and choice.message.content:
								raw_response = choice.message.content

								# If response only contains <think> tags, extract what's after them
								if raw_response.strip().startswith("<think>") and "</think>" in raw_response:
									think_end = raw_response.find("</think>")
									if think_end != -1:
										actual_response = raw_response[think_end + 8 :].strip()
										if actual_response:
											raw_response = actual_response
							else:
								raw_response = ""
						else:
							break

					except json.JSONDecodeError:
						break
					except Exception as e:
						break
				# After processing all tool calls in this response
				# Only increment iteration if we processed at least one tool call
				if len(tool_call_matches) > 0:
					iteration += 1
				else:
					# No tool calls found
					break
			else:
				# No tool calls in response
				break

		# Format the final response
		from raven.ai.response_formatter import format_ai_response

		# Check if we have actual content besides think tags
		if raw_response and "<think>" in raw_response and "</think>" in raw_response:
			# Extract content after think tags
			think_end = raw_response.rfind("</think>")  # Use rfind to get last occurrence
			if think_end != -1:
				content_after_think = raw_response[think_end + 8 :].strip()
				if content_after_think:
					# Use the content after think tags
					formatted_response = format_ai_response(content_after_think)
				else:
					# No content after think, use raw response
					formatted_response = "Processing your request..."
			else:
				formatted_response = (
					format_ai_response(raw_response) if raw_response else "No response content."
				)
		else:
			formatted_response = (
				format_ai_response(raw_response) if raw_response else "No response content."
			)

		return {"response": formatted_response, "success": True, "provider": "Local LLM"}

	except Exception as e:
		return {
			"response": "Error processing request with Local LLM.",
			"success": False,
			"error": str(e),
		}


class RavenAgentManager:
	"""Manages Raven agents with local LLM/OpenAI support"""

	# //// Neoffice - channel_id added (2026-09-04): a Custom Function that declares a channel_id
	# //// parameter receives it from function_executor, which is how a NORA function knows which
	# //// conversation it is answering. Defaults to None, so existing callers are unaffected.
	def __init__(self, bot_doc, file_handler=None, channel_id=None):
		self.bot_doc = bot_doc
		self.settings = frappe.get_single("Raven Settings")
		self.file_handler = file_handler
		self.channel_id = channel_id  # //// Neoffice - see the note above (2026-09-04).
		self._setup_client()
		self._setup_tools()

	def _setup_client(self):
		"""Configure OpenAI client based on provider"""
		if self.bot_doc.model_provider == "Local LLM" and self.settings.enable_local_llm:
			# Client for local LLM
			if not self.settings.local_llm_api_url:
				frappe.throw(_("Local LLM API URL is not configured in Raven Settings"))

			# Handle OpenAI Compatible provider differently
			if self.settings.local_llm_provider == "OpenAI Compatible":
				api_key = self.settings.get_password("openai_compatible_api_key") or "sk-key"
			else:
				api_key = "not-needed"  # LM Studio, Ollama, LocalAI don't require API key

			client = AsyncOpenAI(
				api_key=api_key,
				base_url=self.settings.local_llm_api_url,
			)

			# Create provider with use_responses=False for LM Studio
			self.provider = OpenAIProvider(
				openai_client=client, use_responses=False  # Force use of chat/completions endpoint
			)
		else:
			# Standard OpenAI client
			api_key = self.settings.get_password("openai_api_key")
			if not api_key:
				frappe.throw(_("OpenAI API key is not configured in Raven Settings"))

			client = AsyncOpenAI(
				api_key=api_key,
				organization=self.settings.openai_organisation_id,
				project=self.settings.openai_project_id if self.settings.openai_project_id else None,
			)

			# Create provider with use_responses=True for OpenAI
			self.provider = OpenAIProvider(
				openai_client=client, use_responses=True  # Use /v1/responses for OpenAI
			)

		# Keep client reference for backward compatibility
		self.client = client

	async def _test_api_connection(self):
		"""Test API connection before creating agent"""
		try:
			# Try a simple completion to test connectivity
			test_response = await self.client.chat.completions.create(
				model=self.bot_doc.model, messages=[{"role": "user", "content": "test"}], max_tokens=5
			)
			if not test_response or not test_response.choices:
				return False
			return True
		except Exception as e:
			# //// Neoffice - logging restored (2026-09-04). 87fa1010c (2025-08-04 "Fix AI Function Loading
			# //// and Response Formatting") had replaced upstream's frappe.log_error with `pass` here and at
			# //// six other sites of this file, so a wrong local_llm_api_url looked like a bot that simply
			# //// never answers, with nothing in Error Log to say why.
			frappe.log_error(
				"Raven AI: API connection test failed",
				f"Bot: {self.bot_doc.name}\n{frappe.get_traceback()}",
			)
			return False

	def _setup_tools(self):
		"""Create SDK Tools from existing functions"""
		self.tools = []

		# //// Neoffice - fixed 2026-09-04. This block used to import create_raven_tools from
		# //// raven/ai/sdk_tools.py, a module 7cdc45189 (2025-08-22 "Feat add SDK LM Studio") had deleted.
		# //// The ImportError landed in an `except ... pass`, so self.tools stayed empty and every agent
		# //// ran with NO Raven AI Function at all - only the CRUD tools appended below reached it - with
		# //// nothing in Error Log. The functions are now built here from the bot configuration and run
		# //// through function_executor, which is what replaced sdk_tools.
		try:
			raven_tools = self._create_function_tools()
			if raven_tools:
				self.tools.extend(raven_tools)
		# //// Neoffice - and a failure to build them is logged now (2026-09-04), see above.
		except Exception:
			frappe.log_error(
				"Raven AI: bot functions could not be loaded",
				f"Bot: {self.bot_doc.name}\n{frappe.get_traceback()}",
			)

		# Add CRUD tools
		crud_tools = self._create_crud_tools()
		if crud_tools:
			self.tools.extend(crud_tools)

		# Add file search tool if enabled for OpenAI
		if (
			hasattr(self.bot_doc, "enable_file_search")
			and self.bot_doc.enable_file_search
			and self.bot_doc.model_provider == "OpenAI"
		):
			try:
				# For OpenAI, we need to handle file search differently
				# The SDK doesn't have a built-in FileSearchTool yet
				# We'll create a custom tool that can access uploaded files
				file_search_tool = self._create_file_search_tool()
				if file_search_tool:
					self.tools.append(file_search_tool)
			except Exception as e:
				# //// Neoffice - logging restored (2026-09-04, swallowed by 87fa1010c): a bot with file search
				# //// enabled lost the tool without a word.
				frappe.log_error(
					"Raven AI: file search tool setup failed",
					f"Bot: {self.bot_doc.name}\n{frappe.get_traceback()}",
				)

		# Add Code Interpreter tool if enabled (only for OpenAI, not supported with Local LLM)
		if (
			hasattr(self.bot_doc, "enable_code_interpreter")
			and self.bot_doc.enable_code_interpreter
			and self.bot_doc.model_provider == "OpenAI"
		):
			try:
				# Create CodeInterpreterTool with proper configuration
				code_interpreter_tool = CodeInterpreterTool(
					tool_config={"type": "code_interpreter", "container": {"type": "auto"}}
				)

				self.tools.append(code_interpreter_tool)
			except Exception as e:
				# //// Neoffice - logging restored (2026-09-04, swallowed by 87fa1010c): the code interpreter
				# //// silently disappeared from a bot that had it enabled.
				frappe.log_error(
					"Raven AI: code interpreter tool setup failed",
					f"Bot: {self.bot_doc.name}\n{frappe.get_traceback()}",
				)

		# Only add conversation file tool for OpenAI, not Local LLM (content is pre-extracted for Local LLM)
		if (
			self.file_handler
			and self.file_handler.conversation_files
			and self.bot_doc.model_provider != "Local LLM"
		):
			conversation_file_tool = self.file_handler.create_file_analysis_tool()
			if conversation_file_tool:
				self.tools.append(conversation_file_tool)

	# //// Neoffice - added method (2026-09-04), replaces the create_raven_tools() of the deleted
	# //// raven/ai/sdk_tools.py. One SDK FunctionTool per Raven AI Function linked to the bot; the
	# //// call itself goes through raven/ai/function_executor.py, the module that replaced sdk_tools
	# //// (7cdc45189) and that the local-LLM path already uses.
	def _create_function_tools(self) -> list[Tool]:
		"""Build one SDK tool per Raven AI Function configured on the bot."""
		from agents import FunctionTool

		tools = []

		for func_link in self.bot_doc.bot_functions or []:
			try:
				function_doc = frappe.get_doc("Raven AI Function", func_link.function)
			except Exception:
				frappe.log_error(
					"Raven AI: function could not be loaded",
					f"Bot: {self.bot_doc.name}\nFunction: {func_link.function}\n{frappe.get_traceback()}",
				)
				continue

			params = {}
			if function_doc.params:
				try:
					params = json.loads(function_doc.params)
				except (json.JSONDecodeError, TypeError):
					frappe.log_error(
						"Raven AI: function parameters are not valid JSON",
						f"Function: {function_doc.name}\nParams: {function_doc.params}",
					)
					continue

			if not isinstance(params, dict) or not params:
				params = {"type": "object", "properties": {}}

			# strict_json_schema below is False, and the strict variant rejects the schemas stored on
			# Raven AI Function, so additionalProperties is dropped rather than trusted.
			params.pop("additionalProperties", None)

			tools.append(
				FunctionTool(
					name=function_doc.function_name,
					description=function_doc.description or function_doc.function_name,
					params_json_schema=params,
					on_invoke_tool=self._build_function_invoker(function_doc.name),
					strict_json_schema=False,
				)
			)

		return tools

	# //// Neoffice - added method (2026-09-04), see _create_function_tools() above.
	def _build_function_invoker(self, function_id: str):
		"""Return the async callback the SDK calls when the model uses `function_id`."""
		channel_id = self.channel_id

		async def invoke_tool(context, arguments: str) -> str:
			args = {}
			if arguments:
				try:
					args = json.loads(arguments)
				except (json.JSONDecodeError, TypeError):
					frappe.log_error(
						"Raven AI: model sent invalid tool arguments",
						f"Function: {function_id}\nArguments: {arguments}",
					)
					return json.dumps({"error": "Invalid arguments"})

			result = execute_raven_function(function_id, args, channel_id=channel_id)
			return json.dumps(result, default=str)

		return invoke_tool

	def _create_crud_tools(self) -> list[Tool]:
		"""Wrap CRUD functions as OpenAI Agents Tools"""

		tools = []

		# Tool for get_document
		@function_tool
		def get_document_tool(doctype: str, document_id: str) -> dict:
			"""Get a single document with permissions check

			Args:
			    doctype: The DocType name
			    document_id: The document ID
			"""
			return get_document(doctype, document_id)

		# Tool for create_document
		# //// Neoffice - strict_mode=False on the three tools below (2026-09-04). openai-agents builds a
		# //// STRICT JSON schema by default, and a strict schema forbids additionalProperties, which is
		# //// exactly what a `dict` parameter compiles to. With openai-agents 0.6.x the decorator raised
		# //// UserError at import of the tool, so _create_crud_tools() - and therefore _setup_tools() and
		# //// the whole RavenAgentManager constructor - blew up before any tool was registered. Found
		# //// while proving the sdk_tools fix on osiris; the other four tools take only strings and stay
		# //// strict.
		@function_tool(strict_mode=False)
		def create_document_tool(doctype: str, data: dict) -> dict:
			"""Create a new document in the database

			Args:
			    doctype: The DocType name
			    data: Document data as dictionary
			"""
			# Pass bot function if exists
			function = self._get_bot_function(doctype)
			return create_document(doctype, data, function)

		# Tool for update_document
		# //// Neoffice - strict_mode=False, see create_document_tool above (2026-09-04).
		@function_tool(strict_mode=False)
		def update_document_tool(doctype: str, document_id: str, data: dict) -> dict:
			"""Update a document in the database

			Args:
			    doctype: The DocType name
			    document_id: The document ID
			    data: Fields to update
			"""
			function = self._get_bot_function(doctype)
			return update_document(doctype, document_id, data, function)

		# Tool for delete_document
		@function_tool
		def delete_document_tool(doctype: str, document_id: str) -> dict:
			"""Delete a document from the database

			Args:
			    doctype: The DocType name
			    document_id: The document ID
			"""
			return delete_document(doctype, document_id)

		# Tool for get_list
		# //// Neoffice - strict_mode=False, see create_document_tool above (2026-09-04).
		@function_tool(strict_mode=False)
		def search_documents(
			doctype: str, filters: dict | None = None, fields: list[str] | None = None, limit: int = 20
		) -> list[dict]:
			"""Search documents in the database

			Args:
			    doctype: The DocType name
			    filters: Optional filters dictionary
			    fields: Optional list of fields to return
			    limit: Maximum number of results
			"""
			return get_list(doctype, filters, fields, limit)

		# Tool for submit_document
		@function_tool
		def submit_document_tool(doctype: str, document_id: str) -> dict:
			"""Submit a document (for submittable DocTypes)

			Args:
			    doctype: The DocType name
			    document_id: The document ID
			"""
			return submit_document(doctype, document_id)

		# Tool for cancel_document
		@function_tool
		def cancel_document_tool(doctype: str, document_id: str) -> dict:
			"""Cancel a submitted document

			Args:
			    doctype: The DocType name
			    document_id: The document ID
			"""
			return cancel_document(doctype, document_id)

		tools.extend(
			[
				get_document_tool,
				create_document_tool,
				update_document_tool,
				delete_document_tool,
				search_documents,
				submit_document_tool,
				cancel_document_tool,
			]
		)

		return tools

	def _create_file_search_tool(self):
		"""Create a file search tool for OpenAI bots using SDK's FileSearchTool"""
		try:
			from agents import FileSearchTool

			# First check if bot has a vector store ID directly stored
			vector_store_ids = []

			# Check if bot has openai_vector_store_id field
			if hasattr(self.bot_doc, "openai_vector_store_id") and self.bot_doc.openai_vector_store_id:
				vector_store_ids = [self.bot_doc.openai_vector_store_id]

			# If not found on bot, check the assistant
			elif hasattr(self.bot_doc, "openai_assistant_id") and self.bot_doc.openai_assistant_id:
				try:
					# Create a synchronous client for assistant operations
					from openai import OpenAI

					api_key = self.settings.get_password("openai_api_key")
					sync_client = OpenAI(
						api_key=api_key,
						organization=self.settings.openai_organisation_id,
						project=self.settings.openai_project_id if self.settings.openai_project_id else None,
					)

					assistant = sync_client.beta.assistants.retrieve(self.bot_doc.openai_assistant_id)

					# Check if assistant has vector store IDs in tool_resources
					if hasattr(assistant, "tool_resources") and assistant.tool_resources:
						# Access the vector store IDs
						file_search = getattr(assistant.tool_resources, "file_search", None)
						if file_search and hasattr(file_search, "vector_store_ids"):
							vs_ids = file_search.vector_store_ids
							if vs_ids:
								vector_store_ids = vs_ids

				except Exception as e:
					# //// Neoffice - logging restored (2026-09-04, swallowed by 87fa1010c): without the vector
					# //// store ids the bot answers as if it had no documents at all.
					frappe.log_error(
						"Raven AI: OpenAI assistant could not be read",
						f"Bot: {self.bot_doc.name}\n{frappe.get_traceback()}",
					)

			# If still no vector store, log and return None
			if not vector_store_ids:
				return None

			file_search_tool = FileSearchTool(
				vector_store_ids=vector_store_ids,
				max_num_results=5,
				include_search_results=True,  # Include the actual search results
			)

			return file_search_tool

		except ImportError:
			# The installed agents SDK has no FileSearchTool: an expected condition, not an error.
			return None
		# //// Neoffice - logging restored (2026-09-04, swallowed by 87fa1010c). Unlike the ImportError
		# //// just above, reaching this branch means the vector store lookup itself broke.
		except Exception as e:
			frappe.log_error(
				"Raven AI: file search tool creation failed",
				f"Bot: {self.bot_doc.name}\n{frappe.get_traceback()}",
			)
			return None

	def _get_bot_function(self, doctype: str):
		"""Get bot function configuration for a DocType"""
		for func in self.bot_doc.bot_functions:
			if func.linked_doctype == doctype:
				return func
		return None

	def _filter_tools_for_provider(self) -> list[Tool]:
		"""Filter tools based on the provider capabilities"""
		if self.bot_doc.model_provider == "Local LLM":
			# Filter out hosted tools that are not supported with ChatCompletions API
			filtered_tools = []
			hosted_tool_types = (
				CodeInterpreterTool,
				FileSearchTool,
				WebSearchTool,
				ComputerTool,
				HostedMCPTool,
				ImageGenerationTool,
				LocalShellTool,
			)

			for tool in self.tools:
				if isinstance(tool, hosted_tool_types):
					frappe.log_error(
						f"Skipping hosted tool {tool.name} for Local LLM - not supported with ChatCompletions API",
						"Tool Filtering",
					)
				else:
					filtered_tools.append(tool)

			return filtered_tools
		else:
			# For OpenAI, all tools are supported
			return self.tools

	def create_agent(self) -> Agent:
		"""Create main agent with bot configuration"""

		# Validate model configuration
		if not self.bot_doc.model:
			frappe.throw(_("Bot model is not configured"))

		# Dynamic instructions if needed
		instructions = self.bot_doc.instruction
		if self.bot_doc.dynamic_instructions:
			# Replace Jinja variables
			from jinja2 import Template

			template = Template(instructions)
			instructions = template.render(
				user=frappe.session.user,
				company=frappe.defaults.get_user_default("company"),
				# Add other contextual variables
			)

		# Enhance instructions with tool information if tools are available
		if self.tools:
			tool_descriptions = []
			for tool in self.tools:
				# Handle different tool types
				if hasattr(tool, "description"):
					tool_descriptions.append(f"- {tool.name}: {tool.description}")
				elif isinstance(tool, CodeInterpreterTool):
					tool_descriptions.append(
						"- code_interpreter: Execute Python code to analyze data, process files, and perform calculations"
					)
				else:
					tool_descriptions.append(f"- {tool.name}: {type(tool).__name__}")

			tools_instruction = f"""

You have access to the following tools/functions that you can use to help answer questions:

{chr(10).join(tool_descriptions)}

CRITICAL INSTRUCTIONS FOR TOOL USE:
1. When a user asks for information that these tools can provide, use the appropriate tool IMMEDIATELY.
2. When asked to "improve", "enhance", or "update" something, PROPOSE A SPECIFIC SOLUTION FIRST, then apply it when the user confirms.
3. When the user confirms with words like "ok", "yes", "apply", "do it", "applique cela", etc., USE THE APPROPRIATE TOOL to make the change.
4. Do NOT ask the user to provide information that you can generate or retrieve yourself.
5. Always read function descriptions carefully and follow any workflow instructions they contain.

NOTE: File content from uploaded documents is automatically extracted and included in the conversation, so you can directly answer questions about files without needing special tools.

IMPORTANT: When calling tools, the SDK will handle the tool execution automatically. Simply state your intent to use the tool and the SDK will execute it. Do not use XML tags like <tool_call> or any other custom format."""

			instructions = instructions + tools_instruction

		# Create model settings
		model_settings = ModelSettings(temperature=self.bot_doc.temperature, top_p=self.bot_doc.top_p)

		# Add reasoning_effort if available (for o-series models)
		if hasattr(self.bot_doc, "reasoning_effort") and self.bot_doc.reasoning_effort:
			model_settings.reasoning_effort = self.bot_doc.reasoning_effort

		# Create agent - ALWAYS pass empty list instead of None for tools
		# Get the model from the provider
		model = self.provider.get_model(self.bot_doc.model)

		# Filter tools based on provider capabilities
		filtered_tools = self._filter_tools_for_provider()

		agent = Agent(
			name=self.bot_doc.bot_name,
			instructions=instructions,
			model=model,  # Pass the model object from provider
			tools=filtered_tools if filtered_tools else [],  # Pass empty list, not None
			model_settings=model_settings,
		)

		# Ensure tools is always a list on the agent object
		if not hasattr(agent, "tools") or agent.tools is None:
			agent.tools = []

		return agent


# Async handler function that can be called from sync context
async def handle_ai_request_async(
	bot, message: str, channel_id: str, conversation_history: list = None, file_handler=None
):
	"""Handle AI request asynchronously"""
	try:

		# //// Neoffice - channel_id passed through (2026-09-04) so a Custom Function that declares a
		# //// channel_id parameter knows which conversation it is answering. See RavenAgentManager.
		manager = RavenAgentManager(bot, file_handler=file_handler, channel_id=channel_id)

		# No need to test API connection anymore - the SDK will handle errors
		agent = manager.create_agent()

		if not agent:
			return {
				"response": "Failed to create AI agent.",
				"success": False,
				"error": "Agent creation failed",
			}

		# Build input with proper conversation history format
		# Note: File content is now extracted upfront in ai.py and included in the message
		if conversation_history:
			# Convert conversation history to proper format for the SDK
			input_items = []

			# Add conversation history as separate items
			for msg in conversation_history:
				# Clean HTML and extract plain text content
				content = msg["content"]

				# Remove HTML details/summary tags for reasoning
				if "<details" in content and "</details>" in content:
					# Extract the main response after the details section
					# Remove the entire details block
					content = re.sub(r"<details.*?</details>", "", content, flags=re.DOTALL).strip()

				# Skip empty messages
				if not content:
					continue

				if msg["role"] == "user":
					input_items.append({"role": "user", "content": content})  # Use "role" not "type"
				elif msg["role"] == "assistant":
					input_items.append({"role": "assistant", "content": content})  # Use "role" not "type"

			# Add current message
			input_items.append({"role": "user", "content": message})
			full_input = input_items
		else:
			# No history, just the current message
			full_input = message

		try:
			# For Local LLM, always use direct API call to handle custom tool formats
			if bot.model_provider == "Local LLM":
				raise TypeError("Force fallback for Local LLM to handle custom tool calls")

			# Use Runner.run as a static method (not an instance)
			# Set max_turns to prevent infinite loops
			result = await Runner.run(agent, full_input, max_turns=5)

		except (TypeError, openai.NotFoundError) as e:
			# Handle both TypeError and NotFoundError (404) with fallback
			should_fallback = False

			if isinstance(e, TypeError) and "NoneType" in str(e) and "not iterable" in str(e):
				should_fallback = True
			elif isinstance(e, TypeError) and "Force fallback for Local LLM" in str(e):
				# Forced fallback for Local LLM to handle custom tool calls
				should_fallback = True
			elif isinstance(e, openai.NotFoundError):
				# 404 errors indicate the endpoint is not supported (like agents SDK endpoints on Ollama)
				should_fallback = True

			if should_fallback:
				# Try direct API call as fallback
				try:
					# For direct API calls, we need to manually add tool definitions
					# if the bot has tools configured
					tools_param = None
					if manager.tools:
						tools_param = []
						for tool in manager.tools:
							# Skip non-FunctionTool tools (like CodeInterpreterTool)
							# as they can't be converted to OpenAI function format
							if hasattr(tool, "description") and hasattr(tool, "params_json_schema"):
								# Convert FunctionTool to OpenAI function format
								tool_def = {
									"type": "function",
									"function": {
										"name": tool.name,
										"description": tool.description,
										"parameters": tool.params_json_schema,
									},
								}
								tools_param.append(tool_def)

					# Add instruction to encourage immediate tool use
					enhanced_instructions = (
						agent.instructions
						+ "\n\nIMPORTANT: When asked to perform an action, use your tools immediately. Do not overthink. Keep responses brief and action-oriented. When asked to improve something, propose a specific solution immediately. File content from uploaded documents is automatically extracted and included in the conversation - DO NOT use the analyze_conversation_file tool for files that are already in the conversation context, just use the extracted content provided."
					)

					# Build messages array with proper conversation history
					messages = [{"role": "system", "content": [{"type": "text", "text": enhanced_instructions}]}]

					# Add conversation history as separate messages
					if conversation_history:
						for msg in conversation_history:
							messages.append(
								{"role": msg["role"], "content": [{"type": "text", "text": msg["content"]}]}
							)

					# Add current user message
					messages.append({"role": "user", "content": [{"type": "text", "text": message}]})

					# Create the API call with or without tools
					api_params = {
						"model": bot.model,
						"messages": messages,
						"temperature": agent.model_settings.temperature,
						"top_p": agent.model_settings.top_p,
						# //// Neoffice - max_tokens 800 -> 4096 (6c5dfb539 + bbe50bc26, 2025-07-31/2025-08-05 "Fix: OpenAI Agents SDK Compatibility with Local LLMs"): 800 truncated a local model
						# //// mid-<tool_call>, so the JSON never parsed and the tool never ran.
						"max_tokens": 4096,  # Sufficient for reasoning and tool calls
					}

					# Add tools if available
					# //// Neoffice - local models are called WITHOUT the OpenAI tools parameter (6c5dfb539 + bbe50bc26, 2025-07-31/2025-08-05 "Fix: OpenAI Agents SDK Compatibility with Local LLMs"):
					# //// most of them reject the schema outright. The tools are described in the prompt instead and
					# //// parsed back out of the text (see _handle_local_llm_request above).
					# For Local LLM, we might not want to include tools in the API params
					# as they might not support the OpenAI tool format
					if tools_param and bot.model_provider != "Local LLM":
						api_params["tools"] = tools_param
						api_params["tool_choice"] = "auto"

					response = await manager.client.chat.completions.create(**api_params)

					if response and response.choices:
						choice = response.choices[0]
						# //// Neoffice - local-LLM response shapes (6c5dfb539 + bbe50bc26, 2025-07-31/2025-08-05 "Fix: OpenAI Agents SDK Compatibility with Local LLMs"): llama.cpp-style servers put
						# //// the answer in choice.text, LM Studio in choice.message.content, and some return an empty
						# //// string rather than null. Upstream reads choice.message.content only and crashed on the rest.
						# Handle different response formats for Local LLMs
						if hasattr(choice, "message") and choice.message and hasattr(choice.message, "content"):
							raw_response = choice.message.content
							# Special handling for empty content - check if it's actually None or empty string
							if raw_response == "" and bot.model_provider == "Local LLM":
								pass
						elif hasattr(choice, "text"):
							# Some Local LLMs return response in choice.text
							raw_response = choice.text
						elif hasattr(choice, "delta") and hasattr(choice.delta, "content"):
							# Some LLMs use delta for streaming-style responses
							raw_response = choice.delta.content
						else:
							# Try to extract content from any available field
							raw_response = None

						# Check if the response contains tool calls
						# //// Neoffice - defensive attribute walk for the same reason as above (6c5dfb539 + bbe50bc26, 2025-07-31/2025-08-05 "Fix: OpenAI Agents SDK Compatibility with Local LLMs").
						if (
							hasattr(choice, "message")
							and choice.message
							and hasattr(choice.message, "tool_calls")
							and choice.message.tool_calls
						):
							# Execute tool calls
							tool_results = []
							for tool_call in choice.message.tool_calls:
								tool_name = tool_call.function.name
								tool_args = tool_call.function.arguments
								# Find the tool in manager.tools
								tool_result = None
								for tool in manager.tools:
									if tool.name == tool_name:
										# Execute the tool
										tool_result = await tool.on_invoke_tool(None, tool_args)
										break

								if tool_result:
									tool_results.append({"tool_call_id": tool_call.id, "output": tool_result})

							# If we have tool results, make another API call with the results
							if tool_results:
								# Add assistant message with tool calls
								assistant_message = choice.message.model_dump()
								# Fix assistant message content format
								if isinstance(assistant_message.get("content"), str):
									assistant_message["content"] = [{"type": "text", "text": assistant_message["content"]}]

								messages = [
									{"role": "system", "content": [{"type": "text", "text": agent.instructions}]},
									{"role": "user", "content": [{"type": "text", "text": str(full_input)}]},
									assistant_message,
								]

								# Add tool results
								for result in tool_results:
									# Ensure output is a string
									output_content = result["output"]
									if not isinstance(output_content, str):
										output_content = json.dumps(output_content)

									messages.append(
										{
											"role": "tool",
											"content": [{"type": "text", "text": result["output"]}],
											"tool_call_id": result["tool_call_id"],
										}
									)

								# Make final API call
								final_response = await manager.client.chat.completions.create(
									model=bot.model,
									messages=messages,
									temperature=agent.model_settings.temperature,
									top_p=agent.model_settings.top_p,
									max_tokens=2000,
								)

								if final_response and final_response.choices:
									raw_response = final_response.choices[0].message.content
								else:
									raw_response = "Failed to get final response after tool execution."
							else:
								raw_response = "Tool execution failed - no results obtained."
						else:
							# No tool calls, check if the response contains custom tool call format
							raw_response = choice.message.content

							# Check for custom <tool_call> format in the response
							if raw_response and "<tool_call>" in raw_response and "</tool_call>" in raw_response:
								# Extract tool call from response
								tool_call_match = re.search(
									r"<tool_call>\s*({.*?})\s*</tool_call>", raw_response, re.DOTALL
								)

								if tool_call_match:
									try:
										# Parse the tool call
										tool_call_data = json.loads(tool_call_match.group(1))
										tool_name = tool_call_data.get("name")
										tool_args = json.dumps(tool_call_data.get("arguments", {}))

										# Find and execute the tool
										tool_result = None
										for tool in manager.tools:
											if tool.name == tool_name:
												# Execute the tool
												tool_result = await tool.on_invoke_tool(None, tool_args)
												break

										if tool_result:
											# Remove the tool call from the response
											response_without_tool = re.sub(
												r"<tool_call>.*?</tool_call>", "", raw_response, flags=re.DOTALL
											).strip()

											# Parse the tool result if it's JSON
											try:
												result_data = json.loads(tool_result)
												if isinstance(result_data, dict) and "result" in result_data:
													# Format the result nicely
													formatted_result = "Voici les produits trouvés :\n\n"
													for item in result_data["result"]:
														if isinstance(item, dict):
															formatted_result += f"• {item.get('name', 'Sans nom')}\n"

													# Add warning if present
													if "warning" in result_data:
														formatted_result += f"\n⚠️ {result_data['warning']}"

													raw_response = (
														response_without_tool + "\n\n" + formatted_result
														if response_without_tool
														else formatted_result
													)
												else:
													# Not the expected format, use as is
													raw_response = f"{response_without_tool}\n\n{tool_result}"
											except Exception:
												# Not JSON or parsing failed, use as is
												raw_response = f"{response_without_tool}\n\n{tool_result}"
										else:
											frappe.log_error(
												f"Tool '{tool_name}' not found or execution failed", "Custom Tool Call Error"
											)

									except json.JSONDecodeError as e:
										frappe.log_error(
											f"Failed to parse tool call JSON: {str(e)}\nContent: {tool_call_match.group(1)}",
											"Tool Call Parse Error",
										)
									except Exception as e:
										frappe.log_error(
											f"Error executing custom tool call: {str(e)}", "Tool Call Execution Error"
										)

						# Format the response
						from raven.ai.response_formatter import format_ai_response

						# Log the raw response

						formatted_response = (
							format_ai_response(raw_response) if raw_response else "No response content."
						)

						result = type("Result", (), {"final_output": formatted_response})()
					else:
						# //// Neoffice - TO REVIEW: upstream raises "No response from API"; here the absence of a response
						# //// becomes raw_response = None and the flow continues (87fa1010c, 2025-08-04).
						# No response or no choices
						raw_response = None

					# //// Neoffice - fixed 2026-09-04. 87fa1010c (2025-08-04) manufactured a fake Result object
					# //// whose final_output was the sentence "Failed to get response from API", so the failure
					# //// was delivered to the user as if the assistant had written it, and nothing reached
					# //// Error Log. It is now logged and returned as an explicit failure; raven/ai/ai.py turns
					# //// success=False into the user-facing error message.
					if "result" not in locals():
						frappe.log_error(
							"Raven AI: no usable response from the provider",
							f"Bot: {bot.name}\nModel: {bot.model}\nProvider: {bot.model_provider}",
						)
						return {
							"response": _("Sorry, I could not get a response from the AI provider."),
							"success": False,
							"error": "No response from API",
						}

				# //// Neoffice - fixed 2026-09-04. 87fa1010c (2025-08-04) turned this exception into a fake
				# //// Result whose final_output was "Error: <exception>", i.e. the traceback text was posted
				# //// in the chat as the assistant's answer and never logged. Logged and returned as a
				# //// failure now; the detail still reaches the user when bot.debug_mode is on, through
				# //// raven/ai/ai.py.
				except Exception as api_e:
					frappe.log_error(
						"Raven AI: direct API fallback failed",
						f"Bot: {bot.name}\nModel: {bot.model}\n{frappe.get_traceback()}",
					)
					return {
						"response": _("Sorry, I could not get a response from the AI provider."),
						"success": False,
						"error": str(api_e),
					}
			else:
				raise

		# Format the response if not already formatted
		from raven.ai.response_formatter import format_ai_response

		final_response = result.final_output

		# Check if response needs formatting (contains think tags or boxed notation)
		if "<think>" in final_response or "\\boxed{" in final_response:
			final_response = format_ai_response(final_response)

		# //// Neoffice - dead branch kept as a marker (6c5dfb539 + bbe50bc26, 2025-07-31/2025-08-05 "Fix: OpenAI Agents SDK Compatibility with Local LLMs"): a local model can still
		# //// emit an unexecuted <tool_call> here. TO REVIEW: the body is `pass` - it detects the case and
		# //// does nothing with it.
		# IMPORTANT: Check if the response contains unexecuted tool calls
		# This can happen if the SDK doesn't support native function calling
		if "<tool_call>" in final_response and "</tool_call>" in final_response:
			# The response contains tool calls that weren't executed
			# This means we need to handle them manually
			pass

		return {
			"response": final_response,
			"success": True,
			"provider": bot.model_provider if hasattr(bot, "model_provider") else "OpenAI",
		}

	# //// Neoffice - the top-level "AI Agent Error" log restored (2026-09-04); 87fa1010c (2025-08-04)
	# //// had dropped it, and this is the last place an agent failure can be seen at all. The returned
	# //// dict is unchanged, so the user still gets the message raven/ai/ai.py builds from it.
	except Exception as e:
		frappe.log_error(
			"Raven AI: agent request failed",
			f"Bot: {bot.name}\nChannel: {channel_id}\n{frappe.get_traceback()}",
		)
		return {
			"response": "I encountered an error while processing your request.",
			"success": False,
			"error": str(e) if bot.debug_mode else None,
		}


def handle_ai_request_sync(
	bot, message: str, channel_id: str, conversation_history: list = None, file_handler=None
):
	"""Synchronous wrapper for async AI request handling"""
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)
	try:
		return loop.run_until_complete(
			handle_ai_request_async(bot, message, channel_id, conversation_history, file_handler)
		)
	finally:
		loop.close()
