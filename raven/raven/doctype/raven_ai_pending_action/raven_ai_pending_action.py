import json
import uuid
from datetime import datetime, timedelta

import frappe
from frappe.model.document import Document


class RavenAIPendingAction(Document):
	"""Virtual DocType using Redis as backend for pending AI actions"""

	REDIS_PREFIX = "raven_ai_pending_action:"
	DEFAULT_EXPIRY = 259200  # 3 days in seconds

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Ensure this document is never cached by Frappe
		self.flags.ignore_cache = True

	def db_insert(self, *args, **kwargs):
		"""Store in Redis instead of database"""
		d = self.get_valid_dict(convert_dates_to_str=True)

		# Generate unique name if not set
		if not d.get("name"):
			d["name"] = str(uuid.uuid4())[:8]

		# Set timestamps
		now = frappe.utils.now()
		d["creation"] = now
		d["modified"] = now
		d["owner"] = frappe.session.user
		d["modified_by"] = frappe.session.user

		# Set expiry (3 days for done actions, 30 min for pending)
		if d.get("status") == "done":
			expiry = self.DEFAULT_EXPIRY
		else:
			expiry = 1800  # 30 minutes for pending

		d["expires_at"] = (datetime.now() + timedelta(seconds=expiry)).isoformat()

		# Store in Redis
		key = f"{self.REDIS_PREFIX}{d['name']}"
		frappe.cache().set_value(key, d, expires_in_sec=expiry)

		# Add to user's action list
		user_key = f"{self.REDIS_PREFIX}user:{frappe.session.user}"
		user_actions = frappe.cache().get_value(user_key) or []
		if d["name"] not in user_actions:
			user_actions.append(d["name"])
			frappe.cache().set_value(user_key, user_actions, expires_in_sec=self.DEFAULT_EXPIRY)

		# Add to global list for listing
		global_key = f"{self.REDIS_PREFIX}all"
		all_actions = frappe.cache().get_value(global_key) or []
		if d["name"] not in all_actions:
			all_actions.append(d["name"])
			frappe.cache().set_value(global_key, all_actions, expires_in_sec=self.DEFAULT_EXPIRY)

		self.name = d["name"]

	def load_from_db(self):
		"""Load from Redis"""
		key = f"{self.REDIS_PREFIX}{self.name}"
		data = frappe.cache().get_value(key)
		if data:
			# Initialize the parent Document class with the data from Redis
			# This is the pattern from Frappe docs for Virtual DocType
			super(Document, self).__init__(data)
		else:
			frappe.throw(f"Raven AI Pending Action {self.name} not found")

	def db_update(self, *args, **kwargs):
		"""Update in Redis - for Virtual DocType, this is same as insert"""
		# For Virtual DocType, update works exactly like insert
		# We re-save the entire document to Redis
		d = self.get_valid_dict(convert_dates_to_str=True)

		# Ensure name is set
		if not d.get("name"):
			d["name"] = self.name

		# Update timestamps
		d["modified"] = frappe.utils.now()
		d["modified_by"] = frappe.session.user

		# Keep creation if it exists
		if not d.get("creation"):
			d["creation"] = getattr(self, "creation", frappe.utils.now())
		if not d.get("owner"):
			d["owner"] = getattr(self, "owner", frappe.session.user)

		# Adjust expiry based on status
		status = d.get("status", "pending")
		if status == "done":
			expiry = self.DEFAULT_EXPIRY  # 3 days for done
		elif status in ["cancelled", "failed"]:
			expiry = 86400  # 1 day for cancelled/failed
		else:
			expiry = 1800  # 30 min for pending/executing

		d["expires_at"] = (datetime.now() + timedelta(seconds=expiry)).isoformat()

		# IMPORTANT: Delete the key first to ensure cache is invalidated
		# This is a workaround for Frappe cache not updating values properly
		key = f"{self.REDIS_PREFIX}{d['name']}"
		frappe.cache().delete_value(key)

		# Now store the new value in Redis
		frappe.cache().set_value(key, d, expires_in_sec=expiry)

	def delete(self):
		"""Remove from Redis"""
		key = f"{self.REDIS_PREFIX}{self.name}"
		frappe.cache().delete_value(key)

		# Remove from user's list
		user_key = f"{self.REDIS_PREFIX}user:{frappe.session.user}"
		user_actions = frappe.cache().get_value(user_key) or []
		if self.name in user_actions:
			user_actions.remove(self.name)
			frappe.cache().set_value(user_key, user_actions)

		# Remove from global list
		global_key = f"{self.REDIS_PREFIX}all"
		all_actions = frappe.cache().get_value(global_key) or []
		if self.name in all_actions:
			all_actions.remove(self.name)
			frappe.cache().set_value(global_key, all_actions)

	@staticmethod
	def get_list(args):
		"""Get list of all pending actions"""
		filters = args.get("filters", {})

		# Handle filters being passed as empty list from ReportView
		if isinstance(filters, list) and len(filters) == 0:
			filters = {}
		elif isinstance(filters, list):
			# Convert list of filter dicts to a single dict
			filter_dict = {}
			for f in filters:
				if isinstance(f, dict):
					filter_dict.update(f)
			filters = filter_dict

		order_by = args.get("order_by", "creation desc")
		limit = args.get("limit_page_length", 20) or args.get("page_length", 20)
		start = args.get("start", 0)

		# Convert to integers if they're strings
		try:
			limit = int(limit) if limit else 20
		except (ValueError, TypeError):
			limit = 20

		try:
			start = int(start) if start else 0
		except (ValueError, TypeError):
			start = 0

		# Get all action IDs
		global_key = f"{RavenAIPendingAction.REDIS_PREFIX}all"
		all_action_ids = frappe.cache().get_value(global_key) or []

		actions = []
		for action_id in all_action_ids:
			key = f"{RavenAIPendingAction.REDIS_PREFIX}{action_id}"
			data = frappe.cache().get_value(key)
			if data:
				# Apply filters
				match = True
				if filters:
					for field, value in filters.items():
						if data.get(field) != value:
							match = False
							break

				if match:
					actions.append(frappe._dict(data))

		# Sort by creation desc by default
		if "desc" in order_by:
			actions.sort(key=lambda x: x.get("creation", ""), reverse=True)
		else:
			actions.sort(key=lambda x: x.get("creation", ""))

		# Apply pagination (start and limit)
		if start:
			actions = actions[start:]
		if limit:
			actions = actions[:limit]

		return actions

	@staticmethod
	def get_count(args):
		"""Count pending actions"""
		return len(RavenAIPendingAction.get_list(args))

	@staticmethod
	def get_stats(args):
		"""Get statistics"""
		actions = RavenAIPendingAction.get_list({"limit_page_length": 1000})
		stats = {
			"total": len(actions),
			"pending": len([a for a in actions if a.get("status") == "pending"]),
			"done": len([a for a in actions if a.get("status") == "done"]),
			"failed": len([a for a in actions if a.get("status") == "failed"]),
		}
		return stats

	def execute(self):
		"""Execute the pending action"""
		if self.status != "pending":
			return {"status": "error", "message": f"Cannot execute action with status {self.status}"}

		# Update status to executing
		self.status = "executing"
		self.db_update()  # Use db_update for Virtual DocType

		try:
			# Parse action data
			action_data = json.loads(self.action_data) if self.action_data else {}

			# Execute based on action type
			result = self._execute_action_type(action_data)

			# Update status to done
			self.status = "done"
			self.execution_result = json.dumps(result) if isinstance(result, dict) else str(result)
			self.executed_at = frappe.utils.now()
			self.db_update()  # Use db_update for Virtual DocType

			return result

		except Exception as e:
			# Update status to failed
			self.status = "failed"
			self.error_message = str(e)[:500]  # Limit error message length
			self.db_update()  # Use db_update for Virtual DocType
			return {"status": "error", "message": str(e)}

	def _execute_action_type(self, action_data):
		"""Execute action based on type"""

		# Handle specific action types
		if self.action_type == "document_email":
			# Execute document email sending
			try:
				document_type = action_data.get("document_type")
				document_id = action_data.get("document_id")
				recipient_email = action_data.get("recipient_email")
				message = action_data.get("message")

				if not document_type or not document_id or not recipient_email:
					return {"status": "error", "message": "Missing required fields for document email"}

				# Verify document exists
				if not frappe.db.exists(document_type, document_id):
					return {"status": "error", "message": f"Document {document_type} {document_id} not found"}

				# Use the Frappe communication system to send document with PDF
				from frappe.core.doctype.communication.email import make

				# Get the default print format for this doctype
				print_format = frappe.db.get_value("DocType", document_type, "default_print_format")
				if not print_format:
					print_format = "Standard"

				# Generate the PDF content first
				try:
					pdf_file = frappe.attach_print(
						doctype=document_type, name=document_id, print_format=print_format
					)
					attachments = [pdf_file] if pdf_file else []
				except Exception as e:
					frappe.log_error("PDF Generation Error", str(e))
					attachments = []

				# Create and send email with document as PDF attachment
				# This is the standard Frappe way to send documents
				make(
					doctype=document_type,
					name=document_id,
					subject=f"{document_type} {document_id}",
					content=message or f"Please find attached {document_type} {document_id}",
					recipients=recipient_email,
					communication_medium="Email",
					send_email=True,
					print_html=None,
					print_format=print_format,
					attachments=attachments,  # Pass the PDF as attachment
					send_me_a_copy=False,
					print_letterhead=True,
				)

				frappe.log_error(f"Email sent to {recipient_email}", f"Document Email Success - {document_id}")

				return {
					"status": "success",
					"message": f"Email sent successfully to {recipient_email}",
					"document": f"{document_type} {document_id}",
				}

			except Exception as e:
				frappe.log_error("Document Email Error", str(e))
				return {"status": "error", "message": str(e)}

		elif self.action_type == "email":
			# Email with HTML and attachments support
			try:
				# Get email details
				recipient_email = action_data.get("recipient_email")
				subject = action_data.get("subject")
				content = action_data.get("content")
				attachments = action_data.get("attachments", [])
				is_html = action_data.get("is_html", False)

				# Send the email with all features
				frappe.sendmail(
					recipients=[recipient_email],
					subject=subject,
					message=content,
					attachments=attachments,
					now=True,
					as_markdown=not is_html,  # If HTML, don't convert to markdown
				)

				frappe.log_error(
					f"Email sent successfully to {recipient_email}", f"Pending Action Executed - {self.name}"
				)

				return {"status": "success", "message": f"Email sent to {recipient_email}"}
			except Exception as e:
				frappe.log_error(f"Email send error: {str(e)}", "Email Action Failed")
				return {"status": "error", "message": str(e)}

		else:
			# Generic execution - publish event for apps to handle
			frappe.publish_realtime(
				"raven_ai_action_execute",
				{"action_id": self.name, "action_type": self.action_type, "data": action_data},
				user=self.owner,
			)

			# Check if there's a hook handler
			handlers = frappe.get_hooks("raven_ai_action_handlers", {})
			if self.action_type in handlers:
				try:
					handler = frappe.get_attr(handlers[self.action_type])
					return handler(self)
				except Exception as e:
					return {"status": "error", "message": str(e)}

			# Return generic success
			return {"status": "success", "message": f"Action {self.action_type} executed"}
