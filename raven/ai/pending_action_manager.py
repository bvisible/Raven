"""
Pending Action Manager for Raven AI
Centralized management of confirmation workflows and pending actions
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import frappe


class PendingActionManager:
	"""
	Unified manager for all pending actions in Raven AI.
	Simplifies confirmation workflows and reduces code duplication.
	"""

	@staticmethod
	def create(
		action_type: str,
		data: dict,
		auto_execute: bool = False,
		user: str = None,
		channel_id: str = None,
		expires_in_minutes: int = 30,
	) -> dict[str, Any]:
		"""
		Create a pending action or execute directly based on permissions.

		Args:
		    action_type: Type of action ('email', 'update', 'delete', 'create')
		    data: Action-specific data
		    auto_execute: If True and permissions allow, execute immediately
		    user: User creating the action (defaults to current user)
		    channel_id: Associated Raven channel
		    expires_in_minutes: Minutes until action expires

		Returns:
		    Dict with status ('success', 'pending', 'error') and relevant data
		"""
		try:
			user = user or frappe.session.user

			# Check if auto-execution is allowed
			if auto_execute and PendingActionManager._can_auto_execute(action_type, user):
				return PendingActionManager._execute_action(action_type, data, user, channel_id)

			# Create pending action
			expiry = datetime.now() + timedelta(minutes=expires_in_minutes)

			# Check if DocType exists, if not create a simple cache entry
			if frappe.db.exists("DocType", "Raven AI Pending Action"):
				action = frappe.get_doc(
					{
						"doctype": "Raven AI Pending Action",
						"action_type": action_type,
						"action_data": json.dumps(data),
						"status": "pending",
						"user": user,
						"channel_id": channel_id,
						"expires_at": expiry,
						"created_at": datetime.now(),
					}
				)
				action.insert(ignore_permissions=True)
				action_id = action.name
			else:
				# Fallback to cache-based storage
				action_id = frappe.generate_hash(length=10)
				cache_key = f"pending_action_{action_id}"

				frappe.cache().set_value(
					cache_key,
					{
						"action_type": action_type,
						"data": data,
						"user": user,
						"channel_id": channel_id,
						"created_at": datetime.now().isoformat(),
					},
					expires_in_sec=expires_in_minutes * 60,
				)

			# Generate user-friendly message
			message = PendingActionManager._get_confirmation_message(action_type, data)

			return {
				"status": "pending",
				"action_id": action_id,
				"message": message,
				"expires_in": expires_in_minutes,
				"data": {
					"action_type": action_type,
					"preview": PendingActionManager._get_action_preview(action_type, data),
				},
			}

		except Exception as e:
			frappe.log_error(f"Failed to create pending action: {str(e)}", "PendingActionManager")
			return {"status": "error", "message": f"Erreur lors de la création de l'action: {str(e)}"}

	@staticmethod
	def confirm(action_id: str, user: str = None) -> dict[str, Any]:
		"""
		Confirm and execute a pending action.

		Args:
		    action_id: ID of the pending action
		    user: User confirming (must match creator)

		Returns:
		    Execution result
		"""
		try:
			user = user or frappe.session.user
			action_data = None

			# Try to get from DocType first
			if frappe.db.exists("DocType", "Raven AI Pending Action"):
				if frappe.db.exists("Raven AI Pending Action", action_id):
					action = frappe.get_doc("Raven AI Pending Action", action_id)

					# Validate user
					if action.user != user:
						return {"status": "error", "message": "Vous ne pouvez pas confirmer cette action"}

					# Check if expired
					if action.expires_at and action.expires_at < datetime.now():
						action.status = "expired"
						action.save(ignore_permissions=True)
						return {"status": "error", "message": "Cette action a expiré"}

					# Check if already processed
					if action.status != "pending":
						return {"status": "error", "message": f"Action déjà {action.status}"}

					action_data = {
						"action_type": action.action_type,
						"data": json.loads(action.action_data),
						"channel_id": action.channel_id,
					}

					# Update status
					action.status = "processing"
					action.save(ignore_permissions=True)

			# Fallback to cache
			if not action_data:
				cache_key = f"pending_action_{action_id}"
				cached = frappe.cache().get_value(cache_key)

				if not cached:
					return {"status": "error", "message": "Action introuvable ou expirée"}

				if cached.get("user") != user:
					return {"status": "error", "message": "Vous ne pouvez pas confirmer cette action"}

				action_data = {
					"action_type": cached["action_type"],
					"data": cached["data"],
					"channel_id": cached.get("channel_id"),
				}

				# Remove from cache
				frappe.cache().delete_value(cache_key)

			# Execute the action
			result = PendingActionManager._execute_action(
				action_data["action_type"], action_data["data"], user, action_data.get("channel_id")
			)

			# Update status if using DocType
			if frappe.db.exists("DocType", "Raven AI Pending Action"):
				if frappe.db.exists("Raven AI Pending Action", action_id):
					action = frappe.get_doc("Raven AI Pending Action", action_id)
					action.status = "completed" if result.get("status") == "success" else "failed"
					action.result = json.dumps(result)
					action.completed_at = datetime.now()
					action.save(ignore_permissions=True)

			return result

		except Exception as e:
			frappe.log_error(f"Failed to confirm action: {str(e)}", "PendingActionManager")
			return {"status": "error", "message": f"Erreur lors de la confirmation: {str(e)}"}

	@staticmethod
	def confirm_last(user: str = None, channel_id: str = None) -> dict[str, Any]:
		"""
		Confirm the last pending action for a user.

		Args:
		    user: User to check for
		    channel_id: Optional channel filter

		Returns:
		    Confirmation result
		"""
		try:
			user = user or frappe.session.user

			# Try DocType first
			if frappe.db.exists("DocType", "Raven AI Pending Action"):
				filters = {"user": user, "status": "pending"}
				if channel_id:
					filters["channel_id"] = channel_id

				actions = frappe.get_list(
					"Raven AI Pending Action", filters=filters, order_by="created_at desc", limit=1, pluck="name"
				)

				if actions:
					return PendingActionManager.confirm(actions[0], user)

			# Fallback: Check cache for recent actions
			# This would need a list of action IDs stored per user
			# For now, return not found
			return {"status": "error", "message": "Aucune action en attente trouvée"}

		except Exception as e:
			frappe.log_error(f"Failed to confirm last action: {str(e)}", "PendingActionManager")
			return {"status": "error", "message": f"Erreur: {str(e)}"}

	@staticmethod
	def cancel(action_id: str, user: str = None) -> dict[str, Any]:
		"""
		Cancel a pending action.

		Args:
		    action_id: ID of the action to cancel
		    user: User cancelling (must match creator)

		Returns:
		    Cancellation result
		"""
		try:
			user = user or frappe.session.user

			# Try DocType first
			if frappe.db.exists("DocType", "Raven AI Pending Action"):
				if frappe.db.exists("Raven AI Pending Action", action_id):
					action = frappe.get_doc("Raven AI Pending Action", action_id)

					if action.user != user:
						return {"status": "error", "message": "Vous ne pouvez pas annuler cette action"}

					if action.status != "pending":
						return {"status": "error", "message": f"Action déjà {action.status}"}

					action.status = "cancelled"
					action.completed_at = datetime.now()
					action.save(ignore_permissions=True)

					return {"status": "success", "message": "Action annulée"}

			# Fallback to cache
			cache_key = f"pending_action_{action_id}"
			cached = frappe.cache().get_value(cache_key)

			if cached and cached.get("user") == user:
				frappe.cache().delete_value(cache_key)
				return {"status": "success", "message": "Action annulée"}

			return {"status": "error", "message": "Action introuvable"}

		except Exception as e:
			frappe.log_error(f"Failed to cancel action: {str(e)}", "PendingActionManager")
			return {"status": "error", "message": f"Erreur: {str(e)}"}

	@staticmethod
	def list_pending(user: str = None, channel_id: str = None) -> list[dict]:
		"""
		List all pending actions for a user.

		Args:
		    user: User to list for
		    channel_id: Optional channel filter

		Returns:
		    List of pending actions
		"""
		try:
			user = user or frappe.session.user
			actions = []

			if frappe.db.exists("DocType", "Raven AI Pending Action"):
				filters = {"user": user, "status": "pending"}
				if channel_id:
					filters["channel_id"] = channel_id

				db_actions = frappe.get_list(
					"Raven AI Pending Action",
					filters=filters,
					fields=["name", "action_type", "action_data", "created_at", "expires_at"],
					order_by="created_at desc",
				)

				for action in db_actions:
					data = json.loads(action.action_data)
					actions.append(
						{
							"id": action.name,
							"type": action.action_type,
							"preview": PendingActionManager._get_action_preview(action.action_type, data),
							"created": action.created_at,
							"expires": action.expires_at,
						}
					)

			return actions

		except Exception as e:
			frappe.log_error(f"Failed to list pending actions: {str(e)}", "PendingActionManager")
			return []

	@staticmethod
	def _can_auto_execute(action_type: str, user: str) -> bool:
		"""Check if user can auto-execute this action type"""
		# Check user permissions
		permission_map = {"email": "Email", "update": "Write", "delete": "Delete", "create": "Create"}

		# For now, only allow auto-execute for system users or specific roles
		if user == "Administrator":
			return True

		# Check if user has specific role
		user_roles = frappe.get_roles(user)
		if "AI Auto Execute" in user_roles:
			return True

		# Check specific permission for action type
		if action_type in permission_map:
			# This would check actual DocType permissions
			# For now, return False for safety
			return False

		return False

	@staticmethod
	def _execute_action(
		action_type: str, data: dict, user: str, channel_id: str = None
	) -> dict[str, Any]:
		"""Execute the actual action"""
		try:
			if action_type == "email":
				return PendingActionManager._execute_email(data)
			elif action_type == "update":
				return PendingActionManager._execute_update(data)
			elif action_type == "delete":
				return PendingActionManager._execute_delete(data)
			elif action_type == "create":
				return PendingActionManager._execute_create(data)
			else:
				# Custom action type - try to find handler
				handler = frappe.get_attr(f"raven.ai.actions.{action_type}_handler")
				if handler:
					return handler(data, user, channel_id)
				else:
					return {"status": "error", "message": f"Type d'action inconnu: {action_type}"}
		except Exception as e:
			frappe.log_error(f"Action execution failed: {str(e)}", "PendingActionManager")
			return {"status": "error", "message": f"Erreur d'exécution: {str(e)}"}

	@staticmethod
	def _execute_email(data: dict) -> dict[str, Any]:
		"""Execute email sending"""
		try:
			frappe.sendmail(
				recipients=data.get("to"),
				subject=data.get("subject", "No Subject"),
				message=data.get("message"),
				attachments=data.get("attachments"),
				delayed=False,
			)

			return {"status": "success", "message": f"Email envoyé à {data.get('to')}"}
		except Exception as e:
			return {"status": "error", "message": f"Erreur d'envoi: {str(e)}"}

	@staticmethod
	def _execute_update(data: dict) -> dict[str, Any]:
		"""Execute document update"""
		try:
			doc = frappe.get_doc(data.get("doctype"), data.get("name"))

			for field, value in data.get("updates", {}).items():
				doc.set(field, value)

			doc.save()

			return {
				"status": "success",
				"message": f"{data.get('doctype')} mis à jour",
				"document": doc.name,
			}
		except Exception as e:
			return {"status": "error", "message": f"Erreur de mise à jour: {str(e)}"}

	@staticmethod
	def _execute_delete(data: dict) -> dict[str, Any]:
		"""Execute document deletion"""
		try:
			frappe.delete_doc(data.get("doctype"), data.get("name"), force=data.get("force", False))

			return {"status": "success", "message": f"{data.get('doctype')} supprimé"}
		except Exception as e:
			return {"status": "error", "message": f"Erreur de suppression: {str(e)}"}

	@staticmethod
	def _execute_create(data: dict) -> dict[str, Any]:
		"""Execute document creation"""
		try:
			doc = frappe.get_doc({"doctype": data.get("doctype"), **data.get("fields", {})})
			doc.insert()

			return {"status": "success", "message": f"{data.get('doctype')} créé", "document": doc.name}
		except Exception as e:
			return {"status": "error", "message": f"Erreur de création: {str(e)}"}

	@staticmethod
	def _get_confirmation_message(action_type: str, data: dict) -> str:
		"""Generate user-friendly confirmation message"""
		messages = {
			"email": f"Confirmez l'envoi d'email à {data.get('to')}",
			"update": f"Confirmez la mise à jour de {data.get('doctype')} {data.get('name')}",
			"delete": f"Confirmez la suppression de {data.get('doctype')} {data.get('name')}",
			"create": f"Confirmez la création de {data.get('doctype')}",
		}

		return messages.get(
			action_type, f"Confirmez l'action '{action_type}' - Répondez 'ok' pour continuer"
		)

	@staticmethod
	def _get_action_preview(action_type: str, data: dict) -> str:
		"""Generate preview of action for display"""
		if action_type == "email":
			return f"Email à {data.get('to')}: {data.get('subject', 'Sans sujet')}"
		elif action_type == "update":
			updates = data.get("updates", {})
			return f"Mise à jour {data.get('doctype')}: {len(updates)} champs"
		elif action_type == "delete":
			return f"Suppression {data.get('doctype')} {data.get('name')}"
		elif action_type == "create":
			return f"Création {data.get('doctype')}"
		else:
			return f"Action {action_type}"


# Convenience functions for direct use
@frappe.whitelist()
def create_pending_action(
	action_type: str, data: str, auto_execute: bool = False
) -> dict[str, Any]:
	"""Whitelist wrapper for creating pending actions"""
	if isinstance(data, str):
		data = json.loads(data)
	return PendingActionManager.create(action_type, data, auto_execute)


@frappe.whitelist()
def confirm_pending_action(action_id: str) -> dict[str, Any]:
	"""Whitelist wrapper for confirming actions"""
	return PendingActionManager.confirm(action_id)


@frappe.whitelist()
def cancel_pending_action(action_id: str) -> dict[str, Any]:
	"""Whitelist wrapper for cancelling actions"""
	return PendingActionManager.cancel(action_id)


@frappe.whitelist()
def list_pending_actions() -> list[dict]:
	"""Whitelist wrapper for listing pending actions"""
	return PendingActionManager.list_pending()


@frappe.whitelist()
def confirm_last_action() -> dict[str, Any]:
	"""Whitelist wrapper for confirming last action"""
	return PendingActionManager.confirm_last()
