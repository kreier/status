"""Host information inspection and status detection utility.

Safely reads host information from inside a Docker container using
mounted /host files or container fallbacks.
"""

import datetime
import json
import os
import platform
import socket
import sqlite3
import time
from typing import Any, Dict, Optional

STATUS_VERSION = "v0.3.0"

# In-memory state for update checking
_update_state = {
    "checked": False,
    "available": True,  # Default matching initial version
    "last_check": None,
    "message": "Update available",
}


def _read_file_stripped(path: str) -> str:
    """Safely read a single-line file."""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def get_machine_name() -> str:
    """Detect machine / host name.
    Priority: MACHINE_NAME env -> /host/etc/hostname -> /etc/hostname -> socket.gethostname().
    """
    env_name = os.environ.get("MACHINE_NAME")
    if env_name:
        return env_name.strip()

    for host_path in ("/host/etc/hostname", "/etc/hostname"):
        name = _read_file_stripped(host_path)
        if name:
            return name

    name = socket.gethostname()
    return name if name else "Unknown"


def get_system_os() -> str:
    """Detect host operating system (e.g. Armbian, Debian, Ubuntu).
    Priority: HOST_SYSTEM env -> /host/etc/os-release -> /etc/os-release -> /host/etc/armbian-release.
    """
    env_system = os.environ.get("HOST_SYSTEM")
    if env_system:
        return env_system.strip()

    # Check for Armbian specific release file
    for armbian_path in ("/host/etc/armbian-release", "/etc/armbian-release"):
        if os.path.exists(armbian_path):
            return "Armbian"

    # Check os-release
    for path in ("/host/etc/os-release", "/etc/os-release", "/host/usr/lib/os-release"):
        if os.path.exists(path):
            try:
                data = {}
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            k, v = line.split("=", 1)
                            data[k.strip()] = v.strip().strip('"').strip("'")
                
                # Check for Armbian in NAME or PRETTY_NAME
                name = data.get("NAME", "")
                pretty = data.get("PRETTY_NAME", "")
                if "Armbian" in name or "Armbian" in pretty:
                    return "Armbian"
                if name:
                    return name
            except Exception:
                pass

    return platform.system() or "Linux"


def get_kernel() -> str:
    """Return host kernel version (shared with container)."""
    return platform.release() or os.uname().release


def get_architecture() -> str:
    """Return normalized architecture name (e.g., armhf, arm64, amd64)."""
    arch = platform.machine().lower()
    mapping = {
        "armv7l": "armhf",
        "armv6l": "armhf",
        "aarch64": "arm64",
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "i386": "x86",
        "i686": "x86",
    }
    return mapping.get(arch, arch)


def get_uptime() -> Dict[str, Any]:
    """Return host uptime formatted string and total seconds."""
    uptime_seconds = 0
    for proc_path in ("/host/proc/uptime", "/proc/uptime"):
        if os.path.exists(proc_path):
            try:
                with open(proc_path, "r", encoding="utf-8") as f:
                    uptime_seconds = int(float(f.readline().split()[0]))
                    break
            except Exception:
                pass

    if uptime_seconds == 0:
        return {"formatted": "unknown", "seconds": 0}

    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60

    if days > 0:
        formatted = f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        formatted = f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        formatted = f"{minutes} minute{'s' if minutes != 1 else ''}"

    return {
        "formatted": formatted,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": uptime_seconds,
    }


def _format_tuptime_duration(seconds: int) -> str:
    """Format seconds into tuptime-style duration (e.g. 2yr 222d 4h 14m 24s)."""
    if seconds < 0:
        seconds = 0
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    years, days = divmod(days, 365)

    parts = []
    if years > 0:
        parts.append(f"{years}yr")
    if days > 0 or years > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0 or years > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0 or years > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)


