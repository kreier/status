"""Config loading - repo categories, collector intervals, etc. See docs/SCHEMA.md."""

import os

import yaml

CONFIG_PATH = os.environ.get("STATUS_CONFIG_PATH", "/app/config.yaml")


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)
