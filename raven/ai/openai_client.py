import frappe
from frappe import _
from openai import OpenAI


def get_open_ai_client():
	"""
	Get the OpenAI client
	"""

	raven_settings = frappe.get_cached_doc("Raven Settings")

	if not raven_settings.enable_ai_integration:
		frappe.throw(_("AI Integration is not enabled"))
	
	if not raven_settings.enable_openai_services:
		frappe.throw(_("OpenAI services are not enabled"))

	openai_api_key = raven_settings.get_password("openai_api_key")
	openai_organisation_id = (raven_settings.openai_organisation_id or "").strip()
	openai_project_id = (raven_settings.openai_project_id or "").strip()

	if raven_settings.openai_project_id:
		client = OpenAI(
			organization=raven_settings.openai_organisation_id,
			project=raven_settings.openai_project_id,
			api_key=openai_api_key,
			max_retries=1  # Limit retries to prevent duplicate responses
		)
	else:
		client = OpenAI(
			api_key=openai_api_key, 
			organization=raven_settings.openai_organisation_id,
			max_retries=1  # Limit retries to prevent duplicate responses
		)

def get_openai_models():
	"""
	Get the available OpenAI models
	"""
	client = get_open_ai_client()
	return client.models.list()


code_interpreter_file_types = [
	"pdf",
	"csv",
	"docx",
	"doc",
	"xlsx",
	"pptx",
	"txt",
	"png",
	"jpg",
	"jpeg",
	"md",
	"json",
	"html",
]

file_search_file_types = ["pdf", "csv", "doc", "docx", "json", "txt", "md", "html", "pptx"]
