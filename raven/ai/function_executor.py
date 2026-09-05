# //// Neoffice - added file (no upstream equivalent). Runs a Raven AI Function from a name +
# //// arguments dict (7cdc45189, 2025-08-22 "Feat add SDK LM Studio"), used by the text-based tool-calling path: with no
# //// native function calling there is no SDK to dispatch the call for us.
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

		# //// Neoffice - full dispatch (2026-09-04). Only six of the eighteen Raven AI Function types
		# //// were handled here, and "Update Document" was called as update_document(doctype, **args),
		# //// which cannot match update_document(doctype, document_id, data, function) - it raised
		# //// TypeError on every call. The table below mirrors the dispatch of raven/ai/handler.py,
		# //// the assistants path, so a function behaves the same whichever provider runs it. It
		# //// matters more now that agents_integration.py builds a tool for EVERY configured function
		# //// again. Each entry is a thunk: only the selected one is evaluated.
		from raven.ai import functions as raven_fn

		doctype = function_doc.reference_doctype
		handlers = {
			"Get Document": lambda: raven_fn.get_document(doctype, **args),
			"Get Multiple Documents": lambda: raven_fn.get_documents(doctype, **args),
			"Get List": lambda: raven_fn.get_list(
				doctype,
				filters=args.get("filters"),
				fields=args.get("fields"),
				limit=args.get("limit", 20),
			),
			"Get Value": lambda: raven_fn.get_value(
				doctype=doctype, filters=args.get("filters"), fieldname=args.get("fieldname")
			),
			"Set Value": lambda: raven_fn.set_value(
				doctype=doctype,
				document_id=args.get("document_id"),
				fieldname=args.get("fieldname"),
				value=args.get("value"),
			),
			"Get Amended Document": lambda: raven_fn.get_amended_document(doctype, **args),
			"Create Document": lambda: raven_fn.create_document(
				doctype, data=args, function=function_doc
			),
			"Create Multiple Documents": lambda: raven_fn.create_documents(
				doctype, data=args.get("data"), function=function_doc
			),
			"Update Document": lambda: raven_fn.update_document(
				doctype, document_id=args.get("document_id"), data=args, function=function_doc
			),
			"Update Multiple Documents": lambda: raven_fn.update_documents(
				doctype, data=args.get("data"), function=function_doc
			),
			"Delete Document": lambda: raven_fn.delete_document(doctype, **args),
			"Delete Multiple Documents": lambda: raven_fn.delete_documents(doctype, **args),
			"Submit Document": lambda: raven_fn.submit_document(doctype, **args),
			"Cancel Document": lambda: raven_fn.cancel_document(doctype, **args),
			"Attach File to Document": lambda: raven_fn.attach_file_to_document(
				args.get("doctype"), args.get("document_id"), args.get("file_path")
			),
			"Get Report Result": lambda: raven_fn.get_report_result(
				report_name=args.get("report_name"),
				filters=args.get("filters"),
				user=args.get("user", frappe.session.user),
				ignore_prepared_report=args.get("ignore_prepared_report", False),
				are_default_filters=args.get("are_default_filters", True),
			),
		}

		handler = handlers.get(function_doc.type)
		if handler:
			return handler()

	except Exception as e:
		frappe.log_error(f"Function execution error: {str(e)}", f"Execute {function_name}")
		return {"error": str(e)}

	return {"error": "Function type not supported"}
