import re

#//// Neoffice - frappe import, for the Raven Settings read below (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
import frappe

#//// Neoffice - frappe._ imported for the fallback sentences below (2026-09-04).
from frappe import _

"""
Response formatter for AI messages to handle special formatting like <think> tags and LaTeX
"""


#//// Neoffice - the annotation is dropped because LM Studio hands back a PredictionResult, not a
#//// string (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
def format_ai_response(response_text) -> str:
	"""
	Format AI response to handle special tags and formatting

	Args:
	    #//// Neoffice - docstring follows the signature above (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
	    response_text: Raw response from the AI (str or PredictionResult)

	Returns:
	    Formatted HTML response
	"""

	#//// Neoffice - unwrap the LM Studio PredictionResult and strip the channel markers some local
	#//// models leak into their answer (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
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

	#//// Neoffice - the model's reasoning is hidden unless Raven Settings.enable_ai_debug_mode is on
	#//// (7cdc45189, 2025-08-22 "Feat add SDK LM Studio"). Upstream always renders the <think> block; local models think out
	#//// loud at length and the user saw pages of it before the answer.
	# Check debug mode setting
	show_thinking = frappe.db.get_value("Raven Settings", None, "enable_ai_debug_mode") or False

	if think_matches and show_thinking:
		# Debug mode ON - show thinking in collapsible section
		#//// Neoffice - replaced by the debug-gated block above (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
		thinking_content = "\n\n".join(think_matches).strip()

		#//// Neoffice - replaced by the debug-gated block above (7cdc45189, 2025-08-22 "Feat add SDK LM Studio").
		details_section = (
			f'<details data-summary="Nora\'s Thinking Process">\n' f"{thinking_content}\n" f"</details>"
		)

		#//// Neoffice - the answer is converted to HTML here rather than by the caller, so a <details>
		#//// block and its markdown body can coexist (7cdc45189, 2025-08-22 "Feat add SDK LM Studio" and 092d027d8, 2025-08-07).
		#//// The three fallback sentences below were hardcoded French; they go through frappe._()
		#//// since 2026-09-04 (source files are English, user-facing text comes from the
		#//// catalogue). raven/locale/ holds only main.pot today, so the French wording has to be
		#//// re-added by the translation pass - see the commit message.
		if main_response:
			main_response_html = frappe.utils.md_to_html(main_response)
			return f"{details_section}{main_response_html}"
		else:
			# Only thinking, add default message
			#//// Neoffice - translated through _() (2026-09-04), was hardcoded French.
			default_msg = _("How can I help you?")
			default_html = frappe.utils.md_to_html(default_msg)
			return f"{details_section}{default_html}"
	elif think_matches and not show_thinking:
		# Debug mode OFF - completely hide thinking, only show main response
		if main_response:
			return main_response
		else:
			# No main response found - return a proper greeting
			#//// Neoffice - translated through _() (2026-09-04), was hardcoded French.
			return _("Hello! How can I help you today?")

	# No thinking section found at all
	if main_response:
		return main_response
	else:
		# Empty response - should not happen but handle gracefully
		#//// Neoffice - translated through _() (2026-09-04), was hardcoded French.
		return _("Hello! How can I help you?")


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
