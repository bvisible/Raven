# //// Neoffice — added file (no upstream equivalent)
"""sync_users_tokens_to_raven_cloud only talks to Raven Cloud when Raven Cloud is configured.

It read the relay secret unconditionally: on a site with another push service, or none, get_password raised and the daily job
failed every night, in a Scheduled Job Log row no check reads (the sibling of sync_invalid_tokens, #410; seen again 2026-10-19).
"""

import unittest
from unittest import mock

import frappe

from raven import raven_cloud_notifications as notifications


class Settings(frappe._dict):
	def get_password(self, fieldname, raise_exception=True):
		secret = self.get("_secret")
		if not secret and raise_exception:
			raise frappe.ValidationError(f"Password not found for Raven Settings {fieldname}")
		return secret


class TestSyncUsersTokensToRavenCloud(unittest.TestCase):
	def _run(self, **settings):
		with (
			mock.patch.object(notifications.frappe, "get_single", return_value=Settings(settings)),
			mock.patch.object(
				notifications.frappe,
				"db",
				mock.MagicMock(**{"get_all.return_value": [{"user": "a@x.example", "fcm_token": "t"}]}),
			),
			mock.patch.object(notifications, "make_api_call") as call,
			mock.patch.object(notifications, "get_site_name", return_value="test-site"),
		):
			call.return_value = {"message": {"status": "success"}}
			result = notifications.sync_users_tokens_to_raven_cloud()
		return call, result

	def test_another_push_service_is_left_alone(self):
		call, result = self._run(push_notification_service="Firebase")
		self.assertFalse(call.called)
		self.assertIsNone(result)

	def test_no_push_service_at_all_is_left_alone(self):
		call, _result = self._run()
		self.assertFalse(call.called)

	def test_no_api_key_means_no_call(self):
		call, _result = self._run(push_notification_service="Raven")
		self.assertFalse(call.called)

	def test_no_secret_means_no_call_and_no_error(self):
		call, _result = self._run(push_notification_service="Raven", push_notification_api_key="key")
		self.assertFalse(call.called)

	def test_raven_cloud_with_credentials_still_syncs(self):
		call, result = self._run(
			push_notification_service="Raven",
			push_notification_api_key="key",
			push_notification_server_url="https://push.example.invalid",
			_secret="secret",
		)
		call.assert_called_once()
		self.assertEqual(call.call_args.kwargs["api_secret"], "secret")
		self.assertEqual(call.call_args.kwargs["api_key"], "key")
		self.assertEqual(result, "Tokens synced successfully")
