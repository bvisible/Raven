import frappe
from frappe import _
from openai import OpenAI, AzureOpenAI


def get_open_ai_client():
	"""
	Get the OpenAI client or AzureOpenAI client based on settings
	"""

	raven_settings = frappe.get_cached_doc("Raven Settings")

	if not raven_settings.enable_ai_integration:
		frappe.throw(_("AI Integration is not enabled"))

	# Check if Azure OpenAI is enabled
	if raven_settings.get("use_azure_openai") and raven_settings.get("azure_openai_api_key"):
		azure_api_key = raven_settings.get_password("azure_openai_api_key")
		azure_endpoint = raven_settings.get("azure_openai_endpoint")
		azure_api_version = raven_settings.get("azure_openai_api_version") or "2023-05-15"
		
		if not azure_endpoint:
			frappe.throw(_("Azure OpenAI Endpoint is required when using Azure OpenAI"))
		
		client = AzureOpenAI(
			api_key=azure_api_key,
			api_version=azure_api_version,
			azure_endpoint=azure_endpoint
		)
		
		return client
	
	# Regular OpenAI client
	openai_api_key = raven_settings.get_password("openai_api_key")

	if raven_settings.openai_project_id:
		client = OpenAI(
			organization=raven_settings.openai_organisation_id,
			project=raven_settings.openai_project_id,
			api_key=openai_api_key,
		)

		return client

	else:
		client = OpenAI(api_key=openai_api_key, organization=raven_settings.openai_organisation_id)

		return client
