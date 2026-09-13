#!/usr/bin/env python3
"""Test suite for HTTP handling in app.py."""

import json
import os
import unittest

os.environ["MACHINE_NAME"] = "RK3229"
import app

class TestApp(unittest.TestCase):
    def test_import_and_structure(self):
        self.assertTrue(hasattr(app, "host_info"))

    def test_status_payload(self):
        status = app.host_info.get_all_status()
        self.assertEqual(status["machine"], "RK3229")
        self.assertIn("system", status)
        self.assertIn("versions", status)
        self.assertIn("updates", status)

    def test_flask_routes_if_available(self):
        if app.app is not None:
            with app.app.test_client() as c:
                for path in ["/", "/status", "/status/"]:
                    res = c.get(path)
                    self.assertEqual(res.status_code, 200, f"Failed for {path}")
                    self.assertIn(b"html", res.data.lower())

                for path in ["/api", "/api/status", "/status/api", "/status/api/status"]:
                    res = c.get(path)
                    self.assertEqual(res.status_code, 200, f"Failed for {path}")
                    data = json.loads(res.data)
                    self.assertEqual(data["machine"], "RK3229")

if __name__ == "__main__":
    unittest.main()
