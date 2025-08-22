#!/usr/bin/env python3
"""
Test de l'injection de contexte pour Nora avec LM Studio
Tests pour vérifier que le contexte est correctement injecté sans get_current_context
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import frappe


class TestContextInjection(unittest.TestCase):
	"""Test suite for context injection without get_current_context"""

	@classmethod
	def setUpClass(cls):
		"""Setup test environment"""
		# Initialize Frappe if not already done
		if not frappe.db:
			frappe.init(site="prod.local")
			frappe.connect()
			frappe.set_user("Administrator")

	def test_get_variables_for_instructions_completeness(self):
		"""Test that get_variables_for_instructions returns all required variables"""
		from raven.ai.handler import get_variables_for_instructions

		# Get variables
		variables = get_variables_for_instructions()

		# Check all required variables are present
		required_vars = [
			"user",
			"user_id",
			"first_name",
			"full_name",
			"email",
			"company",
			"currency",
			"lang",
			"language",
			"time_zone",
			"current_date",
			"current_time",
		]

		for var in required_vars:
			self.assertIn(var, variables, f"Variable '{var}' is missing")

		# Check types
		self.assertIsInstance(variables["user_id"], str)
		self.assertIsInstance(variables["lang"], str)
		self.assertEqual(variables["lang"], variables["lang"].upper(), "lang should be uppercase")

		# Check currency is set
		if variables.get("company"):
			self.assertIn("currency", variables)
			self.assertIsNotNone(variables["currency"])

	def test_context_variables_completeness(self):
		"""Test that all necessary context variables are available"""
		from raven.ai.handler import get_variables_for_instructions

		# Get instruction variables
		instruction_vars = get_variables_for_instructions()

		# Check that all essential context variables are present
		essential_vars = [
			"user",
			"user_id",
			"full_name",
			"email",
			"company",
			"currency",
			"language",
			"lang",
			"current_date",
			"current_time",
			"time_zone",
		]

		for var in essential_vars:
			self.assertIn(var, instruction_vars, f"Essential variable '{var}' not in instruction vars")

	def test_prompt_rendering_with_variables(self):
		"""Test that prompt is correctly rendered with context variables"""
		import frappe

		from raven.ai.handler import get_variables_for_instructions

		# Sample prompt with variables
		prompt = """You are assisting {{full_name}} from {{company}}.
Current date: {{current_date}}
Language: {{lang}}
Currency: {{currency}}"""

		# Get variables
		variables = get_variables_for_instructions()

		# Render prompt
		rendered = frappe.render_template(prompt, variables)

		# Check that variables are replaced
		self.assertNotIn("{{full_name}}", rendered, "Variable {{full_name}} not replaced")
		self.assertNotIn("{{company}}", rendered, "Variable {{company}} not replaced")
		self.assertNotIn("{{current_date}}", rendered, "Variable {{current_date}} not replaced")
		self.assertNotIn("{{lang}}", rendered, "Variable {{lang}} not replaced")

		# Check that actual values are in the rendered prompt
		if variables.get("full_name"):
			self.assertIn(variables["full_name"], rendered)
		if variables.get("company"):
			self.assertIn(str(variables["company"]), rendered)

	def test_nora_prompt_uses_template_variables(self):
		"""Test that Nora's prompt uses template variables instead of function calls"""
		from neoffice_theme.ai.core.nora_manager import get_nora_prompt

		prompt = get_nora_prompt()

		# Check that prompt uses template variables
		self.assertIn("{{full_name}}", prompt, "Prompt should use {{full_name}} variable")
		self.assertIn("{{company}}", prompt, "Prompt should use {{company}} variable")
		self.assertIn("{{currency}}", prompt, "Prompt should use {{currency}} variable")
		self.assertIn("{{lang}}", prompt, "Prompt should use {{lang}} variable")

	def test_context_injection_in_system_prompt(self):
		"""Test that context is properly injected in the system prompt"""
		from raven.ai.lmstudio.enhanced_handler import EnhancedLMStudioHandler

		# Create mock bot
		mock_bot = Mock()
		mock_bot.name = "Nora"
		mock_bot.instruction = "You are assisting {{full_name}} from {{company}}."
		mock_bot.dynamic_instructions = 1
		mock_bot.bot_functions = []

		# Initialize handler with empty context
		handler = EnhancedLMStudioHandler(bot=mock_bot, context={})

		# Build system prompt
		with patch("raven.ai.handler.get_variables_for_instructions") as mock_get_vars:
			mock_get_vars.return_value = {
				"full_name": "John Doe",
				"company": "Test Company",
				"currency": "USD",
				"lang": "EN",
				"user_id": "john@example.com",
				"current_date": "2024-01-22",
				"current_time": datetime.now(),
			}

			system_prompt = handler._build_system_prompt()

			# Check that variables are replaced
			self.assertNotIn(
				"{{full_name}}", system_prompt, "Template variable {{full_name}} should be replaced"
			)
			self.assertIn("John Doe", system_prompt, "Actual name should be in prompt")
			self.assertIn("Test Company", system_prompt, "Actual company should be in prompt")


def run_tests():
	"""Run all context injection tests"""
	print("=" * 60)
	print("Running Context Injection Tests")
	print("=" * 60)

	# Create test suite
	suite = unittest.TestLoader().loadTestsFromTestCase(TestContextInjection)

	# Run tests
	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)

	# Print summary
	print("\n" + "=" * 60)
	if result.wasSuccessful():
		print("✅ All tests passed!")
	else:
		print(f"❌ {len(result.failures)} test(s) failed")
		print(f"❌ {len(result.errors)} test(s) had errors")
	print("=" * 60)

	return result.wasSuccessful()


if __name__ == "__main__":
	import sys

	success = run_tests()
	sys.exit(0 if success else 1)
