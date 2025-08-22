"""Function executor for Raven AI functions"""

import inspect
import json

import frappe


def execute_raven_function(function_name: str, args: dict, channel_id: str = None):
	"""
	Execute a Raven function by name.

	Args:
	    function_name: Name of the function to execute
	    args: Arguments to pass to the function
	    channel_id: Optional channel ID for context (used by notification functions)
	"""
	try:
		# Get the function document
		function_doc = frappe.get_doc("Raven AI Function", function_name)

		if function_doc.type == "Custom Function":
			# Execute custom function
			function_path = function_doc.function_path
			if function_path:
				func = frappe.get_attr(function_path)
				if func:
					# Convert camelCase parameters to snake_case if needed
					converted_args = {}
					for key, value in args.items():
						# Convert camelCase to snake_case
						snake_key = "".join(["_" + c.lower() if c.isupper() else c for c in key]).lstrip("_")
						converted_args[snake_key] = value

					# Add channel_id to args if function accepts it and it's not already there
					if channel_id and "channel_id" not in converted_args:
						# Check if function accepts channel_id parameter
						sig = inspect.signature(func)
						if "channel_id" in sig.parameters:
							converted_args["channel_id"] = channel_id

					result = func(**converted_args)

					# Ensure result is JSON serializable
					if isinstance(result, dict):
						try:
							# Test serialization
							json.dumps(result, default=str)
						except (TypeError, ValueError):
							# Convert non-serializable values
							result = json.loads(json.dumps(result, default=str))
					return result

		# For other types, use existing handlers
		from raven.ai.functions import (
			create_document,
			delete_document,
			get_document,
			get_list,
			update_document,
		)

		if function_doc.type == "Get Document":
			return get_document(function_doc.reference_doctype, **args)
		elif function_doc.type == "Create Document":
			return create_document(function_doc.reference_doctype, data=args, function=function_doc)
		elif function_doc.type == "Update Document":
			return update_document(function_doc.reference_doctype, **args, function=function_doc)
		elif function_doc.type == "Delete Document":
			return delete_document(function_doc.reference_doctype, **args)
		elif function_doc.type == "Get List":
			return get_list(function_doc.reference_doctype, **args)

	except Exception as e:
		frappe.log_error(f"Function execution error: {str(e)}", f"Execute {function_name}")
		return {"error": str(e)}

	return {"error": "Function type not supported"}
