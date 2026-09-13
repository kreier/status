"""Uptime, load average, memory. Cheap and local - runs without psutil."""

import os
import time

from core.status import write_entries


def _get_meminfo():
    """Read memory info from /proc/meminfo."""
    mem = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem[key] = int(val)  # in kB
        total = mem.get("MemTotal", 1024 * 1024)
        available = mem.get("MemAvailable", mem.get("MemFree", 0))
        used = total - available
        percent = (used / total) * 100
        return percent, used // 1024, total // 1024
    except Exception:
        return 0.0, 0, 0


def collect():
    try:
        load1, load5, load15 = os.getloadavg()
    except (AttributeError, OSError):
        load1, load5, load15 = 0.0, 0.0, 0.0

    percent, used_mb, total_mb = _get_meminfo()

    uptime_s = 0
    try:
        with open("/proc/uptime", "r") as f:
            uptime_s = int(float(f.readline().split()[0]))
    except Exception:
        pass

    days, rem = divmod(uptime_s, 86400)
    hours, minutes = divmod(rem, 3600)
    minutes //= 60

    entries = [
        {"id": "pi_uptime", "category": "system", "label": "Uptime",
         "value": f"{days}d {hours}h {minutes}m", "status": "ok"},
        {"id": "pi_load", "category": "system", "label": "Load average (1/5/15 min)",
         "value": f"{load1:.2f}, {load5:.2f}, {load15:.2f}", "status": "ok"},
        {"id": "pi_memory", "category": "system", "label": "Memory",
         "value": f"{percent:.0f}% used ({used_mb} / {total_mb} MB)",
         "status": "ok"},
    ]
    write_entries(entries)
    return entries


if __name__ == "__main__":
    print(collect())