def get_tuptime() -> Dict[str, Any]:
    """Inspect historical uptime statistics from tuptime SQLite database if available."""
    db_paths = []
    custom_db = os.environ.get("TUPTIME_DB")
    if custom_db:
        db_paths.append(custom_db)
    db_paths.extend([
        "/host/var/lib/tuptime/tuptime.db",
        "/var/lib/tuptime/tuptime.db",
        "/host/etc/tuptime/tuptime.db",
        "/etc/tuptime/tuptime.db",
    ])

    target_db = None
    for p in db_paths:
        if os.path.isfile(p):
            target_db = p
            break

    if not target_db:
        return {
            "available": False,
            "system_life": "not available",
            "uptime_rate_formatted": "not available",
            "reason": "tuptime database not found (/host/var/lib/tuptime/tuptime.db). Mount /var/lib/tuptime in docker-compose.yml",
        }

    try:
        try:
            conn = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True, timeout=2.0)
        except Exception:
            conn = sqlite3.connect(target_db, timeout=2.0)

        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT rowid, bootid, btime, uptime, rntime, slptime, offbtime, endst, downtime, kernel "
            "FROM tuptime ORDER BY rowid ASC"
        ).fetchall()
        conn.close()

        if not rows:
            return {
                "available": False,
                "system_life": "not available",
                "uptime_rate_formatted": "not available",
                "reason": "tuptime database is empty",
            }

        startups = len(rows)
        shutdowns_ok = sum(1 for r in rows if r["offbtime"] is not None and r["endst"] == 1)
        shutdowns_bad = sum(1 for r in rows if r["offbtime"] is not None and r["endst"] == 0)

        curr_uptime_sec = get_uptime().get("seconds", 0)

        last_row = rows[-1]
        if last_row["offbtime"] is None:
            # System is currently running on this boot
            current_boot_up = max(last_row["uptime"] or 0, curr_uptime_sec)
            total_up = sum(r["uptime"] or 0 for r in rows[:-1]) + current_boot_up
        else:
            total_up = sum(r["uptime"] or 0 for r in rows)

        total_down = sum(r["downtime"] or 0 for r in rows if r["downtime"] is not None)
        system_life = total_up + total_down

        rate = round((total_up * 100.0) / system_life, 2) if system_life > 0 else 0.0

        return {
            "available": True,
            "startups": startups,
            "shutdowns_ok": shutdowns_ok,
            "shutdowns_bad": shutdowns_bad,
            "shutdowns_formatted": f"{shutdowns_ok} ok + {shutdowns_bad} bad",
            "system_life": _format_tuptime_duration(system_life),
            "system_life_seconds": system_life,
            "uptime_rate": rate,
            "uptime_rate_formatted": f"{rate:.2f}%",
            "total_uptime": _format_tuptime_duration(total_up),
            "total_uptime_seconds": total_up,
            "total_downtime": _format_tuptime_duration(total_down),
            "total_downtime_seconds": total_down,
        }
    except Exception as e:
        return {
            "available": False,
            "system_life": "not available",
            "uptime_rate_formatted": "not available",
            "reason": f"error reading tuptime database: {str(e)}",
        }


def get_uptime_history(days: int = 90) -> Dict[str, Any]:
    """Calculate daily uptime percentages, total uptime seconds, and bad shutdowns over past N days from tuptime.db."""
    if days < 1:
        days = 1
    elif days > 365:
        days = 365

    db_paths = []
    custom_db = os.environ.get("TUPTIME_DB")
    if custom_db:
        db_paths.append(custom_db)
    db_paths.extend([
        "/host/var/lib/tuptime/tuptime.db",
        "/var/lib/tuptime/tuptime.db",
        "/host/etc/tuptime/tuptime.db",
        "/etc/tuptime/tuptime.db",
    ])

    target_db = None
    for p in db_paths:
        if os.path.isfile(p):
            target_db = p
            break

    if not target_db:
        return {
            "available": False,
            "days": days,
            "history": [],
            "reason": "tuptime database not found (/host/var/lib/tuptime/tuptime.db)",
        }

    try:
        try:
            conn = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True, timeout=2.0)
        except Exception:
            conn = sqlite3.connect(target_db, timeout=2.0)

        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT rowid, bootid, btime, uptime, offbtime, endst, downtime FROM tuptime ORDER BY btime ASC"
        ).fetchall()
        conn.close()

        if not rows:
            return {
                "available": False,
                "days": days,
                "history": [],
                "reason": "tuptime database is empty",
            }

        now = int(time.time())
        first_boot_time = rows[0]["btime"]

        boots = []
        for r in rows:
            b_start = r["btime"]
            b_end = r["offbtime"] if r["offbtime"] is not None else now
            boots.append({
                "start": b_start,
                "end": b_end,
                "endst": r["endst"],
            })

        today = datetime.date.today()
        history = []
        total_tracked_secs = 0
        total_up_secs = 0
        total_bad_shutdowns = 0

        for i in range(days - 1, -1, -1):
            d = today - datetime.timedelta(days=i)
            d_start = int(datetime.datetime.combine(d, datetime.time.min).timestamp())
            d_end = now if i == 0 else int(datetime.datetime.combine(d, datetime.time.max).timestamp())
            day_duration = max(1, d_end - d_start)

            if d_end < first_boot_time:
                history.append({
                    "date": str(d),
                    "weekday": d.weekday(),
                    "uptime_pct": None,
                    "uptime_seconds": 0,
                    "total_seconds": day_duration,
                    "bad_shutdowns": 0,
                    "status": "unrecorded",
                })
                continue

            day_up = 0
            bad_shutdowns = 0
            for b in boots:
                overlap = max(0, min(b["end"], d_end) - max(b["start"], d_start))
                day_up += overlap
                if b["endst"] == 0 and d_start <= b["end"] <= d_end:
                    bad_shutdowns += 1

            pct = 100.0 if day_up >= (day_duration - 60) else round((day_up / day_duration) * 100.0, 1)
            total_tracked_secs += day_duration
            total_up_secs += day_up
            total_bad_shutdowns += bad_shutdowns

            history.append({
                "date": str(d),
                "weekday": d.weekday(),
                "uptime_pct": min(100.0, pct),
                "uptime_seconds": day_up,
                "total_seconds": day_duration,
                "bad_shutdowns": bad_shutdowns,
                "status": "online" if pct > 0 else "offline",
            })

        overall_rate = round((total_up_secs * 100.0) / total_tracked_secs, 2) if total_tracked_secs > 0 else 0.0

        return {
            "available": True,
            "days": days,
            "overall_rate": overall_rate,
            "overall_rate_formatted": f"{overall_rate:.2f}%",
            "total_bad_shutdowns": total_bad_shutdowns,
            "history": history,
        }
    except Exception as e:
        return {
            "available": False,
            "days": days,
            "history": [],
            "reason": f"error computing uptime history: {str(e)}",
        }


