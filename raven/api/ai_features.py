import frappe
import openai
import json
from typing import Dict, Any, Optional

from raven.ai.handler import get_variables_for_instructions


@frappe.whitelist()
def get_instruction_preview(instruction):
	"""
	Function to get the rendered instructions for the bot
	"""
	frappe.has_permission(doctype="Raven Bot", ptype="write", throw=True)

	instructions = frappe.render_template(instruction, get_variables_for_instructions())
	return instructions


@frappe.whitelist()
def get_saved_prompts(bot: str = None):
	"""
	API to get the saved prompt for a user/bot/global
	"""
	or_filters = [["is_global", "=", 1], ["owner", "=", frappe.session.user]]

	prompts = frappe.get_list(
		"Raven Bot AI Prompt", or_filters=or_filters, fields=["name", "prompt", "is_global", "raven_bot"]
	)

	# Order by ones with the given bot
	prompts = sorted(prompts, key=lambda x: x.get("raven_bot") == bot, reverse=True)

	return prompts


@frappe.whitelist()
def get_open_ai_version():
	"""
	API to get the version of the OpenAI Python client
	"""
	frappe.has_permission(doctype="Raven Bot", ptype="read", throw=True)
	return openai.__version__

def get_openai_available_models():
	"""
	API to get the available OpenAI models for assistants
	"""
	frappe.has_permission(doctype="Raven Bot", ptype="read", throw=True)
	from raven.ai.openai_client import get_openai_models

	models = get_openai_models()

	valid_prefixes = ["gpt-4", "gpt-3.5", "o1", "o3-mini"]

	# Model should not contain these words
	invalid_models = ["realtime", "transcribe", "search", "audio"]

	compatible_models = []

	for model in models:
		if any(model.id.startswith(prefix) for prefix in valid_prefixes):
			if not any(word in model.id for word in invalid_models):
				compatible_models.append(model.id)

	return compatible_models

@frappe.whitelist()
def test_llm_configuration():
	"""
	Test the OpenAI and/or local LLM configuration
	"""
	frappe.has_permission(doctype="Raven Settings", ptype="read", throw=True)
	
	results: Dict[str, Any] = {
		"openai": {"status": "not_tested", "message": "OpenAI integration not enabled"},
		"local_llm": {"status": "not_tested", "message": "Local LLM integration not enabled"}
	}
	
	settings = frappe.get_doc("Raven Settings")
	
	# Test OpenAI configuration if enabled
	if settings.enable_ai_integration:
		try:
			# Make a simple API call to OpenAI to verify credentials
			client = openai.OpenAI(
				api_key=settings.get_password("openai_api_key"),
				organization=settings.openai_organisation_id
			)
			
			# List models (lightweight API call)
			models = client.models.list()
			
			results["openai"] = {
				"status": "success",
				"message": f"OpenAI API connection successful. Found {len(models.data)} models available."
			}
		except Exception as e:
			error_message = str(e)
			results["openai"] = {
				"status": "error",
				"message": f"OpenAI API connection failed: {error_message}"
			}
	
	# Test local LLM configuration if enabled
	if settings.enable_local_llm:
		try:
			from openai import OpenAI
			from raven.ai.sdk_agents import ModelProvider
			
			provider = settings.local_llm_provider
			api_url = settings.local_llm_api_url
			
			if not api_url:
				results["local_llm"] = {
					"status": "error",
					"message": f"Local LLM API URL not configured for provider: {provider}"
				}
			else:
				# Set correct API key based on provider
				api_key = "sk-111222333"  # Dummy key, these providers typically don't check the key
				
				# Create client
				client = OpenAI(
					api_key=api_key,
					base_url=api_url
				)
				
				# Make a lightweight call to test connectivity
				try:
					# Try to list models (this works with most OpenAI-compatible APIs)
					models = client.models.list()
					results["local_llm"] = {
						"status": "success",
						"message": f"{provider} API connection successful. Found {len(models.data)} models available."
					}
				except Exception:
					# If models.list fails, try a simple chat completion as fallback
					try:
						# Use a minimal prompt to test connectivity
						response = client.chat.completions.create(
							model="default",  # Use a generic model name, will be overridden by most local providers
							messages=[{"role": "user", "content": "Hello"}],
							max_tokens=5  # Keep it minimal
						)
						results["local_llm"] = {
							"status": "success",
							"message": f"{provider} API connection successful."
						}
					except Exception as e2:
						# Both methods failed
						results["local_llm"] = {
							"status": "error",
							"message": f"{provider} API connection failed: {str(e2)}"
						}
		except Exception as e:
			error_message = str(e)
			results["local_llm"] = {
				"status": "error",
				"message": f"Local LLM API connection failed: {error_message}"
			}
	
	return results


