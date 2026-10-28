#!/usr/bin/env python3
"""Windows-only, per-process wall/peak-working-set measurement for ENERGY-06.

This is *not* a SENS semantic oracle. A successful process still needs the
separate corpus-specific output parity gate in run_study.py. This uses Win32's
PeakWorkingSetSize, not POSIX ru_maxrss; results from different OSs must not be
treated as an identical physical memory metric.

No psutil, subprocess shell, energy/TDP approximation, or extra runner needed.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import math
import os
import subprocess
import time


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def peak_working_set_kib(process: subprocess.Popen) -> int:
    """Read the *specific child* peak working set, even after it exits.

    Popen owns the Win32 process HANDLE until the Popen object is destroyed.
    Never substitute a system-wide or cumulative child-process RSS counter.
    """
    if os.name != "nt":
        raise OSError("Win32 per-process memory counter is unavailable")
    handle = getattr(process, "_handle", None)
    if handle is None:
        raise OSError("no retained Windows process HANDLE")
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    getter = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
    getter.argtypes = (wintypes.HANDLE, ctypes.POINTER(_ProcessMemoryCounters),
                       wintypes.DWORD)
    getter.restype = wintypes.BOOL
    if not getter(wintypes.HANDLE(int(handle)), ctypes.byref(counters),
                  counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    bytes_peak = int(counters.PeakWorkingSetSize)
    if bytes_peak <= 0:
        raise OSError("Win32 returned no valid peak working set")
    return (bytes_peak + 1023) // 1024


def validate_sample(wall_ns: int, memory_kib: int, exit_code: int,
                    stdout: str, stderr: str):
    """Fail closed: only positive measured metrics, clean exit, one output."""
    if not isinstance(wall_ns, int) or wall_ns <= 0:
        return None, None, "BAD_WALL_TIME"
    if not isinstance(memory_kib, int) or memory_kib <= 0:
        return None, None, "BAD_WIN32_PEAK_WORKING_SET"
    if exit_code != 0:
        return None, None, f"EXIT_{exit_code}:{stderr.strip()[:80]}"
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        return None, None, f"BAD_STDOUT_LINES_{len(lines)}"
    return float(wall_ns), float(memory_kib), lines[0]


def run_once_windows(cmd: str, env: dict, timeout_s: float = 120.0):
    """Process-cold Windows sample; stdout parity is checked by caller.

    On Windows, Popen accepts an exact command line with shell=False, without
    POSIX shlex corrupting backslash-separated drive paths. communicate()
    drains pipes while waiting, avoiding the wait-before-read deadlock.
    """
    if os.name != "nt":
        return None, None, "WIN32_METER_UNAVAILABLE"
    if not isinstance(timeout_s, (int, float)) or not math.isfinite(timeout_s) or timeout_s <= 0:
        return None, None, "INVALID_TIMEOUT"
    started = time.perf_counter_ns()
    try:
        child = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True,
                                 shell=False, env=env)
    except OSError as exc:
        return None, None, f"SPAWN_FAIL:{exc}"
    try:
        try:
            stdout, stderr = child.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
            return None, None, f"TIMEOUT_{timeout_s}s"
        elapsed = time.perf_counter_ns() - started
        try:
            peak_kib = peak_working_set_kib(child)
        except (OSError, AttributeError, ValueError) as exc:
            return None, None, f"WIN32_MEMORY_UNAVAILABLE:{exc}"
        return validate_sample(elapsed, peak_kib, child.returncode,
                               stdout, stderr)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate()
