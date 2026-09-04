"""Runs every collector on its own interval, as set in config.yaml. Each collector writes
its own entries into status.json (see core.status.write_entries) - the scheduler just
decides when to call each one. A failing collector logs a traceback and doesn't block others.

To add a new collector: drop a module under sources/<category>/ with a collect() function,
then register it below."""

import importlib
import time
import traceback

from core.config import load_config

COLLECTOR_MODULES = {
    "pi_stats": "sources.system.pi_stats",
    "room_temp": "sources.home.room_temp",
    "ac_state": "sources.home.ac_state",
    "speedtest": "sources.network.speedtest_collector",
    "nas_images": "sources.home.nas_images",
    "github_repos": "sources.github.github_repos",
}

DEFAULT_INTERVAL_MINUTES = 60
POLL_SECONDS = 30  # how often the scheduler checks whether anything is due


def main():
    config = load_config()
    intervals = {
        name: config.get("collectors", {}).get(name, {}).get("interval_minutes", DEFAULT_INTERVAL_MINUTES)
        for name in COLLECTOR_MODULES
    }
    modules = {name: importlib.import_module(mod) for name, mod in COLLECTOR_MODULES.items()}
    last_run = {name: 0 for name in COLLECTOR_MODULES}

    print(f"[scheduler] starting with intervals (minutes): {intervals}")

    while True:
        now = time.time()
        for name, module in modules.items():
            due_in = intervals[name] * 60 - (now - last_run[name])
            if due_in <= 0:
                try:
                    module.collect()
                    print(f"[scheduler] ran {name}")
                except Exception:
                    print(f"[scheduler] {name} failed:")
                    traceback.print_exc()
                last_run[name] = now
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
