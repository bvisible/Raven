import frappe
from frappe import _, client
from frappe.utils import now_datetime, nowdate


def get_document(doctype: str, document_id: str):
	"""
	Get a document from the database
	"""
	# Use the frappe.client.get method to get the document with permissions (both read and field level read)
	return client.get(doctype, name=document_id)


def get_documents(doctype: str, document_ids: list):
	"""
	Get documents from the database
	"""
	docs = []
	for document_id in document_ids:
		# Use the frappe.client.get method to get the document with permissions applied
		docs.append(client.get(doctype, name=document_id))
	return docs


def create_document(doctype: str, data: dict, function=None):
	"""
	Create a document in the database
	"""
	if function:
		# Get any default values
		for param in function.parameters:
			if param.default_value:
				# Check if this value was not to be asked by the AI
				if param.do_not_ask_ai:
					data[param.fieldname] = param.default_value

				# Check if the value was not provided
				if not data.get(param.fieldname):
					data[param.fieldname] = param.default_value

	doc = frappe.get_doc({"doctype": doctype, **data})
	doc.insert()
	return {"document_id": doc.name, "message": "Document created", "doctype": doctype}


def create_documents(doctype: str, data: list, function=None):
	"""
	Create documents in the database
	"""
	docs = []
	for item in data:
		docs.append(create_document(doctype, item, function).get("document_id"))

	return {"documents": docs, "message": "Documents created", "doctype": doctype}


def update_document(doctype: str, document_id: str, data: dict, function=None):
	"""
	Update a document in the database
	"""
	if function:
		# Get any default values
		for param in function.parameters:
			if param.default_value:
				# Check if this value was not to be asked by the AI
				if param.do_not_ask_ai:
					data[param.fieldname] = param.default_value

				# Check if the value was not provided
				if not data.get(param.fieldname):
					data[param.fieldname] = param.default_value

	doc = frappe.get_doc(doctype, document_id)
	doc.update(data)
	doc.save()
	return {"document_id": doc.name, "message": "Document updated", "doctype": doctype}


def update_documents(doctype: str, data: dict, function=None):
	"""
	Update documents in the database
	"""
	updated_docs = []
	for document in data:
		document_without_id = document.copy()
		document_id = document_without_id.pop("document_id")
		updated_docs.append(
			update_document(doctype, document_id, document_without_id, function).get("document_id")
		)

	return {"document_ids": updated_docs, "message": "Documents updated", "doctype": doctype}


def delete_document(doctype: str, document_id: str):
	"""
	Delete a document from the database
	"""
	frappe.delete_doc(doctype, document_id)
	return {"document_id": document_id, "message": "Document deleted", "doctype": doctype}


def delete_documents(doctype: str, document_ids: list):
	"""
	Delete documents from the database
	"""
	for document_id in document_ids:
		frappe.delete_doc(doctype, document_id)
	return {"document_ids": document_ids, "message": "Documents deleted", "doctype": doctype}


def submit_document(doctype: str, document_id: str):
	"""
	Submit a document in the database
	"""
	doc = frappe.get_doc(doctype, document_id)
	doc.submit()
	return {
		"document_id": document_id,
		"message": f"{doctype} {document_id} submitted",
		"doctype": doctype,
	}


def cancel_document(doctype: str, document_id: str):
	"""
	Cancel a document in the database
	"""
	doc = frappe.get_doc(doctype, document_id)
	doc.cancel()
	return {
		"document_id": document_id,
		"message": f"{doctype} {document_id} cancelled",
		"doctype": doctype,
	}


def get_amended_document_id(doctype: str, document_id: str):
	"""
	Get the amended document for a given document
	"""
	amended_doc = frappe.db.exists(doctype, {"amended_from": document_id})
	if amended_doc:
		return amended_doc
	else:
		return {"message": f"{doctype} {document_id} is not amended"}


def get_amended_document(doctype: str, document_id: str):
	"""
	Get the amended document for a given document
	"""
	amended_doc = frappe.db.exists(doctype, {"amended_from": document_id})
	if amended_doc:
		return client.get(doctype, name=document_id)
	else:
		return {"message": f"{doctype} {document_id} is not amended", "doctype": doctype}


def attach_file_to_document(doctype: str, document_id: str, file_path: str):
	"""
	Attach a file to a document in the database
	"""
	if not frappe.db.exists(doctype, document_id):
		return {
			"document_id": document_id,
			"message": f"{doctype} with ID {document_id} not found",
			"doctype": doctype,
		}

	file = frappe.get_doc("File", {"file_url": file_path})

	if not file:
		frappe.throw(_("File not found"))

	newFile = frappe.get_doc(
		{
			"doctype": "File",
			"file_url": file_path,
			"attached_to_doctype": doctype,
			"attached_to_name": document_id,
			"folder": file.folder,
			"file_name": file.file_name,
			"is_private": file.is_private,
		}
	)
	newFile.insert()

	return {"document_id": document_id, "message": "File attached", "file_id": newFile.name}


