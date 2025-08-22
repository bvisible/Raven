"""
Module import and structure tests
"""

from .base import BaseTestCase


class ModuleTests(BaseTestCase):
	"""Test module imports and basic structure"""

	def run(self) -> bool:
		"""Run module tests"""
		if self.verbose:
			print("\n" + "=" * 60)
			print("  MODULE TESTS")
			print("=" * 60)

		success = True

		# Test core modules
		modules = [
			("raven.ai.ai", "Main AI module"),
			("raven.ai.functions", "Functions module"),
			("raven.ai.function_executor", "Function executor"),
			("raven.ai.response_formatter", "Response formatter"),
			("raven.ai.agents_integration", "OpenAI agents"),
			("raven.ai.lmstudio", "LM Studio package"),
			("raven.ai.lmstudio.sdk_handler", "SDK handler"),
			("raven.ai.local_llm_http_handler", "HTTP handler"),
		]

		for module_path, description in modules:
			try:
				__import__(module_path, fromlist=[""])
				self.record_test(f"Import {description}", True, module_path)
			except ImportError as e:
				self.record_test(f"Import {description}", False, str(e))
				success = False

		# Test module structure
		try:
			from raven.ai.lmstudio import LMStudioClient, lmstudio_sdk_handler, test_lmstudio_connection

			self.record_test("LM Studio exports", True, "All exports available")
		except ImportError as e:
			self.record_test("LM Studio exports", False, str(e))
			success = False

		# Test function executor
		try:
			from raven.ai.function_executor import execute_raven_function

			self.record_test("Function executor import", True)
		except ImportError as e:
			self.record_test("Function executor import", False, str(e))
			success = False

		return success
