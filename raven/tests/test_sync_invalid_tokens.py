# //// Neoffice — added file (no upstream equivalent)
"""sync_invalid_tokens only talks to Raven Cloud when Raven Cloud is configured.

It read the relay secret unconditionally: on a site with another push service,
or none, get_password raised and the job failed every night (2026-09-13).
"""

import unittest
from unittest import mock

import frappe

from raven.scheduler import daily


class Settings(frappe._dict):
	def get_password(self, fieldname, raise_exception=True):
		return self.get("_secret")


class TestSyncInvalidTokens(unittest.TestCase):
	def _run(self, **settings):
		with (
			mock.patch.object(daily.frappe, "get_single", return_value=Settings(settings)),
			mock.patch.object(daily, "FrappeClient") as client,
			mock.patch.object(daily, "get_site_name", return_value="test-site"),
		):
			client.return_value.post_api.return_value = {"invalid_tokens": []}
			daily.sync_invalid_tokens()
		return client

	def test_another_push_service_is_left_alone(self):
		self.assertFalse(self._run(push_notification_service="Firebase").called)

	def test_no_secret_means_no_call(self):
		client = self._run(push_notification_service="Raven", push_notification_api_key="key")
		self.assertFalse(client.called)

	def test_raven_cloud_with_credentials_still_syncs(self):
		client = self._run(
			push_notification_service="Raven",
			push_notification_api_key="key",
			push_notification_server_url="https://push.example.invalid",
			_secret="secret",
		)
		client.assert_called_once()
		self.assertEqual(client.call_args.kwargs["api_secret"], "secret")
