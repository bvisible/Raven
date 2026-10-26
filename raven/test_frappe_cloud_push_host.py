from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import jwt

from raven.frappe_cloud_push import get_registration_site_name


class TestRegistrationSiteName(TestCase):
	def setUp(self):
		self.sites_path = Path(self.enterContext(TemporaryDirectory()))
		self.enterContext(patch("frappe.local.sites_path", str(self.sites_path), create=True))
		self.add_site("site.local")

	def add_site(self, name):
		site = self.sites_path / name
		site.mkdir()
		(site / "site_config.json").write_text("{}")

	def select_host(self, hosts, site_name="site.local"):
		token = jwt.encode({"hosts": hosts}, "", algorithm="none")
		return get_registration_site_name(token, site_name)

	def test_prefers_a_host_without_the_generated_prefix(self):
		self.assertEqual(
			self.select_host(["site-123.bom.frappe.cloud", "acme.bom.frappe.cloud"]),
			"acme.bom.frappe.cloud",
		)

	def test_can_choose_any_generated_host(self):
		hosts = ["site-123.bom.frappe.cloud", "site-456.bom.frappe.cloud"]
		self.assertIn(self.select_host(hosts), hosts)

	def test_keeps_a_hostname_already_in_the_token(self):
		self.assertEqual(self.select_host(["site.local", "acme.bom.frappe.cloud"]), "site.local")

	def test_keeps_the_hostname_when_no_hosts_are_available(self):
		self.assertEqual(self.select_host([]), "site.local")

	def test_does_not_choose_a_host_on_a_multisite_bench(self):
		self.add_site("second.local")
		self.assertEqual(self.select_host(["acme.bom.frappe.cloud"]), "site.local")

	def test_ignores_symlinks_and_non_site_directories(self):
		(self.sites_path / "alias.local").symlink_to(self.sites_path / "site.local")
		(self.sites_path / "assets").mkdir()
		self.assertEqual(self.select_host(["acme.bom.frappe.cloud"]), "acme.bom.frappe.cloud")

	def test_does_not_choose_a_host_without_any_sites(self):
		(self.sites_path / "site.local" / "site_config.json").unlink()
		self.assertEqual(self.select_host(["acme.bom.frappe.cloud"]), "site.local")