def get_versions() -> Dict[str, str]:
    """Return component versions (Application, Status, Updater).
    Dynamically checks host version files before falling back to defaults.
    """
    # 1. Status version: env -> VERSION file -> internal STATUS_VERSION
    status_ver = os.environ.get("STATUS_VERSION")
    if not status_ver:
        for vf in ("/app/VERSION", "VERSION"):
            v = _read_file_stripped(vf)
            if v:
                status_ver = v if v.startswith("v") else f"v{v}"
                break
    if not status_ver:
        status_ver = STATUS_VERSION

    # 2. Updater version: env -> trigger dir stamp -> updater dir -> default
    updater_ver = os.environ.get("UPDATER_VERSION")
    if not updater_ver:
        for uf in (
            "/host/trigger/updater_version",
            "/host/trigger/version.txt",
            "/host/updater/version.txt",
            "/host/updater/VERSION",
        ):
            u = _read_file_stripped(uf)
            if u:
                updater_ver = u if u.startswith("v") else f"v{u}"
                break
    if not updater_ver:
        updater_ver = "v0.1.0"

    # 3. Application version: env -> host app version file -> defaults to status_ver
    app_ver = os.environ.get("APPLICATION_VERSION") or os.environ.get("APP_VERSION")
    if not app_ver:
        for af in (
            "/host/app/version.txt",
            "/host/app/VERSION",
            "/host/version.txt",
            "/host/VERSION",
        ):
            a = _read_file_stripped(af)
            if a:
                app_ver = a if a.startswith("v") else f"v{a}"
                break
    if not app_ver:
        app_ver = status_ver

    return {
        "application": app_ver,
        "status": status_ver,
        "updater": updater_ver,
    }


def _parse_semver(ver: str) -> tuple:
    """Parse version string into integer tuple for comparison."""
    try:
        cleaned = ver.strip().lstrip("v").split("-")[0].split("+")[0]
        parts = [int(p) for p in cleaned.split(".") if p.isdigit()]
        return tuple(parts) if parts else (0, 0, 0)
    except Exception:
        return (0, 0, 0)


