import frappe
import openai
from typing import Dict

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


@frappe.whitelist()
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
def test_model_compatibility(provider: str, model_name: str) -> Dict[str, str]:
	"""
	Test if a model is compatible with the tool calling features required by Raven
	"""
	frappe.has_permission(doctype="Raven Bot", ptype="read", throw=True)
	
	settings = frappe.get_doc("Raven Settings")
	
	try:
		if provider == "OpenAI":
			if not settings.enable_openai_services:
				return {"status": "error", "message": "OpenAI services are not enabled"}
			
			from openai import OpenAI
			client = OpenAI(
				api_key=settings.get_password("openai_api_key"),
				organization=settings.openai_organisation_id
			)
			
			# Test the model with a simple tool call
			response = client.chat.completions.create(
				model=model_name,
				messages=[{"role": "user", "content": "What is 2+2?"}],
				tools=[{
					"type": "function",
					"function": {
						"name": "calculate",
						"description": "Perform a calculation",
						"parameters": {
							"type": "object",
							"properties": {
								"expression": {"type": "string"}
							},
							"required": ["expression"]
						}
					}
				}],
				max_tokens=10
			)
			
			# Check if the model can do tool calls
			if hasattr(response.choices[0].message, 'tool_calls'):
				return {
					"status": "success",
					"message": f"✅ {model_name} is compatible with Raven AI features"
				}
			else:
				return {
					"status": "warning",
					"message": f"⚠️ {model_name} works but may have limited tool support"
				}
				
		else:  # Local LLM providers
			if not settings.enable_local_llm:
				return {"status": "error", "message": "Local LLM is not enabled"}
			
			api_url = settings.local_llm_api_url
			if not api_url:
				return {"status": "error", "message": f"API URL not configured for {provider}"}
			
			from openai import OpenAI
			client = OpenAI(
				api_key="sk-111222333",  # Dummy key for local providers
				base_url=api_url
			)
			
			# Test basic connectivity
			response = client.chat.completions.create(
				model=model_name,
				messages=[{"role": "user", "content": "Hello"}],
				max_tokens=5
			)
			
			# Test tool calling capability (may fail for some local models)
			try:
				tool_response = client.chat.completions.create(
					model=model_name,
					messages=[{"role": "user", "content": "What is 2+2?"}],
					tools=[{
						"type": "function",
						"function": {
							"name": "calculate",
							"description": "Perform a calculation",
							"parameters": {
								"type": "object",
								"properties": {
									"expression": {"type": "string"}
								},
								"required": ["expression"]
							}
						}
					}],
					max_tokens=10
				)
				
				if hasattr(tool_response.choices[0].message, 'tool_calls'):
					return {
						"status": "success",
						"message": f"✅ {model_name} on {provider} is fully compatible"
					}
				else:
					return {
						"status": "success",
						"message": f"✅ {model_name} on {provider} works (limited tool support)"
					}
			except:
				return {
					"status": "success",
					"message": f"✅ {model_name} on {provider} is connected (no tool support)"
				}
				
	except Exception as e:
		return {
			"status": "error",
			"message": f"❌ Error testing {model_name}: {str(e)}"
		}
