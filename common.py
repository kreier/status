"""Shared helpers used by every collector. See ../SCHEMA.md for the patterns this implements."""

import hashlib
import json
import os
from datetime import datetime, timezone

import yaml

DATA_DIR = os.environ.get("STATUS_DATA_DIR", "/data")
CONFIG_PATH = os.environ.get("STATUS_CONFIG_PATH", "/app/config.yaml")
STATE_DIR = os.path.join(DATA_DIR, "state")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

os.makedirs(STATE_DIR, exist_ok=True)


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical_hash(obj):
    """Stable hash of a JSON-serializable object, used to detect 'did anything change'."""
    blob = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def run_if_changed(name, fetch_fn, process_fn):
    """Cheap fetch_fn() -> hash -> only run expensive process_fn(raw) if the hash changed.
    Returns the (possibly cached) processed result, or {"error": ...} if fetch_fn raised."""
    hash_path = os.path.join(STATE_DIR, f"{name}.hash")
    cache_path = os.path.join(STATE_DIR, f"{name}.result.json")

    try:
        raw = fetch_fn()
    except Exception as e:
        return {"error": str(e)}

    new_hash = canonical_hash(raw)
    old_hash = open(hash_path).read().strip() if os.path.exists(hash_path) else None

    if new_hash != old_hash or not os.path.exists(cache_path):
        result = process_fn(raw)
        with open(hash_path, "w") as f:
            f.write(new_hash)
        with open(cache_path, "w") as f:
            json.dump(result, f)
        return result

    with open(cache_path) as f:
        return json.load(f)


def append_history(name, row: dict):
    """Append-only log for sources that need history (e.g. speedtest), not just a latest value."""
    path = os.path.join(DATA_DIR, f"{name}_history.jsonl")
    row = {**row, "timestamp": now_iso()}
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def write_entries(entries):
    """Merge a list of {"id": ..., ...} entries into status.json, keyed by id.
    Collectors call this with their own entries; other collectors' entries are preserved."""
    current = {}
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE) as f:
            try:
                current = {e["id"]: e for e in json.load(f)}
            except Exception:
                current = {}
    for e in entries:
        e["updated_at"] = now_iso()
        current[e["id"]] = e
    tmp = STATUS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(list(current.values()), f, indent=2)
    os.replace(tmp, STATUS_FILE)
