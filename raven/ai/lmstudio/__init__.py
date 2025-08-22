"""
LM Studio SDK Integration for Raven AI
"""

from .enhanced_handler import EnhancedLMStudioHandler as LMStudioClient
from .sdk_handler import lmstudio_sdk_handler


def test_lmstudio_connection():
	"""Test LM Studio connection."""
	try:
		import frappe
		import lmstudio as lms

		# Get URL from Raven Settings
		try:
			raven_settings = frappe.get_single("Raven Settings")
			if raven_settings.enable_local_llm and raven_settings.local_llm_api_url:
				url = raven_settings.local_llm_api_url
				# Clean URL - remove protocol and /v1
				if url.startswith("https://"):
					url = url.replace("https://", "").replace("/v1", "")
				elif url.startswith("http://"):
					url = url.replace("http://", "").replace("/v1", "")

				client = lms.Client(api_host=url)
				model = client.llm  # property, not method
				return {"status": "success", "message": f"LM Studio connected to {url}"}
		except Exception:
			pass

		# Try default localhost
		try:
			model = lms.llm()  # This uses the convenience API
			return {"status": "success", "message": "LM Studio connected (localhost)"}
		except Exception:
			pass

		return {"status": "error", "message": "No LM Studio connection available"}
	except Exception as e:
		return {"status": "error", "message": str(e)}


__all__ = ["lmstudio_sdk_handler", "test_lmstudio_connection", "LMStudioClient"]
