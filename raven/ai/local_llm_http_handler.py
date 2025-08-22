"""
Local LLM handler using direct HTTP calls for Ollama, LocalAI and other HTTP-based providers.
Note: For LM Studio, use the SDK handler in raven.ai.lmstudio instead.
"""

import json

import frappe
import requests

from .function_executor import execute_raven_function


def local_llm_http_handler(bot, message: str, channel_id: str, conversation_history: list = None):
	"""
	HTTP handler for Local LLM providers like Ollama and LocalAI.

	Note: LM Studio should use the SDK handler in raven.ai.lmstudio.sdk_handler instead.
	This handler is for HTTP-only providers that don't have SDK support.
	"""

	# Get settings
	settings = frappe.get_single("Raven Settings")
	is_lm_studio = bot.model_provider == "Local LLM" and settings.local_llm_provider == "LM Studio"

	try:
		# Setup API endpoint and headers
		if bot.model_provider == "Local LLM":
			if not settings.local_llm_api_url:
				return {"response": "Local LLM API URL not configured", "success": False}
			base_url = settings.local_llm_api_url
			headers = {"Content-Type": "application/json"}
		else:
			api_key = settings.get_password("openai_api_key")
			if not api_key:
				return {"response": "OpenAI API key not configured", "success": False}
			base_url = "https://api.openai.com/v1"
			headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

		# Get functions from bot
		functions = []
		if hasattr(bot, "bot_functions") and bot.bot_functions:
			for func in bot.bot_functions:
				try:
					function_doc = frappe.get_doc("Raven AI Function", func.function)

					# Get params
					params = {}
					if hasattr(function_doc, "get_params") and callable(function_doc.get_params):
						params = function_doc.get_params()
					elif hasattr(function_doc, "params") and function_doc.params:
						try:
							params = json.loads(function_doc.params)
						except (json.JSONDecodeError, ValueError):
							params = {}

					# Remove additionalProperties
					if "additionalProperties" in params:
						del params["additionalProperties"]

					# Create function definition
					func_def = {
						"name": function_doc.function_name,
						"description": function_doc.description,
						"parameters": params,
					}
					functions.append(func_def)

				except Exception as e:
					# Error loading function - skip this function
					pass

		# Build initial messages
		messages = []

		# Build system prompt
		system_prompt = ""

		# Check if bot has custom instructions
		if bot.instruction:
			# For LM Studio with Qwen model, simplify long prompts to avoid hallucinations
			if is_lm_studio:
				# Simplify long prompts for LM Studio to prevent hallucinations with Qwen models
				system_prompt = (
					bot.instruction
					+ """
## FUNCTION CALLING RULES
When asked to perform actions or retrieve data:
1. Always use available functions
2. Never invent or hallucinate data
3. Call functions sequentially as needed"""
				)
			else:
				# Use full instructions if not too long
				system_prompt = bot.instruction

		# If no instructions, use a default
		if not system_prompt:
			system_prompt = """You are an intelligent AI assistant with access to business functions.

## CRITICAL RULES for function calling

When the user asks you to perform an action, follow these steps:

1. **Analyze the request**: Understand what needs to be done
2. **Call functions sequentially**: Some tasks require multiple function calls
3. **Use function results**: The result of one function may be needed for the next

### Important:
- Always check function descriptions for requirements
- Some functions require information from other functions first
- Continue calling functions until the task is complete
- When presenting lists or tables, use appropriate HTML formatting with <table class='table'>

You can call multiple functions in sequence. After each function call, I will provide the result, and you can then call the next function if needed."""

		messages.append({"role": "system", "content": system_prompt})

		# Add conversation history (last 20 messages only)
		if conversation_history:
			for msg in conversation_history[-20:]:
				messages.append(msg)

		# Add current message
		messages.append({"role": "user", "content": message})

		# Setup model name
		model_name = bot.model if bot.model else "local-model"
		if bot.model_provider == "Local LLM" and not bot.model:
			model_name = "local-model"

		# Maximum rounds for function calls
		max_rounds = 5  # Prevent infinite loops
		current_round = 0
		final_response = None
		all_function_results = []

		# Main loop for multiple rounds
		while current_round < max_rounds:
			current_round += 1

			# Prepare request data
			data = {
				"model": model_name,
				"messages": messages,
				"temperature": bot.temperature,
				"max_tokens": 4096,
			}

			# Add functions/tools based on provider
			if functions:
				if is_lm_studio:
					# LM Studio uses tools format
					tools = []
					for func in functions:
						tools.append({"type": "function", "function": func})
					data["tools"] = tools
				else:
					# Standard OpenAI format
					data["functions"] = functions

			# Make API call
			response = requests.post(
				f"{base_url}/chat/completions", headers=headers, json=data, timeout=120
			)
			response.raise_for_status()
			response_json = response.json()

			# Process response
			if "choices" not in response_json or len(response_json["choices"]) == 0:
				break

			choice = response_json["choices"][0]
			message_data = choice.get("message", {})

			# Extract function calls
			function_calls = []

			# Check for tool_calls (LM Studio format)
			if "tool_calls" in message_data and message_data["tool_calls"]:
				for tool_call in message_data["tool_calls"]:
					if tool_call.get("type") == "function":
						func_data = tool_call.get("function", {})
						func_name = func_data.get("name")
						try:
							args = json.loads(func_data.get("arguments", "{}"))
						except (json.JSONDecodeError, ValueError):
							args = {}
						function_calls.append({"name": func_name, "arguments": args, "id": tool_call.get("id")})

			# Check for function_call (OpenAI format)
			elif "function_call" in message_data and message_data["function_call"]:
				func_call = message_data["function_call"]
				func_name = func_call.get("name")
				try:
					args = json.loads(func_call.get("arguments", "{}"))
				except (json.JSONDecodeError, ValueError):
					args = {}
				function_calls.append({"name": func_name, "arguments": args})

			# Fallback: Check for text-based tool calls in content (for thinking models)
			elif (
				not function_calls and message_data.get("content") and "<tool_call>" in message_data["content"]
			):
				content = message_data["content"]

				# Extract tool call from content
				import re

				tool_call_match = re.search(r"<tool_call>\s*({.*?})\s*</tool_call>", content, re.DOTALL)
				if tool_call_match:
					try:
						tool_call_data = json.loads(tool_call_match.group(1))
						func_name = tool_call_data.get("name")
						args = tool_call_data.get("arguments", {})
						function_calls.append({"name": func_name, "arguments": args})
					except Exception as e:
						pass

			# Additional fallback: Check for OSS model format with commentary/constrain patterns
			elif not function_calls and message_data.get("content"):
				content = message_data["content"]

				# Pattern 1: "Need function_name" followed by structured tokens
				import re

				# Only apply OSS patterns for specific models known to use this format
				# Add model names here as we discover them
				oss_compatible_models = ["gpt-oss-20b", "gpt-oss", "local-model"]  # Add more as needed
				model_lower = model_name.lower() if model_name else ""

				# Check if this model should use OSS patterns
				should_use_oss_patterns = any(oss_model in model_lower for oss_model in oss_compatible_models)

				# Check for "Need function_name" pattern
				need_match = re.search(r"Need\s+(\w+)", content) if should_use_oss_patterns else None
				if need_match:
					func_name = need_match.group(1)

					# Try to extract JSON from various formats
					json_patterns = [
						r"<\|message\|>({.*?})(?:<\||\s|$)",  # <|message|>{json}
						r"<\|constrain\|>json<\|message\|>({.*?})(?:<\||\s|$)",  # <|constrain|>json<|message|>{json}
						r"\{[^}]*\}",  # Any JSON object
					]

					for pattern in json_patterns:
						json_match = re.search(pattern, content, re.DOTALL)
						if json_match:
							try:
								# Extract the JSON part
								json_str = json_match.group(1) if "(" in pattern else json_match.group(0)
								args = json.loads(json_str)
								function_calls.append({"name": func_name, "arguments": args})
								break
							except (json.JSONDecodeError, ValueError):
								continue

				# Pattern 2: Direct function reference like "functions.function_name" - only for OSS models
				if should_use_oss_patterns:
					func_ref_match = re.search(r"functions\.(\w+)", content)
					if not function_calls and func_ref_match:
						func_name = func_ref_match.group(1)

						# Try to find associated JSON
						for pattern in [r"<\|message\|>({.*?})(?:<\||\s|$)", r"\{[^}]*\}"]:
							json_match = re.search(pattern, content, re.DOTALL)
							if json_match:
								try:
									json_str = json_match.group(1) if "(" in pattern else json_match.group(0)
									args = json.loads(json_str)
									function_calls.append({"name": func_name, "arguments": args})
									break
								except (json.JSONDecodeError, ValueError):
									continue

			# If we have function calls, execute them
			if function_calls:
				# Check if we're repeating the same function call (infinite loop detection)
				if all_function_results:
					last_call = all_function_results[-1] if all_function_results else None
					current_call = {
						"function": function_calls[0]["name"],
						"arguments": function_calls[0].get("arguments", {}),
					}
					if (
						last_call
						and last_call["function"] == current_call["function"]
						and last_call["arguments"] == current_call["arguments"]
					):
						# Force a final response to break the loop
						from raven.ai.response_formatter import format_ai_response

						final_response = f"Based on the {current_call['function']} results, here's what I found:\n\n{json.dumps(last_call['result'], default=str, indent=2)}"
						final_response = format_ai_response(final_response)
						break

				# Add assistant message to conversation
				messages.append(message_data)

				# Execute all function calls
				for func_call in function_calls:
					func_name = func_call["name"]
					args = func_call.get("arguments", {})
					tool_call_id = func_call.get("id")

					# Pass channel_id for functions that might need it
					result = execute_raven_function(func_name, args, channel_id=channel_id)

					# Store result
					all_function_results.append({"function": func_name, "arguments": args, "result": result})

					# Add result to messages based on provider
					if is_lm_studio:
						# For LM Studio with tool_calls, we need a special approach
						# Many models don't properly handle the "tool" role and return raw JSON

						if tool_call_id:
							# Model supports tool_calls but may not handle tool role well
							# Solution: Send TWO messages:
							# 1. The tool response (for compatibility)
							# 2. A user prompt asking for formatting

							# First, add the standard tool response
							tool_response = {
								"role": "tool",
								"tool_call_id": tool_call_id,
								"content": json.dumps(result, default=str),
							}
							messages.append(tool_response)

							# Then add a user message asking for formatting
							# This ensures the model formats the response properly
							formatting_prompt = {
								"role": "user",
								"content": f"Format the above {func_name} results in a clear, readable way in French. Present it as a numbered list with key details, not as raw JSON.",
							}
							messages.append(formatting_prompt)
						else:
							# No tool_call_id - use user role
							# Add explicit formatting instruction
							formatted_result = json.dumps(result, default=str, indent=2)
							user_msg = f"""[Function Result - {func_name}]:
{formatted_result}

IMPORTANT: Please format this data as a readable response in French. Do not return raw JSON."""

							messages.append({"role": "user", "content": user_msg})
					else:
						# OpenAI format
						messages.append(
							{"role": "function", "name": func_name, "content": json.dumps(result, default=str)}
						)

				# Continue to next round to get the formatted response
				continue
			else:
				# No function calls - we have our final response
				content = message_data.get("content", "")

				# Check if the response looks like raw JSON (common issue with some models)
				# Also check if it contains the telltale signs of our function result
				needs_formatting = False

				# Check various patterns that indicate raw JSON response
				if content:
					# Pattern 1: Pure JSON
					if content.strip().startswith("{") and content.strip().endswith("}"):
						needs_formatting = True
					# Pattern 2: Text with embedded JSON
					elif "Based on the" in content and "{" in content:
						needs_formatting = True
					# Pattern 3: Contains product data
					elif '"products"' in content or "get_product_list" in content:
						needs_formatting = True
					# Pattern 4: Function result pattern
					elif '"status": "success"' in content:
						needs_formatting = True

				if needs_formatting:
					# Try to extract and format JSON from the response
					import re

					# Try to find JSON in the content
					json_match = re.search(r"\{.*\}", content, re.DOTALL)
					if json_match:
						try:
							json_str = json_match.group(0)
							json_data = json.loads(json_str)

							# If it's valid JSON, create a natural language response
							if isinstance(json_data, dict):
								# Product list response
								if "products" in json_data:
									products = json_data.get("products", [])
									response_parts = ["Voici les produits que j'ai trouvés :"]

									for i, product in enumerate(products[:10], 1):
										name = product.get("name", product.get("item_code", "Unknown"))
										price = product.get("price")
										stock = product.get("stock", 0)
										currency = product.get("currency", "CHF")
										unit = product.get("unit", "Unité")

										product_line = f"\n{i}. **{name}**"
										if price is not None and price > 0:
											product_line += f" - Prix: {currency} {price:.2f}"
										elif price == 0:
											product_line += f" - Prix: {currency} 0.00"
										else:
											product_line += " - Prix: Non défini"

										if stock and stock > 0:
											product_line += f" (Stock: {stock:.0f} {unit})"
										else:
											product_line += " (Stock: Épuisé)"

										response_parts.append(product_line)

									# Add summary
									total = json_data.get("total_count", len(products))
									if total > len(products):
										response_parts.append(f"\n_{total} produits au total, {len(products)} affichés_")

									final_response = "\n".join(response_parts)
								else:
									# Generic JSON response - try to format it nicely
									final_response = f"Voici les informations demandées :\n\n{json.dumps(json_data, indent=2, default=str, ensure_ascii=False)}"
							else:
								final_response = content
						except (json.JSONDecodeError, ValueError):
							# If JSON parsing fails, use content as-is
							final_response = content
					else:
						final_response = content
				else:
					final_response = content
				break

		# Format the final response
		if final_response:
			from raven.ai.response_formatter import format_ai_response

			final_response = format_ai_response(final_response)
		else:
			# No response received
			final_response = None

		return {"response": final_response, "success": True, "function_calls": all_function_results}

	except Exception as e:
		frappe.log_error("Local LLM Handler", f"Error: {str(e)}")
		return {"response": f"Error: {str(e)}", "success": False}
