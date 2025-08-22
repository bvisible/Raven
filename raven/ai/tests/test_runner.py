#!/usr/bin/env python3
"""
Main test runner for Raven AI system
Executes all test categories and provides comprehensive reporting
"""

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import frappe

from .test_actresult import ActResultTests
from .test_conversation import ConversationTests
from .test_functions import FunctionTests
from .test_integration import IntegrationTests
from .test_lmstudio import LMStudioTests
from .test_modules import ModuleTests
from .test_openai import OpenAITests


class RavenAITestRunner:
	"""Main test runner that executes all test suites"""

	def __init__(self, site_name: str = None, verbose: bool = True):
		self.site_name = site_name
		self.verbose = verbose
		self.start_time = None
		self.end_time = None
		self.category_results = {}

	def setup_environment(self):
		"""Initialize Frappe environment"""
		if self.site_name:
			frappe.init(site=self.site_name)
			frappe.connect()
			frappe.set_user("Administrator")

		print("\n" + "=" * 80)
		print("RAVEN AI TEST SUITE - COMPLETE")
		print("=" * 80)
		print(f"Site: {self.site_name or frappe.local.site}")
		print(f"User: {frappe.session.user}")
		print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
		print("=" * 80)

		# Pre-cleanup
		self._pre_cleanup()

	def teardown_environment(self):
		"""Cleanup Frappe environment"""
		# Final cleanup of any test data
		self._post_cleanup()

		if frappe.db:
			frappe.db.commit()
		frappe.destroy()

	def _post_cleanup(self):
		"""Clean up any test data created during tests"""
		if self.verbose:
			print("\n🧹 Post-test cleanup...")

		# Same cleanup as pre-cleanup to ensure everything is removed
		test_patterns = ["Test_%", "TestBot_%", "TestFunc_%", "Test LM%", "Test OpenAI%"]

		cleaned = 0
		for pattern in test_patterns:
			bots = frappe.get_all("Raven Bot", filters={"name": ["like", pattern]})
			for bot in bots:
				try:
					frappe.delete_doc("Raven Bot", bot.name, ignore_permissions=True, force=True)
					cleaned += 1
					if self.verbose:
						print(f"  ✓ Removed: {bot.name}")
				except Exception:
					pass

		# Also clean by bot_name field
		test_bot_names = ["TestBot_LMStudio", "TestBot_OpenAI", "TestBot_Function"]
		for bot_name in test_bot_names:
			bots = frappe.get_all("Raven Bot", filters={"bot_name": bot_name})
			for bot in bots:
				try:
					frappe.delete_doc("Raven Bot", bot.name, ignore_permissions=True, force=True)
					cleaned += 1
					if self.verbose:
						print(f"  ✓ Removed: {bot.name}")
				except Exception:
					pass

		if cleaned > 0:
			frappe.db.commit()
			if self.verbose:
				print(f"  Total cleaned: {cleaned} test bots")

	def _pre_cleanup(self):
		"""Clean any leftover test data"""
		if self.verbose:
			print("\n🧹 Pre-test cleanup...")

		# Clean by name patterns
		test_patterns = ["Test_%", "TestBot_%", "TestFunc_%", "Test LM%", "Test OpenAI%"]

		for pattern in test_patterns:
			bots = frappe.get_all("Raven Bot", filters={"name": ["like", pattern]})
			for bot in bots:
				try:
					frappe.delete_doc("Raven Bot", bot.name, ignore_permissions=True, force=True)
					if self.verbose:
						print(f"  Cleaned: {bot.name}")
				except Exception:
					pass

		# Also clean by bot_name field
		test_bot_names = ["TestBot_LMStudio", "TestBot_OpenAI", "TestBot_Function"]
		for bot_name in test_bot_names:
			bots = frappe.get_all("Raven Bot", filters={"bot_name": bot_name})
			for bot in bots:
				try:
					frappe.delete_doc("Raven Bot", bot.name, ignore_permissions=True, force=True)
					if self.verbose:
						print(f"  Cleaned: {bot.name} (was {bot_name})")
				except Exception:
					pass

		frappe.db.commit()

	def run_all(self) -> bool:
		"""Run all test categories"""
		self.start_time = datetime.now()

		# Define test categories in order
		test_categories = [
			("Modules", ModuleTests),
			("LM Studio", LMStudioTests),
			("OpenAI", OpenAITests),
			("Functions", FunctionTests),
			("Integration", IntegrationTests),
			("ActResult", ActResultTests),
			("Conversation", ConversationTests),
		]

		all_success = True

		for category_name, test_class in test_categories:
			success = self._run_category(category_name, test_class)
			if not success:
				all_success = False

		self.end_time = datetime.now()

		# Generate final report
		self._generate_final_report()

		return all_success

	def _run_category(self, name: str, test_class) -> bool:
		"""Run a single test category"""
		try:
			# Create test instance
			test = test_class(verbose=self.verbose)

			# Setup
			test.setup()

			# Run tests
			success = test.run()

			# Get results
			results = test.get_results()
			self.category_results[name] = results

			# Teardown
			test.teardown()

			# Print summary if verbose
			if self.verbose:
				test.print_summary()

			return success

		except Exception as e:
			print(f"\n❌ Error in {name} tests: {str(e)}")
			self.category_results[name] = {
				"total": 0,
				"passed": 0,
				"failed": 1,
				"success_rate": 0,
				"error": str(e),
			}
			return False

	def _generate_final_report(self):
		"""Generate comprehensive final report"""
		print("\n" + "=" * 80)
		print("FINAL TEST REPORT")
		print("=" * 80)

		# Aggregate results
		total_tests = 0
		total_passed = 0
		total_failed = 0

		print("\n📊 Results by Category:")
		print("-" * 40)

		for category, results in self.category_results.items():
			if "error" in results:
				print(f"{category:15} | ❌ ERROR: {results['error'][:30]}")
			else:
				total_tests += results["total"]
				total_passed += results["passed"]
				total_failed += results["failed"]

				status = (
					"✅" if results["success_rate"] >= 90 else "⚠️" if results["success_rate"] >= 70 else "❌"
				)
				print(
					f"{category:15} | {status} {results['passed']}/{results['total']} ({results['success_rate']:.0f}%)"
				)

		print("-" * 40)

		# Overall summary
		print("\n📈 Overall Results:")
		print(f"  Total Tests:  {total_tests}")
		print(f"  Passed:       {total_passed} ✅")
		print(f"  Failed:       {total_failed} ❌")

		if total_tests > 0:
			overall_rate = (total_passed / total_tests) * 100
			print(f"  Success Rate: {overall_rate:.1f}%")

			# Status message
			if overall_rate == 100:
				print("\n🎉 PERFECT! All tests passed!")
			elif overall_rate >= 90:
				print("\n✨ EXCELLENT! System is working well!")
			elif overall_rate >= 70:
				print("\n👍 GOOD! Most features are working!")
			else:
				print("\n⚠️ Some issues need attention.")

		# Failed tests detail
		if total_failed > 0:
			print("\n❌ Failed Tests Details:")
			for category, results in self.category_results.items():
				if "results" in results:
					failed = [r for r in results["results"] if not r["success"]]
					if failed:
						print(f"\n  {category}:")
						for test in failed:
							print(f"    • {test['name']}")
							if test["details"]:
								print(f"      {test['details'][:60]}")

		# Timing
		if self.start_time and self.end_time:
			duration = (self.end_time - self.start_time).total_seconds()
			print(f"\n⏱️ Test duration: {duration:.1f} seconds")

		print("\n" + "=" * 80)
		print("TEST SUITE COMPLETED")
		print("=" * 80)


