#!/usr/bin/env python3
"""
HP 500 Android — canonical Maestro / adb app package resolution.

Remaps legacy Kodak Smile defaults (com.kodaksmile) to HP Panorama for this repo only.
"""
from __future__ import annotations

import os

HP500_APP_PACKAGE = "com.hp.impulse.panorama"
LEGACY_KODAK_APP_PACKAGE = "com.kodaksmile"


def resolve_app_package(requested: str | None = None) -> str:
    """
    Resolve app package for ATP / Jenkins runs.

    Priority: explicit ``requested`` arg, then env APP_PACKAGE / ATP_APP_PACKAGE,
    then HP500 default. Legacy ``com.kodaksmile`` is always remapped to Panorama here.
    """
    env = (os.environ.get("APP_PACKAGE") or os.environ.get("ATP_APP_PACKAGE") or "").strip()
    raw = (requested or env or "").strip()
    if not raw or raw == LEGACY_KODAK_APP_PACKAGE:
        return HP500_APP_PACKAGE
    return raw


def log_resolved_app_package(resolved: str, *, prefix: str = "[ATP]", source: str = "") -> None:
    src = f" source={source!r}" if source else ""
    print(f"{prefix} resolved_app_id={resolved}{src}", flush=True)


if __name__ == "__main__":
    import sys

    print(resolve_app_package(sys.argv[1] if len(sys.argv) > 1 else None))
