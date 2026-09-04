"""Uptime, load average, memory. Cheap and local - runs every cycle, no hash-guard needed."""

import time

import psutil

from common import write_entries


def collect():
    load1, load5, load15 = psutil.getloadavg()
    mem = psutil.virtual_memory()
    uptime_s = int(time.time() - psutil.boot_time())
    days, rem = divmod(uptime_s, 86400)
    hours, minutes = divmod(rem, 3600)
    minutes //= 60

    entries = [
        {"id": "pi_uptime", "category": "system", "label": "Uptime",
         "value": f"{days}d {hours}h {minutes}m", "status": "ok"},
        {"id": "pi_load", "category": "system", "label": "Load average (1/5/15 min)",
         "value": f"{load1:.2f}, {load5:.2f}, {load15:.2f}", "status": "ok"},
        {"id": "pi_memory", "category": "system", "label": "Memory",
         "value": f"{mem.percent:.0f}% used ({mem.used // (1024**2)} / {mem.total // (1024**2)} MB)",
         "status": "ok"},
    ]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
