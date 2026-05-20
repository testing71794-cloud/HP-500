"""Shared utilities (device names, path helpers)."""

from .device_utils import get_device_display_name, get_device_name, render_device_display
from .git_branch import detect_git_branch, write_git_branch_file
from .subprocess_windows import (
    build_cmd_exe_c,
    build_run_one_flow_on_device_argv,
    execute_command,
    java_system_property,
    popen_command,
    safe_windows_path,
)

__all__ = [
    "build_cmd_exe_c",
    "build_run_one_flow_on_device_argv",
    "detect_git_branch",
    "execute_command",
    "get_device_display_name",
    "get_device_name",
    "java_system_property",
    "popen_command",
    "render_device_display",
    "safe_windows_path",
    "write_git_branch_file",
]
