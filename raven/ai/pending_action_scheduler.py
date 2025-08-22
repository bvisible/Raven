from datetime import datetime, timedelta

import frappe


def purge_old_pending_actions():
	"""
	Purge old pending actions from Redis.
	Called by scheduler to clean up:
	- Actions with status 'done' older than 3 days
	- Actions with status 'cancelled' or 'failed' older than 1 day
	- Actions with status 'pending' older than 30 minutes
	"""
	try:
		# Get all action IDs from global list
		from raven.raven.doctype.raven_ai_pending_action.raven_ai_pending_action import (
			RavenAIPendingAction,
		)

		global_key = f"{RavenAIPendingAction.REDIS_PREFIX}all"
		all_action_ids = frappe.cache().get_value(global_key) or []

		purged_count = 0
		updated_ids = []

		for action_id in all_action_ids:
			key = f"{RavenAIPendingAction.REDIS_PREFIX}{action_id}"
			data = frappe.cache().get_value(key)

			if data:
				# Check if action should be purged based on status and age
				should_purge = False

				if "expires_at" in data:
					# Check if expired
					expires_at = datetime.fromisoformat(data["expires_at"])
					if expires_at < datetime.now():
						should_purge = True
				else:
					# Fall back to status-based purging
					created_at = datetime.fromisoformat(data.get("creation", datetime.now().isoformat()))
					age = datetime.now() - created_at

					status = data.get("status", "pending")

					if status == "done" and age > timedelta(days=3):
						should_purge = True
					elif status in ["cancelled", "failed"] and age > timedelta(days=1):
						should_purge = True
					elif status == "pending" and age > timedelta(minutes=30):
						should_purge = True

				if should_purge:
					# Delete from Redis
					frappe.cache().delete_value(key)

					# Remove from user's list
					owner = data.get("owner")
					if owner:
						user_key = f"{RavenAIPendingAction.REDIS_PREFIX}user:{owner}"
						user_actions = frappe.cache().get_value(user_key) or []
						if action_id in user_actions:
							user_actions.remove(action_id)
							frappe.cache().set_value(user_key, user_actions)

					purged_count += 1
				else:
					# Keep this action
					updated_ids.append(action_id)

		# Update global list with remaining actions
		if purged_count > 0:
			frappe.cache().set_value(global_key, updated_ids)

		return purged_count

	except Exception as e:
		frappe.log_error(f"Error purging pending actions: {str(e)}", "Pending Action Purge Error")
		return 0
