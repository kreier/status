"""Hash-guard pattern: cheap fetch -> hash -> only do expensive work if something changed.
See docs/SCHEMA.md for the intent. Used by any source that rarely changes (GitHub repos,
NAS image count) to avoid wasting compute/network/energy on unchanged data."""

import hashlib
import json
import os

DATA_DIR = os.environ.get("STATUS_DATA_DIR", "/data")
STATE_DIR = os.path.join(DATA_DIR, "state")
os.makedirs(STATE_DIR, exist_ok=True)


def canonical_hash(obj):
    """Stable hash of a JSON-serializable object."""
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
