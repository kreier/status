#!/usr/bin/env python3
"""Test suite for HTTP handling in app.py."""

import json
import os
import unittest
from io import BytesIO
from unittest.mock import MagicMock

os.environ["MACHINE_NAME"] = "RK3229"
import app

class TestApp(unittest.TestCase):
    def test_import_and_structure(self):
        # Verify app module has host_info
        self.assertTrue(hasattr(app, "host_info"))

    def test_status_payload(self):
        status = app.host_info.get_all_status()
        self.assertEqual(status["machine"], "RK3229")
        self.assertIn("system", status)
        self.assertIn("versions", status)
        self.assertIn("updates", status)

if __name__ == "__main__":
    unittest.main()
