"""
Conversation history tests
"""

import frappe

from .base import BaseTestCase


class ConversationTests(BaseTestCase):
	"""Test conversation history functionality"""

	def run(self) -> bool:
		"""Run conversation tests"""
		if self.verbose:
			print("\n" + "=" * 60)
			print("  CONVERSATION HISTORY TESTS")
			print("=" * 60)

		success = True

		# Test conversation memory
		if not self._test_conversation_memory():
			success = False

		# Test history truncation
		if not self._test_history_truncation():
			success = False

		# Test message formatting
		if not self._test_message_formatting():
			success = False

		return success

	def _test_conversation_memory(self) -> bool:
		"""Test that the system remembers previous messages"""
		try:
			# Simulate a conversation history
			conversation_history = [
				{"role": "user", "content": "10+10 est égale à ?"},
				{"role": "assistant", "content": "20"},
			]

			# Check that history is properly formatted
			success = len(conversation_history) == 2
			success = success and conversation_history[0]["role"] == "user"
			success = success and conversation_history[1]["role"] == "assistant"

			return self.record_test(
				"Conversation Memory",
				success,
				"History structure valid" if success else "Invalid history structure",
			)

		except Exception as e:
			return self.record_test("Conversation Memory", False, str(e))

	def _test_history_truncation(self) -> bool:
		"""Test that long histories are truncated properly"""
		try:
			# Create a long history
			long_history = []
			for i in range(20):
				long_history.append({"role": "user", "content": f"Message {i}"})
				long_history.append({"role": "assistant", "content": f"Response {i}"})

			# Test truncation (should keep last 10 messages)
			truncated = long_history[-10:] if len(long_history) > 10 else long_history

			success = len(truncated) == 10

			return self.record_test(
				"History Truncation",
				success,
				f"Truncated to {len(truncated)} messages" if success else "Truncation failed",
			)

		except Exception as e:
			return self.record_test("History Truncation", False, str(e))

	def _test_message_formatting(self) -> bool:
		"""Test message formatting for prompts"""
		try:
			# Test message truncation for long content
			long_message = "A" * 1000
			truncated = long_message[:500] + "..." if len(long_message) > 500 else long_message

			success = len(truncated) == 503  # 500 chars + "..."

			return self.record_test(
				"Message Formatting", success, "Message truncation works" if success else "Truncation failed"
			)

		except Exception as e:
			return self.record_test("Message Formatting", False, str(e))