def run_all_tests(site_name: str = None, verbose: bool = True) -> bool:
	"""Run all test categories"""
	runner = RavenAITestRunner(site_name, verbose)

	try:
		runner.setup_environment()
		return runner.run_all()
	finally:
		runner.teardown_environment()


def run_test_category(category: str, site_name: str = None, verbose: bool = True) -> bool:
	"""Run a specific test category"""

	# Map category names to test classes
	category_map = {
		"modules": ModuleTests,
		"lmstudio": LMStudioTests,
		"openai": OpenAITests,
		"functions": FunctionTests,
		"integration": IntegrationTests,
		"actresult": ActResultTests,
		"conversation": ConversationTests,
	}

	test_class = category_map.get(category.lower())
	if not test_class:
		print(f"❌ Unknown test category: {category}")
		print(f"Available categories: {', '.join(category_map.keys())}")
		return False

	if site_name:
		frappe.init(site=site_name)
		frappe.connect()
		frappe.set_user("Administrator")

	try:
		print(f"\n🚀 Running {category} tests...")
		test = test_class(verbose=verbose)
		test.setup()
		success = test.run()
		test.print_summary()
		test.teardown()
		return success
	finally:
		if frappe.db:
			frappe.db.commit()
		frappe.destroy()


# Entry points for bench execute
def test_all(site_name=None):
	"""Run all tests via bench execute"""
	return run_all_tests(site_name)


def test_modules(site_name=None):
	"""Test modules only"""
	return run_test_category("modules", site_name)


def test_lmstudio(site_name=None):
	"""Test LM Studio only"""
	return run_test_category("lmstudio", site_name)


def test_openai(site_name=None):
	"""Test OpenAI only"""
	return run_test_category("openai", site_name)


def test_functions(site_name=None):
	"""Test functions only"""
	return run_test_category("functions", site_name)


def test_integration(site_name=None):
	"""Test integration only"""
	return run_test_category("integration", site_name)


def test_actresult(site_name=None):
	"""Test ActResult handling only"""
	return run_test_category("actresult", site_name)


def test_conversation(site_name=None):
	"""Test conversation history only"""
	return run_test_category("conversation", site_name)


if __name__ == "__main__":
	# Command line interface
	if len(sys.argv) < 2:
		print("Usage:")
		print("  Run all tests:")
		print("    bench execute raven.ai.tests.test_runner.test_all")
		print("")
		print("  Run specific category:")
		print("    bench execute raven.ai.tests.test_runner.test_modules")
		print("    bench execute raven.ai.tests.test_runner.test_lmstudio")
		print("    bench execute raven.ai.tests.test_runner.test_openai")
		print("    bench execute raven.ai.tests.test_runner.test_functions")
		print("    bench execute raven.ai.tests.test_runner.test_integration")
		sys.exit(1)

	site_name = sys.argv[1] if len(sys.argv) > 1 else None
	category = sys.argv[2] if len(sys.argv) > 2 else "all"

	if category == "all":
		run_all_tests(site_name)
	else:
		run_test_category(category, site_name)
