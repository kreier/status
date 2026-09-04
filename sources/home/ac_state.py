"""A/C on/off/mode - STUB. Fill in once the integration is chosen (see docs/HARDWARE.md:
smart plug API, IR blaster + Home Assistant, etc). Wire the real reading into collect()
below; keep the entry shape the same."""

from core.status import write_entries


def collect():
    entries = [{"id": "ac_state", "category": "home", "label": "A/C",
                "value": "not configured", "status": "stale"}]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