@frappe.whitelist()
def test_model_compatibility(provider: Optional[str] = None, model_name: Optional[str] = None):
	"""
	Test if a specific model is compatible with the OpenAI Agents SDK tool calling capabilities
	
	Args:
		provider: The model provider (OpenAI, LocalLLM, etc)
		model_name: The name of the model to test
		
	Returns:
		Dict with test results
	"""
	frappe.has_permission(doctype="Raven Bot", ptype="write", throw=True)
	
	settings = frappe.get_doc("Raven Settings")
	
	result = {
		"status": "not_tested",
		"message": "Model compatibility not tested",
		"tool_support": False,
		"details": ""
	}
	
	if not provider:
		result["status"] = "error"
		result["message"] = "Provider not specified"
		return result
		
	if not model_name:
		result["status"] = "error"
		result["message"] = "Model name not specified"
		return result
	
	try:
		# Handle local LLM provider which requires resolution from settings
		actual_provider = provider
		if provider == "LocalLLM":
			if not settings.enable_local_llm:
				result["status"] = "error"
				result["message"] = "Local LLM integration not enabled in settings"
				return result
				
			actual_provider = settings.local_llm_provider
		
		# Set up the client based on the provider
		if provider == "OpenAI":
			if not settings.enable_ai_integration:
				result["status"] = "error"
				result["message"] = "OpenAI integration not enabled in settings"
				return result
				
			from openai import OpenAI
			client = OpenAI(
				api_key=settings.get_password("openai_api_key"),
				organization=settings.openai_organisation_id
			)
			
			api_url = None  # Default OpenAI API
			
		elif provider == "LocalLLM" or provider in ["LM Studio", "Ollama", "LocalAI"]:
			if not settings.enable_local_llm:
				result["status"] = "error"
				result["message"] = "Local LLM integration not enabled in settings"
				return result
				
			api_url = settings.local_llm_api_url
			if not api_url:
				result["status"] = "error"
				result["message"] = f"Local LLM API URL not configured for provider: {actual_provider}"
				return result
				
			from openai import OpenAI
			client = OpenAI(
				api_key="sk-111222333",  # Dummy key, local providers typically don't check
				base_url=api_url
			)
		else:
			result["status"] = "error"
			result["message"] = f"Unsupported provider: {provider}"
			return result
		
		# Test basic connectivity first
		try:
			# First, check if we can connect at all
			response = client.chat.completions.create(
				model=model_name,
				messages=[{"role": "user", "content": "Hello"}],
				max_tokens=5
			)
			
			if not response or not response.choices or not response.choices[0].message:
				result["status"] = "error"
				result["message"] = f"Connection successful, but received invalid response format from {actual_provider}"
				return result
				
			# Connection successful, now test tool calling capabilities
			try:
				# Define a simple tool for testing
				tools = [
					{
						"type": "function",
						"function": {
							"name": "get_weather",
							"description": "Get the current weather",
							"parameters": {
								"type": "object",
								"properties": {
									"location": {
										"type": "string",
										"description": "The city and state, e.g. San Francisco, CA"
									}
								},
								"required": ["location"]
							}
						}
					}
				]
				
				# Test tool calling with a prompt that should trigger tool use
				tool_test_response = client.chat.completions.create(
					model=model_name,
					messages=[{"role": "user", "content": "What's the weather like in Paris?"}],
					tools=tools,
					tool_choice="auto",
					max_tokens=256
				)
				
				# Check if the model actually used the tool
				if tool_test_response.choices and tool_test_response.choices[0].message:
					message = tool_test_response.choices[0].message
					if message.tool_calls and len(message.tool_calls) > 0:
						# Tool was used - model supports tool calling!
						result["status"] = "success"
						result["message"] = f"Model '{model_name}' successfully supports tool calling"
						result["tool_support"] = True
						result["details"] = "The model correctly called the weather tool when asked about the weather."
					else:
						# Tool was not used - might still support tools but didn't choose to use them
						result["status"] = "warning"
						result["message"] = f"Model '{model_name}' may support tool calling but did not use the provided tool"
						result["tool_support"] = False
						result["details"] = "The model did not use the provided tool when expected to. This could mean the model doesn't fully support tool calling, or it chose not to use the tool in this instance."
				else:
					result["status"] = "error"
					result["message"] = f"Received invalid response during tool compatibility test"
					result["details"] = "The response from the model did not contain expected message structure."
					
			except Exception as e:
				# If tool test fails but basic connectivity worked, it suggests the model doesn't support tools
				result["status"] = "warning"
				result["message"] = f"Model '{model_name}' likely does not support tool calling"
				result["tool_support"] = False
				result["details"] = f"Error during tool compatibility test: {str(e)}"
				
		except Exception as e:
			# Basic connectivity failed
			result["status"] = "error"
			result["message"] = f"Failed to connect to model '{model_name}'"
			result["details"] = f"Error: {str(e)}"
			
	except Exception as e:
		# General error
		result["status"] = "error"
		result["message"] = "An error occurred during the compatibility test"
		result["details"] = f"Error: {str(e)}"
		
	return result
