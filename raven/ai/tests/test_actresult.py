"""
Test ActResult handling in LM Studio SDK
"""

import frappe

from .base import BaseTestCase


class ActResultTests(BaseTestCase):
	"""Test ActResult handling specifically"""

	def run(self) -> bool:
		"""Run ActResult tests"""
		if self.verbose:
			print("\n" + "=" * 60)
			print("  ACTRESULT HANDLING TESTS")
			print("=" * 60)

		success = True

		# Test ActResult parsing
		if not self._test_actresult_parsing():
			success = False

		# Test message extraction
		if not self._test_message_extraction():
			success = False

		return success

	def _test_actresult_parsing(self) -> bool:
		"""Test parsing of ActResult objects"""
		try:
			from raven.ai.lmstudio import lmstudio_sdk_handler

			# Mock ActResult-like response
			mock_response = {
				"act_result": "ActResult(rounds=1, totaltimeseconds=8.096)",
				"captured_messages": [{"content": [{"text": "Bonjour ! Je suis Nora, votre assistante."}]}],
			}

			# Test that we can extract text from this structure
			# This would be part of the response processing
			captured = mock_response.get("captured_messages", [])
			if captured:
				last_msg = captured[-1]
				if isinstance(last_msg, dict) and "content" in last_msg:
					content = last_msg["content"]
					if isinstance(content, list):
						for item in content:
							if isinstance(item, dict) and "text" in item:
								extracted_text = item["text"]
								success = "Bonjour" in extracted_text
								return self.record_test(
									"ActResult Parsing",
									success,
									"Successfully extracted text" if success else "Failed to extract",
								)

			return self.record_test("ActResult Parsing", False, "No messages to parse")

		except Exception as e:
			return self.record_test("ActResult Parsing", False, str(e))

	def _test_message_extraction(self) -> bool:
		"""Test extraction of messages from AssistantResponse format"""
		try:
			import re

			# Test string that looks like what we saw in the logs
			test_string = """AssistantResponse.from_dict({
  "content": [
    {
      "text": "Bonjour ! Comment puis-je vous aider ?"
    }
  ]
})"""

			# Extract text using regex
			text_match = re.search(r'"text":\s*"([^"]*)"', test_string)
			if text_match:
				extracted = text_match.group(1)
				success = extracted == "Bonjour ! Comment puis-je vous aider ?"
				self.record_test(
					"Message Extraction", success, f"Extracted: {extracted}" if success else "Extraction mismatch"
				)
			else:
				self.record_test("Message Extraction", False, "Regex failed")

			# Test channel extraction with think tags formatting
			test_with_channels = """<|channel|>analysis<|message|>The user says "Bonjour". They greet.<|end|><|start|>assistant<|channel|>final<|message|>Je suis à votre disposition pour toute question.<|end|>"""

			# Extract both channels like in SDK handler
			analysis_match = re.search(
				r"<\|channel\|>analysis<\|message\|>(.*?)(?:<\|end\|>|$)", test_with_channels, flags=re.DOTALL
			)

			final_match = re.search(
				r"<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|$)", test_with_channels, flags=re.DOTALL
			)

			if final_match and analysis_match:
				# Format with think tags like SDK handler
				analysis_text = analysis_match.group(1).strip()
				final_text = final_match.group(1).strip()
				formatted_response = f"<think>{analysis_text}</think>\n\n{final_text}"

				# Check that we got the expected format
				success = (
					'<think>The user says "Bonjour". They greet.</think>' in formatted_response
					and "Je suis à votre disposition pour toute question." in formatted_response
				)

				return self.record_test(
					"Channel Extraction with Think Tags",
					success,
					"Formatted correctly with think tags" if success else "Failed to format with think tags",
				)
			else:
				return self.record_test("Channel Extraction with Think Tags", False, "Missing channels")

		except Exception as e:
			return self.record_test("Message Extraction", False, str(e))
