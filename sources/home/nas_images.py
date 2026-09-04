"""NAS image count - STUB. Fill in fetch_listing() once NAS access is chosen (SMB mount, NAS
API, SSH). The hash-guard scaffolding is already wired: fetch_listing() should stay cheap
(file count + total size + latest mtime, not a full walk); do the expensive per-file
categorization inside process() only, since that only runs when the cheap listing changes."""

from core.state import run_if_changed
from core.status import write_entries


def fetch_listing():
    # TODO: replace with a real cheap listing, e.g.:
    #   count, total_size, latest_mtime = scan(nas_share_path)
    #   return {"count": count, "total_size": total_size, "latest_mtime": latest_mtime}
    return {"count": None}


def process(raw):
    return {"count": raw["count"]}


def collect():
    if fetch_listing()["count"] is None:
        entries = [{"id": "nas_images", "category": "home", "label": "NAS images",
                    "value": "not configured", "status": "stale"}]
    else:
        result = run_if_changed("nas_images", fetch_listing, process)
        entries = [{"id": "nas_images", "category": "home", "label": "NAS images",
                    "value": f"{result['count']} images", "status": "ok"}]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
