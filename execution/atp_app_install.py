#!/usr/bin/env python3
"""
HP 500 ATP — adb ``pm path`` app install checks (preflight + fast-fail helpers).
"""
from __future__ import annotations

import re
import subprocess
from typing import Sequence

ATP_EXIT_APP_NOT_INSTALLED = 23
SKIPPED_APP_NOT_INSTALLED = "SKIPPED_APP_NOT_INSTALLED"
LOG_MARKER_APP_NOT_INSTALLED = "APP_NOT_INSTALLED_ON_DEVICE"


def _adb_pm_path(device_id: str, app_id: str, *, timeout_sec: float = 8.0) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["adb", "-s", device_id, "shell", "pm", "path", app_id],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


def is_app_installed(device_id: str, app_id: str) -> bool:
    """True when ``adb shell pm path`` returns a ``package:`` line."""
    _code, text = _adb_pm_path(device_id, app_id)
    if not text:
        return False
    return bool(re.search(r"(?m)^package:", text)) or "package:" in text


def log_app_install_check(device_id: str, app_id: str, installed: bool) -> None:
    flag = "true" if installed else "false"
    print(
        f"[ATP] app_install_check device={device_id} app={app_id} installed={flag}",
        flush=True,
    )


def preflight_app_install_matrix(
    devices: Sequence[str], app_id: str
) -> tuple[list[str], list[str], dict[str, bool]]:
    """
    Check every device before scheduling.

    Returns (active_devices, skipped_devices, matrix).
    """
    matrix: dict[str, bool] = {}
    active: list[str] = []
    skipped: list[str] = []
    for dev in devices:
        ok = is_app_installed(dev, app_id)
        matrix[dev] = ok
        log_app_install_check(dev, app_id, ok)
        print(f"device={dev} installed={'true' if ok else 'false'}", flush=True)
        if ok:
            active.append(dev)
        else:
            skipped.append(dev)
    if skipped:
        print(
            f"[ATP] preflight_app_install skipped_devices="
            f"{', '.join(skipped)} app={app_id}",
            flush=True,
        )
    return active, skipped, matrix


def is_app_not_installed_exit(exit_code: int) -> bool:
    return exit_code == ATP_EXIT_APP_NOT_INSTALLED
