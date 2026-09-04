"""Writing collector output: status.json (merged by id) and append-only history logs
(e.g. speedtest_history.jsonl for the heatmap). See docs/SCHEMA.md for the entry shape."""

import json
import os
from datetime import datetime, timezone

DATA_DIR = os.environ.get("STATUS_DATA_DIR", "/data")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def append_history(name, row: dict):
    path = os.path.join(DATA_DIR, f"{name}_history.jsonl")
    row = {**row, "timestamp": now_iso()}
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def write_entries(entries):
    """Merge a list of {"id": ..., ...} entries into status.json, keyed by id.
    Other collectors' entries are preserved - each collector only touches its own ids."""
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
