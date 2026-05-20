#!/usr/bin/env python3
"""
Map legacy Kodak Smile Jenkins ATP folder names to HP500 ``ATP TestCase Flows`` children.

Jenkins stages still pass Kodak names (e.g. SignUp_Login); on disk HP500 uses signup-login.
Suite ids (atp_signup_login) are unchanged — both names normalize to the same id.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Jenkins / docs / manual CLI name -> folder under ``ATP TestCase Flows``
LEGACY_FOLDER_ALIASES: dict[str, str] = {
    "SignUp_Login": "signup-login",
    "SignUp-Login": "signup-login",
    "signup_login": "signup-login",
    "Connection": "connection",
    "Onboarding": "onboarding",
}


def _alias_lookup(requested: str) -> str | None:
    key = requested.strip()
    if not key:
        return None
    direct = LEGACY_FOLDER_ALIASES.get(key)
    if direct:
        return direct
    lower = key.lower()
    for legacy, mapped in LEGACY_FOLDER_ALIASES.items():
        if legacy.lower() == lower:
            return mapped
    return None


def resolve_atp_subfolder(requested: str, repo_root: Path | None = None) -> str:
    """
    Return the ATP child folder name to use on disk.

    - Empty input -> "" (run all folders).
    - Exact or case-insensitive match on disk -> that folder name.
    - Known legacy alias -> mapped name (even if folder missing; orchestrator will SKIP).
    - Otherwise -> trimmed input unchanged.
    """
    raw = (requested or "").strip()
    if not raw:
        return ""
    root = (repo_root or REPO).resolve()
    atp_root = root / "ATP TestCase Flows"
    if not atp_root.is_dir():
        return raw

    for entry in atp_root.iterdir():
        if entry.is_dir() and entry.name.lower() == raw.lower():
            return entry.name

    mapped = _alias_lookup(raw)
    if mapped and (atp_root / mapped).is_dir():
        return mapped
    if mapped:
        return mapped

    return raw


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: atp_folder_resolve.py <FOLDER_OR_EMPTY> [REPO_ROOT]", file=sys.stderr)
        return 2
    repo = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else REPO
    print(resolve_atp_subfolder(sys.argv[1], repo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
