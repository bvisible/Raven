"""
Base test class with common functionality
"""

from datetime import datetime
from typing import Any, Dict, List

import frappe


class BaseTestCase:
	"""Base class for all test cases"""

	def __init__(self, verbose: bool = True):
		self.verbose = verbose
		self.test_results = []
		self.created_resources = {}

	def setup(self):
		"""Setup before tests"""
		pass

	def teardown(self):
		"""Cleanup after tests"""
		self.cleanup_resources()

	def cleanup_resources(self):
		"""Clean up created test resources"""
		if not self.created_resources:
			return

		if self.verbose:
			print("\n🧹 Cleaning up test resources...")

		cleanup_count = 0
		for resource_name, resource_type in self.created_resources.items():
			if frappe.db.exists(resource_type, resource_name):
				try:
					frappe.delete_doc(resource_type, resource_name, ignore_permissions=True, force=True)
					cleanup_count += 1
					if self.verbose:
						print(f"  ✓ Deleted {resource_type}: {resource_name}")
				except Exception as e:
					if self.verbose:
						print(f"  ✗ Failed to delete {resource_name}: {str(e)}")

		if cleanup_count > 0:
			frappe.db.commit()
			if self.verbose:
				print(f"  Cleaned {cleanup_count} resources")

		self.created_resources = {}

	def record_test(self, name: str, success: bool, details: str = ""):
		"""Record test result"""
		status = "✅" if success else "❌"
		if self.verbose:
			print(f"{status} {name}")
			if details and (not success or self.verbose):
				print(f"   → {details}")

		self.test_results.append({"name": name, "success": success, "details": details})

		return success

	def get_results(self) -> dict[str, Any]:
		"""Get test results summary"""
		total = len(self.test_results)
		passed = sum(1 for r in self.test_results if r["success"])
		failed = total - passed

		return {
			"total": total,
			"passed": passed,
			"failed": failed,
			"success_rate": (passed / total * 100) if total > 0 else 0,
			"results": self.test_results,
		}

	def print_summary(self):
		"""Print test summary"""
		results = self.get_results()

		print("\n📊 Summary:")
		print(f"  Total:  {results['total']}")
		print(f"  Passed: {results['passed']} ✅")
		print(f"  Failed: {results['failed']} ❌")

		if results["total"] > 0:
			print(f"  Success Rate: {results['success_rate']:.1f}%")

			if results["failed"] > 0:
				print("\n❌ Failed Tests:")
				for result in self.test_results:
					if not result["success"]:
						print(f"  • {result['name']}")
						if result["details"]:
							print(f"    {result['details'][:80]}")

	def run(self) -> bool:
		"""Run all tests in this category"""
		raise NotImplementedError("Subclasses must implement run()")