def get_list(doctype: str, filters: dict = None, fields: list = None, limit: int = 20):
	"""
	Get a list of documents from the database
	"""
	if filters is None:
		filters = {}

	if fields is None:
		filtered_fields = ["*"]
	else:
		meta = frappe.get_meta(doctype)
		filtered_fields = ["name as document_id"]
		if "title" in fields:
			filtered_fields.append(meta.get_title_field())

		for field in fields:
			if meta.has_field(field) and field not in filtered_fields:
				filtered_fields.append(field)

	# Use the frappe.get_list method to get the list of documents
	return frappe.get_list(doctype, filters=filters, fields=filtered_fields, limit=limit)


def get_value(doctype: str, filters: dict = None, fieldname: str | list = "name"):
	"""
	Returns a value from a document

	                :param doctype: DocType to be queried
	                :param fieldname: Field to be returned (default `name`) - can be a list of fields(str) or a single field(str)
	                :param filters: dict or string for identifying the record
	"""
	meta = frappe.get_meta(doctype)

	if isinstance(fieldname, list):
		for field in fieldname:
			if not meta.has_field(field):
				return {"message": f"Field {field} does not exist in {doctype}"}

		return client.get_value(doctype, filters=filters, fieldname=fieldname)
	else:
		if not meta.has_field(fieldname):
			return {"message": f"Field {fieldname} does not exist in {doctype}"}

		return client.get_value(doctype, filters=filters, fieldname=fieldname)


def set_value(doctype: str, document_id: str, fieldname: str | dict, value: str = None):
	"""
	Set a value in a document

	                :param doctype: DocType to be queried
	                :param document_id: Document ID to be updated
	                :param fieldname: Field to be updated - fieldname string or JSON / dict with key value pair
	                :param value: value if fieldname is JSON

	                Example:
	                                client.set_value("Customer", "CUST-00001", {"customer_name": "John Doe", "customer_email": "john.doe@example.com"}) OR
	                                client.set_value("Customer", "CUST-00001", "customer_name", "John Doe")
	"""
	if isinstance(fieldname, dict):
		return client.set_value(doctype, document_id, fieldname)
	else:
		return client.set_value(doctype, document_id, fieldname, value)


def get_report_result(
	report_name: str,
	filters: dict = None,
	limit=None,
	user: str = None,
	ignore_prepared_report: bool = False,
	are_default_filters: bool = True,
):
	"""
	Run a report and return the columns and result
	"""
	# fetch the particular report
	report = frappe.get_doc("Report", report_name)
	if not report:
		return {
			"message": f"Report {report_name} is not present in the system. Please create the report first."
		}

	# run the report by using the get_data method and return the columns and result
	columns, data = report.get_data(
		filters=filters,
		limit=limit,
		user=user,
		ignore_prepared_report=ignore_prepared_report,
		are_default_filters=are_default_filters,
	)

	return {"columns": columns, "data": data}


# ========== AI PENDING ACTION FUNCTIONS ==========


