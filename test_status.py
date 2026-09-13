#!/usr/bin/env python3
"""Test suite for host status collector and API endpoints."""

import os
import unittest
from core import host_info

class TestHostInfo(unittest.TestCase):
    def setUp(self):
        os.environ["MACHINE_NAME"] = "RK3229"
        os.environ["HOST_SYSTEM"] = "Armbian"
        os.environ["APP_VERSION"] = "v0.4.2"
        os.environ["STATUS_VERSION"] = "v0.2.0"
        os.environ["UPDATER_VERSION"] = "v0.1.1"

    def test_machine_name(self):
        self.assertEqual(host_info.get_machine_name(), "RK3229")

    def test_system_os(self):
        self.assertEqual(host_info.get_system_os(), "Armbian")

    def test_versions(self):
        versions = host_info.get_versions()
        self.assertEqual(versions["application"], "v0.4.2")
        self.assertEqual(versions["status"], "v0.2.0")
        self.assertEqual(versions["updater"], "v0.1.1")

    def test_updates(self):
        updates = host_info.check_updates()
        self.assertIn("available", updates)
        self.assertIn("status_text", updates)

    def test_get_all_status(self):
        data = host_info.get_all_status()
        self.assertEqual(data["machine"], "RK3229")
        self.assertEqual(data["system"]["os"], "Armbian")
        self.assertIn("kernel", data["system"])
        self.assertIn("architecture", data["system"])
        self.assertIn("uptime", data["system"])
        self.assertEqual(data["versions"]["application"], "v0.4.2")
        self.assertEqual(data["versions"]["status"], "v0.2.0")
        self.assertEqual(data["versions"]["updater"], "v0.1.1")
        self.assertIn(data["updates"]["status_text"], ["YES", "NO"])

    def test_trigger_update(self):
        res = host_info.trigger_update()
        self.assertIn("success", res)
        self.assertTrue(res["success"])

if __name__ == "__main__":
    unittest.main()
