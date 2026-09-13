"""Host information inspection and status detection utility.

Safely reads host information from inside a Docker container using
mounted /host files or container fallbacks.
"""

import os
import platform
import socket
from typing import Any, Dict

STATUS_VERSION = "v0.2.0"

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


def get_versions() -> Dict[str, str]:
    """Return component versions (Application, Status, Updater)."""
    app_ver = os.environ.get("APPLICATION_VERSION") or os.environ.get("APP_VERSION") or "v0.4.2"
    updater_ver = os.environ.get("UPDATER_VERSION") or "v0.1.1"
    status_ver = os.environ.get("STATUS_VERSION") or STATUS_VERSION

    # Also check if version files exist on host
    app_ver_file = "/host/app/version.txt"
    if os.path.exists(app_ver_file):
        custom_ver = _read_file_stripped(app_ver_file)
        if custom_ver:
            app_ver = custom_ver

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
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "status-monitor/0.1.0",
                "Accept": "application/vnd.github.v3+json",
            }
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
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
    except Exception as e:
        # Fallback to cached state or report offline check
        if _update_state.get("checked"):
            return {
                "available": _update_state.get("available", False),
                "status_text": "YES" if _update_state.get("available", False) else "NO",
                "message": _update_state.get("message", "Up to date"),
                "latest_version": _update_state.get("latest_version"),
            }
        message = "Could not check remote version"

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
    """Trigger update process for host components via Watchtower API or host script."""
    # 1. Check for Watchtower HTTP API
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

    # 2. Check for host update script
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

    # 3. Check for trigger file mechanism
    trigger_dir = "/host/trigger"
    if os.path.exists(trigger_dir) and os.path.isdir(trigger_dir):
        try:
            trigger_file = os.path.join(trigger_dir, "update")
            with open(trigger_file, "w") as f:
                f.write(STATUS_VERSION)
            return {
                "success": True,
                "message": "Host update trigger written to trigger file.",
            }
        except Exception as e:
            return {"success": False, "message": f"Could not write trigger: {str(e)}"}

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
        "versions": versions,
        "updates": update_info,
    }