@frappe.whitelist()
def create_pending_action(
	action_type, action_data, preview_message=None, confirmation_message=None, priority="Medium"
):
	"""
	Create a new pending action that requires user confirmation.
	Used by AI bots to create actions that need user approval.

	Args:
	        action_type: Type of action (e.g., "document_send", "email", "task")
	        action_data: Dictionary containing action-specific data
	        preview_message: Optional message to show in preview
	        confirmation_message: Optional message to show when confirming
	        priority: Priority level (Low, Medium, High, Critical)

	Returns:
	        dict: Created action details with ID
	"""
	try:
		import json

		# Ensure action_data is JSON string
		if isinstance(action_data, dict):
			action_data = json.dumps(action_data)

		# Create the pending action
		action = frappe.get_doc(
			{
				"doctype": "Raven AI Pending Action",
				"action_type": action_type,
				"status": "pending",
				"action_data": action_data,
				"preview_message": preview_message,
				"confirmation_message": confirmation_message,
				"priority": priority,
				"channel_id": frappe.flags.get("raven_channel_id"),
				"message_id": frappe.flags.get("raven_message_id"),
				"bot": frappe.flags.get("raven_bot"),
			}
		)
		action.insert()

		return {
			"status": "success",
			"action_id": action.name,
			"message": f"Pending action created: {action_type}",
			"requires_confirmation": True,
		}

	except Exception as e:
		frappe.log_error("AI Pending Action", str(e))
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_pending_actions(status=None, limit=10):
	"""
	Get list of pending actions for current user.
	Used by AI to check what actions are waiting.

	Args:
	        status: Filter by status (pending, confirmed, done, failed, cancelled)
	        limit: Maximum number of actions to return

	Returns:
	        dict: List of pending actions
	"""
	try:
		filters = {"owner": frappe.session.user}
		if status:
			filters["status"] = status

		actions = frappe.get_list(
			"Raven AI Pending Action",
			filters=filters,
			fields=["name", "action_type", "status", "priority", "creation", "preview_message"],
			order_by="creation desc",
			limit_page_length=limit,
		)

		return {"status": "success", "actions": actions, "count": len(actions)}

	except Exception as e:
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_pending_action_details(action_id):
	"""
	Get detailed information about a specific pending action.
	Used by AI to understand what an action will do.

	Args:
	        action_id: The action ID to get details for

	Returns:
	        dict: Full action details
	"""
	try:
		action = frappe.get_doc("Raven AI Pending Action", action_id)

		# Check permission
		if action.owner != frappe.session.user and not frappe.has_permission(
			"Raven AI Pending Action", "read"
		):
			frappe.throw("You don't have permission to view this action")

		return {"status": "success", "action": action.as_dict()}

	except Exception as e:
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def execute_pending_action(action_id):
	"""
	Execute a pending action.
	Used by AI after user confirmation.

	Args:
	        action_id: The action ID to execute

	Returns:
	        dict: Execution result
	"""
	try:
		action = frappe.get_doc("Raven AI Pending Action", action_id)

		# Check permission
		if action.owner != frappe.session.user:
			frappe.throw("You can only execute your own actions")

		# Execute the action
		result = action.execute()

		return result

	except Exception as e:
		# Log error with proper parameter order: title (140 char limit), then full error
		frappe.log_error(f"AI Action Execution - {action_id}"[:140], str(e))
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def cancel_pending_action(action_id):
	"""
	Cancel a pending action.
	Used by AI when user declines.

	Args:
	        action_id: The action ID to cancel

	Returns:
	        dict: Cancellation result
	"""
	try:
		action = frappe.get_doc("Raven AI Pending Action", action_id)

		# Check permission
		if action.owner != frappe.session.user:
			frappe.throw("You can only cancel your own actions")

		# Cancel the action
		action.status = "cancelled"
		action.save()

		return {"status": "success", "message": "Action cancelled"}

	except Exception as e:
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def confirm_pending_action(confirmation_type=None, action_id=None):
	"""
	Universal confirmation handler for any pending action.
	Now uses the Virtual DocType instead of cache.

	Args:
	        confirmation_type: "confirm" to execute, "cancel" to cancel, None to check status
	        action_id: Optional specific action ID, uses last pending if not provided

	Returns:
	        dict: Result of the action execution or current pending action info
	"""
	try:
		# Handle placeholder from AI models
		if action_id == "<ACTION_ID_FROM_PREVIEW>" or action_id == "":
			action_id = None

		# Get the pending action
		if not action_id:
			# Get last pending action for current user using the function that works with Virtual DocType
			result = get_pending_actions(status="pending", limit=1)
			if result.get("status") != "success" or not result.get("actions"):
				return {
					"status": "no_action",
					"message": "No pending action found. Please create an action first.",
				}
			action_id = result["actions"][0]["name"]

		# Get the pending action from Virtual DocType
		try:
			action = frappe.get_doc("Raven AI Pending Action", action_id)
		except frappe.DoesNotExistError:
			return {"status": "not_found", "message": f"No pending action found with ID {action_id}"}

		# If no confirmation type, just return the pending action info
		if not confirmation_type:
			return {
				"status": "pending",
				"action": action.as_dict(),
				"message": "Action is waiting for confirmation",
			}

		# Handle confirmation or cancellation
		if confirmation_type == "confirm":
			# Use the new execute_pending_action function
			result = execute_pending_action(action_id)
			return result

		elif confirmation_type == "cancel":
			# Use the new cancel_pending_action function
			result = cancel_pending_action(action_id)
			return result
		else:
			return {
				"status": "error",
				"message": f"Invalid confirmation_type: {confirmation_type}. Use 'confirm' or 'cancel'",
			}

	except Exception as e:
		frappe.log_error("Confirmation Error", str(e))
		return {"status": "error", "message": str(e)}
