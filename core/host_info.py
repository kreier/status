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


def check_updates() -> Dict[str, Any]:
    """Check for available updates."""
    # Check if forced via env var
    env_update = os.environ.get("UPDATES_AVAILABLE")
    if env_update is not None:
        avail = env_update.strip().lower() in ("true", "1", "yes", "y")
    else:
        avail = _update_state.get("available", True)

    _update_state["checked"] = True
    _update_state["available"] = avail

    return {
        "available": avail,
        "status_text": "YES" if avail else "NO",
        "message": "Updates available" if avail else "All components up to date",
    }


def trigger_update() -> Dict[str, Any]:
    """Trigger update process for host components."""
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
        "message": "Update triggered successfully (mock updater).",
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