def check_updates() -> Dict[str, Any]:
    """Check for available updates against GitHub Releases API or env override."""
    env_update = os.environ.get("UPDATES_AVAILABLE")
    if env_update is not None:
        avail = env_update.strip().lower() in ("true", "1", "yes", "y")
        return {
            "available": avail,
            "status_text": "YES" if avail else "NO",
            "message": "Updates available (forced)" if avail else "Up to date (forced)",
            "latest_version": None,
        }

    repo = os.environ.get("CHECK_REPO", "kreier/status").strip()
    status_ver = os.environ.get("STATUS_VERSION", STATUS_VERSION)
    latest_ver = None
    avail = False
    message = "All components up to date"

    try:
        import urllib.request

        # 1. Check via GitHub HTML releases redirect (avoids unauthenticated API rate limits)
        html_url = f"https://github.com/{repo}/releases/latest"
        req = urllib.request.Request(
            html_url,
            headers={
                "User-Agent": f"status-monitor/{STATUS_VERSION} (Mozilla/5.0)",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                final_url = resp.geturl()
                if "/releases/tag/" in final_url:
                    latest_ver = final_url.split("/releases/tag/")[-1].strip()
        except Exception:
            pass

        # 2. Fallback to GitHub REST API if not resolved by redirect
        if not latest_ver:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            headers = {
                "User-Agent": f"status-monitor/{STATUS_VERSION}",
                "Accept": "application/vnd.github.v3+json",
            }
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req_api = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req_api, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    latest_ver = data.get("tag_name", "").strip()

        if latest_ver:
            curr_tuple = _parse_semver(status_ver)
            latest_tuple = _parse_semver(latest_ver)
            if latest_tuple > curr_tuple:
                avail = True
                message = f"New version available: {latest_ver}"
            else:
                avail = False
                message = f"Up to date ({status_ver})"
        else:
            message = f"Up to date ({status_ver})"
    except Exception as e:
        # Fallback to cached state or report offline check
        if _update_state.get("checked"):
            return {
                "available": _update_state.get("available", False),
                "status_text": "YES" if _update_state.get("available", False) else "NO",
                "message": _update_state.get("message", "Up to date"),
                "latest_version": _update_state.get("latest_version"),
            }
        message = f"Remote check unavailable ({type(e).__name__})"

    _update_state["checked"] = True
    _update_state["available"] = avail
    _update_state["latest_version"] = latest_ver
    _update_state["message"] = message

    return {
        "available": avail,
        "status_text": "YES" if avail else "NO",
        "latest_version": latest_ver,
        "message": message,
    }


def trigger_update() -> Dict[str, Any]:
    """Trigger update process for host components via trigger file, Watchtower API, or host script."""
    # 1. Check for trigger file mechanism (Method B - Secure decoupled host trigger)
    trigger_dir = "/host/trigger"
    if os.path.exists(trigger_dir) and os.path.isdir(trigger_dir):
        try:
            trigger_file = os.path.join(trigger_dir, "update")
            with open(trigger_file, "w") as f:
                f.write(f"trigger {STATUS_VERSION}")
            return {
                "success": True,
                "message": "Update triggered! Host updater is pulling and recreating container...",
            }
        except Exception as e:
            return {"success": False, "message": f"Could not write trigger: {str(e)}"}

    # 2. Check for Watchtower HTTP API (Method A)
    watchtower_url = os.environ.get("WATCHTOWER_URL")
    if watchtower_url:
        try:
            import urllib.request
            token = os.environ.get("WATCHTOWER_TOKEN", "")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            req = urllib.request.Request(watchtower_url, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 204):
                    return {
                        "success": True,
                        "message": "Watchtower update triggered successfully.",
                    }
        except Exception as e:
            return {"success": False, "message": f"Watchtower trigger failed: {str(e)}"}

    # 3. Check for host update script
    update_script = os.environ.get("UPDATE_SCRIPT", "/host/update.sh")
    if os.path.exists(update_script) and os.access(update_script, os.X_OK):
        try:
            import subprocess
            res = subprocess.run([update_script], capture_output=True, text=True, timeout=60)
            return {
                "success": res.returncode == 0,
                "message": res.stdout.strip() or "Update script executed",
                "output": res.stdout,
                "error": res.stderr,
            }
        except Exception as e:
            return {"success": False, "message": f"Update failed: {str(e)}"}

    return {
        "success": True,
        "message": "Update triggered (simulate: no updater script or Watchtower configured).",
    }


def get_all_status() -> Dict[str, Any]:
    """Aggregate all status data for UI and API consumption."""
    machine = get_machine_name()
    sys_os = get_system_os()
    kernel = get_kernel()
    arch = get_architecture()
    uptime = get_uptime()
    tuptime = get_tuptime()
    versions = get_versions()
    update_info = check_updates()

    return {
        "machine": machine,
        "system": {
            "os": sys_os,
            "kernel": kernel,
            "architecture": arch,
            "uptime": uptime["formatted"],
            "uptime_seconds": uptime["seconds"],
        },
        "tuptime": tuptime,
        "versions": versions,
        "updates": update_info,
    }
