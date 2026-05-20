#!/usr/bin/env python3
"""
Safe Windows subprocess helpers for paths that may contain spaces.

Use argv lists with shell=False. When embedding paths in JVM flags or legacy
cmd strings, use java_system_property() so values stay quoted.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

__all__ = [
    "build_cmd_exe_c",
    "build_run_one_flow_on_device_argv",
    "build_subprocess_args",
    "execute_command",
    "java_system_property",
    "log_subprocess_launch",
    "popen_command",
    "quote_windows_cmd_token",
    "safe_windows_path",
]


def safe_windows_path(path: str | Path) -> str:
    """Resolve to an absolute path string safe for subprocess argv on Windows."""
    return str(Path(path).resolve())


def quote_windows_cmd_token(token: str) -> str:
    """Quote a token when it must be embedded in a cmd.exe command-line string."""
    if token == "":
        return '""'
    if all(c not in ' \t"' for c in token):
        return token
    return '"' + token.replace('"', r'\"') + '"'


def java_system_property(key: str, value: str | Path) -> str:
    """JVM -D flag with quoted value (safe when expanded by cmd.exe batch files)."""
    v = str(value).replace('"', r'\"')
    return f'-D{key}="{v}"'


def build_subprocess_args(executable: str | Path, *args: str | Path) -> list[str]:
    out: list[str] = [str(executable)]
    for a in args:
        if isinstance(a, Path):
            out.append(safe_windows_path(a))
        elif isinstance(a, str) and Path(a).exists():
            out.append(safe_windows_path(a))
        else:
            out.append(str(a))
    return out


def _resolve_cmd_token(token: str | Path) -> str:
    if isinstance(token, Path):
        return safe_windows_path(token)
    p = Path(token)
    if p.exists():
        return safe_windows_path(p)
    return str(token)


def build_cmd_exe_c(command: str | Path, *args: str | Path) -> list[str]:
    """Build argv for ``cmd.exe /d /c <command> <args...>`` with shell=False."""
    return ["cmd.exe", "/d", "/c", _resolve_cmd_token(command), *[_resolve_cmd_token(a) for a in args]]


def build_run_one_flow_on_device_argv(
    bat: str | Path,
    *,
    suite_id: str,
    flow_path: str | Path,
    device_id: str,
    app_id: str,
    clear_state: str,
    maestro_launcher: str | Path,
    include_tag: str = "__EMPTY__",
) -> list[str]:
    """Argv for blocking ``scripts/run_one_flow_on_device.bat`` (one cmd.exe child)."""
    return build_cmd_exe_c(
        bat,
        suite_id,
        flow_path,
        device_id,
        app_id,
        clear_state,
        maestro_launcher,
        include_tag,
    )


def log_subprocess_launch(
    cmd: Sequence[str],
    *,
    cwd: str | Path | None = None,
    shell: bool = False,
    prefix: str = "[ATP]",
) -> None:
    print(f"{prefix} subprocess_safe_args={list(cmd)!r}", flush=True)
    print(f"{prefix} subprocess_shell={shell}", flush=True)
    if cwd:
        print(f'{prefix} cwd="{safe_windows_path(cwd)}"', flush=True)
    else:
        print(f"{prefix} cwd=", flush=True)


def execute_command(
    cmd: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    shell: bool = False,
    timeout: float | None = None,
    check: bool = False,
    capture_output: bool = False,
    prefix: str = "[ATP]",
    **kwargs: Any,
) -> subprocess.CompletedProcess[Any]:
    log_subprocess_launch(cmd, cwd=cwd, shell=shell, prefix=prefix)
    run_kw: dict[str, Any] = {"shell": shell, "check": check, **kwargs}
    if cwd is not None:
        run_kw["cwd"] = safe_windows_path(cwd)
    if env is not None:
        run_kw["env"] = dict(env)
    if capture_output:
        run_kw["capture_output"] = True
        run_kw["text"] = True
    if timeout is not None:
        run_kw["timeout"] = timeout
    return subprocess.run(list(cmd), **run_kw)


def popen_command(
    cmd: Sequence[str],
    *,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    shell: bool = False,
    prefix: str = "[ATP]",
    **kwargs: Any,
) -> subprocess.Popen[Any]:
    log_subprocess_launch(cmd, cwd=cwd, shell=shell, prefix=prefix)
    popen_kw: dict[str, Any] = {"shell": shell, **kwargs}
    if cwd is not None:
        popen_kw["cwd"] = safe_windows_path(cwd)
    if env is not None:
        popen_kw["env"] = dict(env)
    return subprocess.Popen(list(cmd), **popen_kw)
