"""
Enhanced function call parser for LM Studio responses
Handles multiple formats and variations
"""

import json
import re
from typing import Any, Dict, Optional, Tuple

import frappe


class FunctionCallParser:
	"""
	Robust parser for function calls in LLM responses.
	Handles various formats including corrupted ones.
	"""

	# All possible patterns for function calls
	PATTERNS = [
		# Standard formats
		r"FUNCTION_CALL:\s*(\w+)\((.*?)\)",
		r"FUNCTION CALL:\s*(\w+)\((.*?)\)",
		# Variations without underscores
		r"FUNCTIONCALL:\s*(\w+)\((.*?)\)",
		r"FUNCTION-CALL:\s*(\w+)\((.*?)\)",
		# With HTML corruption
		r"FUNCTION.*?CALL:\s*(\w+)\((.*?)\)",
		r"<em>FUNCTION</em>.*?<em>CALL</em>:\s*(\w+)\((.*?)\)",
		# Case insensitive versions
		r"(?i)function[_\-\s]*call:\s*(\w+)\((.*?)\)",
		# JSON-like format
		r'"function":\s*"(\w+)".*?"arguments":\s*\{(.*?)\}',
		r'"name":\s*"(\w+)".*?"arguments":\s*\{(.*?)\}',
		# Tool call format
		r"tool_call:\s*(\w+)\((.*?)\)",
		r"TOOL_CALL:\s*(\w+)\((.*?)\)",
		# Action format
		r"ACTION:\s*(\w+)\((.*?)\)",
		r"<action>(\w+)\((.*?)\)</action>",
	]

	# Common function name corrections
	NAME_CORRECTIONS = {
		"getdocument": "get_document",
		"get_document": "get_document",
		"getdoc": "get_document",
		"getdocuments": "get_documents",
		"get_documents": "get_documents",
		"getdocs": "get_documents",
		"getlist": "get_list",
		"get_list": "get_list",
		"list": "get_list",
		# Add more mappings as needed
	}

	@classmethod
	def parse(cls, text: str, available_functions: list = None) -> tuple[str, dict[str, Any]] | None:
		"""
		Parse function call from text.

		Args:
		    text: The text to parse
		    available_functions: List of available function names for validation

		Returns:
		    Tuple of (function_name, arguments) or None if no function call found
		"""

		# Clean HTML tags if present
		clean_text = re.sub(r"<[^>]+>", "", text)

		# Try each pattern
		for pattern in cls.PATTERNS:
			matches = re.findall(pattern, clean_text, re.IGNORECASE | re.DOTALL)

			if matches:
				for match in matches:
					func_name = match[0].lower()
					args_str = match[1] if len(match) > 1 else ""

					# Normalize function name
					func_name = cls._normalize_function_name(func_name, available_functions)

					if func_name:
						# Parse arguments
						args = cls._parse_arguments(args_str)

						frappe.log_error(f"Function parsed: {func_name}", f"Pattern: {pattern}\nArgs: {args}")

						return func_name, args

		# Try to detect if user intended a function call
		if cls._looks_like_function_call(text):
			frappe.log_error("Possible function call not parsed", f"Text: {text[:500]}")

		return None

	@classmethod
	def _normalize_function_name(cls, name: str, available_functions: list = None) -> str | None:
		"""
		Normalize and validate function name.
		"""
		# Remove spaces and convert to lowercase
		normalized = name.lower().replace(" ", "").replace("-", "")

		# Check corrections dictionary
		if normalized in cls.NAME_CORRECTIONS:
			corrected = cls.NAME_CORRECTIONS[normalized]

			# Validate against available functions if provided
			if available_functions:
				if corrected in available_functions:
					return corrected
				# Try fuzzy matching
				for func in available_functions:
					if func.lower() == corrected.lower():
						return func
			else:
				return corrected

		# Direct match with available functions
		if available_functions:
			for func in available_functions:
				if func.lower() == normalized or func.lower().replace("_", "") == normalized:
					return func

		# If no available functions list, return as-is if it looks valid
		if re.match(r"^[a-z_][a-z0-9_]*$", name, re.IGNORECASE):
			return name

		return None

	@classmethod
	def _parse_arguments(cls, args_str: str) -> dict[str, Any]:
		"""
		Parse function arguments from string.
		Handles multiple formats.
		"""
		args = {}

		if not args_str or args_str.strip() in ["", "()"]:
			return args

		# Clean up the string
		args_str = args_str.strip()

		# Try JSON format first
		try:
			if args_str.startswith("{"):
				args = json.loads(args_str)
				return args
		except Exception:
			pass

		# Try key=value format
		# Handle both quoted and unquoted values
		patterns = [
			r'(\w+)\s*=\s*"([^"]*)"',  # key="value"
			r"(\w+)\s*=\s*\'([^\']*)\'",  # key='value'
			r"(\w+)\s*=\s*([^,\)]+)",  # key=value
		]

		for pattern in patterns:
			matches = re.findall(pattern, args_str)
			for match in matches:
				key = match[0]
				value = match[1] if len(match) > 1 else ""

				# Try to parse value type
				value = cls._parse_value(value)
				args[key] = value

		# If no key=value pairs found, treat as positional
		if not args and args_str:
			# Remove quotes and split by comma
			values = re.split(r",\s*", args_str)
			if values:
				# Map to common parameter names
				param_names = ["query", "doctype", "name", "id", "text"]
				for i, value in enumerate(values):
					if i < len(param_names):
						args[param_names[i]] = cls._parse_value(value.strip())

		return args

	@classmethod
	def _parse_value(cls, value: str) -> Any:
		"""
		Parse a string value to appropriate type.
		"""
		if not value:
			return ""

		# Remove quotes if present
		value = value.strip().strip('"').strip("'")

		# Try to parse as JSON
		try:
			return json.loads(value)
		except Exception:
			pass

		# Check for boolean
		if value.lower() == "true":
			return True
		elif value.lower() == "false":
			return False

		# Check for None
		if value.lower() in ["none", "null"]:
			return None

		# Try to parse as number
		try:
			if "." in value:
				return float(value)
			else:
				return int(value)
		except Exception:
			pass

		# Return as string
		return value

	@classmethod
	def _looks_like_function_call(cls, text: str) -> bool:
		"""
		Check if text looks like an attempted function call.
		"""
		indicators = [
			"function",
			"call",
			"execute",
			"run",
			"get_",
			"create_",
			"update_",
			"delete_",
			"()",
			"action",
			"tool",
		]

		text_lower = text.lower()
		return any(indicator in text_lower for indicator in indicators)

	@classmethod
	def extract_all_calls(cls, text: str, available_functions: list = None) -> list:
		"""
		Extract all function calls from text.

		Returns:
		    List of tuples (function_name, arguments)
		"""
		calls = []
		remaining_text = text

		while True:
			result = cls.parse(remaining_text, available_functions)
			if not result:
				break

			calls.append(result)

			# Find where this call ends in the text to continue parsing
			func_name, args = result
			# Simple approach - remove the first occurrence
			pattern = f"{func_name}\\("
			idx = remaining_text.lower().find(pattern.lower())
			if idx != -1:
				# Find the closing parenthesis
				paren_count = 1
				end_idx = idx + len(pattern)
				while end_idx < len(remaining_text) and paren_count > 0:
					if remaining_text[end_idx] == "(":
						paren_count += 1
					elif remaining_text[end_idx] == ")":
						paren_count -= 1
					end_idx += 1

				remaining_text = remaining_text[end_idx:]
			else:
				break

		return calls
