"""
Integration tests for complete workflow
"""

import frappe

from .base import BaseTestCase


class IntegrationTests(BaseTestCase):
	"""Test end-to-end integration"""

	def run(self) -> bool:
		"""Run integration tests"""
		if self.verbose:
			print("\n" + "=" * 60)
			print("  INTEGRATION TESTS")
			print("=" * 60)

		success = True

		# Test bot configurations
		if not self._test_bot_configs():
			success = False

		# Test settings integration
		if not self._test_settings():
			success = False

		# Test message processing pipeline
		if not self._test_message_pipeline():
			success = False

		# Test error handling
		if not self._test_error_handling():
			success = False

		return success

	def _test_bot_configs(self) -> bool:
		"""Test bot configurations"""
		try:
			# Get all AI bots
			bots = frappe.db.sql(
				"""
                SELECT
                    rb.name,
                    rb.bot_name,
                    rb.model_provider,
                    rb.model,
                    rb.is_ai_bot,
                    COUNT(rbf.name) as function_count
                FROM `tabRaven Bot` rb
                LEFT JOIN `tabRaven Bot Functions` rbf ON rb.name = rbf.parent
                WHERE rb.is_ai_bot = 1
                GROUP BY rb.name
            """,
				as_dict=True,
			)

			bot_count = len(bots)

			if self.verbose and bot_count > 0:
				print(f"  Found {bot_count} AI bots:")
				for bot in bots[:3]:
					print(f"    • {bot['bot_name']} ({bot['model_provider']})")
					print(f"      Model: {bot['model'] or 'auto'}")
					print(f"      Functions: {bot['function_count']}")

			# Check for Nora (production bot)
			has_nora = any(bot["name"] == "Nora" for bot in bots)

			if has_nora:
				self.record_test("Production Bot (Nora)", True, "Configured")

			return self.record_test("Bot Configurations", bot_count > 0, f"Found {bot_count} AI bots")

		except Exception as e:
			return self.record_test("Bot Configurations", False, str(e))

	def _test_settings(self) -> bool:
		"""Test Raven Settings configuration"""
		try:
			settings = frappe.get_single("Raven Settings")

			# Check AI integration
			ai_enabled = getattr(settings, "enable_ai_integration", False)

			# Check LLM provider
			llm_provider = getattr(settings, "local_llm_provider", None)
			llm_url = getattr(settings, "local_llm_api_url", None)

			# Check OpenAI
			has_openai = bool(settings.get_password("openai_api_key"))

			details = []
			if ai_enabled:
				details.append("AI enabled")
			if llm_provider:
				details.append(f"LLM: {llm_provider}")
			if has_openai:
				details.append("OpenAI configured")

			return self.record_test(
				"Settings Configuration",
				ai_enabled or has_openai,
				", ".join(details) if details else "No AI configured",
			)

		except Exception as e:
			return self.record_test("Settings Configuration", False, str(e))

	def _test_message_pipeline(self) -> bool:
		"""Test message processing pipeline"""
		try:
			# Import main processing function
			from raven.ai.ai import process_message_with_agent

			# Check if we can import without errors
			self.record_test("Message Pipeline Import", True)

			# Test that the function exists and has correct signature
			import inspect

			sig = inspect.signature(process_message_with_agent)
			params = list(sig.parameters.keys())

			# Check for expected parameters (may vary by implementation)
			has_message = "message" in params
			has_bot = "bot" in params or "agent_name" in params
			has_channel = "channel_id" in params or "channel" in params

			success = has_message and (has_bot or has_channel)

			return self.record_test("Pipeline Signature", success, f"Parameters: {', '.join(params[:3])}")

		except Exception as e:
			return self.record_test("Message Pipeline", False, str(e))

	def _test_error_handling(self) -> bool:
		"""Test error handling in the system"""
		try:
			from raven.ai.function_executor import execute_raven_function

			# Try to execute non-existent function
			try:
				result = execute_raven_function("non_existent_function_xyz_123456", {})
				# Some implementations might return None or error dict
				if result is None or (isinstance(result, dict) and "error" in result):
					return self.record_test("Error Handling", True, "Handled non-existent function gracefully")
				else:
					return self.record_test("Error Handling", False, "Non-existent function didn't raise error")
			except Exception as e:
				# Good - it raised an error
				error_msg = str(e)
				has_good_error = (
					"not found" in error_msg.lower()
					or "does not exist" in error_msg.lower()
					or "no function" in error_msg.lower()
				)

				return self.record_test(
					"Error Handling",
					has_good_error,
					"Proper error for non-existent function" if has_good_error else f"Error: {error_msg[:50]}",
				)

		except ImportError:
			return self.record_test("Error Handling", False, "Could not import executor")
