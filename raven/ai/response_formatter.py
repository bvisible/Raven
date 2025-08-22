import re

import frappe

"""
Response formatter for AI messages to handle special formatting like <think> tags and LaTeX
"""


def format_ai_response(response_text) -> str:
	"""
	Format AI response to handle special tags and formatting

	Args:
	    response_text: Raw response from the AI (str or PredictionResult)

	Returns:
	    Formatted HTML response
	"""

	# Extract content from PredictionResult if needed
	if hasattr(response_text, "content"):
		response_text = response_text.content
	elif not isinstance(response_text, str):
		response_text = str(response_text)

	# Also check for channel markers that might not be wrapped in think tags
	# Remove them completely if debug is off
	if not (frappe.db.get_value("Raven Settings", None, "enable_ai_debug_mode") or False):
		import re

		# Remove channel markers and everything between them
		response_text = re.sub(
			r"<\|channel\|>analysis<\|message\|>.*?(?:<\|channel\|>final<\|message\|>|$)",
			"",
			response_text,
			flags=re.DOTALL,
		)
		# Clean up remaining markers
		response_text = re.sub(r"<\|channel\|>final<\|message\|>", "", response_text)
		response_text = re.sub(r"<\|end\|>", "", response_text)
		response_text = response_text.strip()

	# Handle unclosed think tags (truncated responses)
	if "<think>" in response_text and "</think>" not in response_text:
		# Close the unclosed think tag
		response_text = response_text + "</think>"

	# Extract thinking sections
	think_pattern = r"<think>(.*?)</think>"
	think_matches = re.findall(think_pattern, response_text, re.DOTALL)

	# Remove think tags from main response
	main_response = re.sub(think_pattern, "", response_text, flags=re.DOTALL).strip()

	# Convert LaTeX boxed notation to bold
	# \boxed{...} -> **...**
	main_response = re.sub(r"\\boxed\{([^}]+)\}", r"**\1**", main_response)

	# Build formatted response
	formatted_parts = []

	# Check debug mode setting
	show_thinking = frappe.db.get_value("Raven Settings", None, "enable_ai_debug_mode") or False

	if think_matches and show_thinking:
		# Debug mode ON - show thinking in collapsible section
		thinking_content = "\n\n".join(think_matches).strip()

		details_section = (
			f'<details data-summary="Nora\'s Thinking Process">\n' f"{thinking_content}\n" f"</details>"
		)

		if main_response:
			main_response_html = frappe.utils.md_to_html(main_response)
			return f"{details_section}{main_response_html}"
		else:
			# Only thinking, add default message
			default_msg = "Comment puis-je vous aider ?"
			default_html = frappe.utils.md_to_html(default_msg)
			return f"{details_section}{default_html}"
	elif think_matches and not show_thinking:
		# Debug mode OFF - completely hide thinking, only show main response
		if main_response:
			return main_response
		else:
			# No main response found - return a proper greeting
			return "Bonjour ! Comment puis-je vous aider aujourd'hui ?"

	# No thinking section found at all
	if main_response:
		return main_response
	else:
		# Empty response - should not happen but handle gracefully
		return "Bonjour ! Comment puis-je vous aider ?"


def extract_thinking(response_text: str) -> tuple[str, str]:
	"""
	Extract thinking and main response separately

	Returns:
	    tuple of (thinking_text, main_response)
	"""
	think_pattern = r"<think>(.*?)</think>"
	think_matches = re.findall(think_pattern, response_text, re.DOTALL)

	# Remove think tags from main response
	main_response = re.sub(think_pattern, "", response_text, flags=re.DOTALL).strip()

	# Convert LaTeX boxed notation
	main_response = re.sub(r"\\boxed\{([^}]+)\}", r"**\1**", main_response)

	thinking_text = "\n\n".join(think_matches).strip() if think_matches else ""

	return thinking_text, main_response
