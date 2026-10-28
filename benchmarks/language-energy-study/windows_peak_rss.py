#!/usr/bin/env python3
"""Точний піковий working set одного Windows PID; незалежний механізм RSS.

Не є семантичним оракулом SENS, не є енергетичним вимірювачем.
На Windows PeakWorkingSetSize (bytes) включає максимум resident working
set від створення процесу. Це НЕ тотожно Linux ru_maxrss, GPU, system RSS
або енергії; при помилці повернення нуля заборонене.
"""
import os


def peak_working_set_kib(pid: int) -> int:
    """Return Windows process PeakWorkingSetSize in KiB; fail closed."""
    if isinstance(pid, bool) or not isinstance(pid, int) or not 0 < pid < 2**32:
        raise ValueError("valid positive Windows DWORD pid required")
    if os.name != "nt":
        raise RuntimeError("WINDOWS_ONLY: no portable Linux/macOS surrogate")

    import ctypes
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
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

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    # PSAPI v1: PROCESS_QUERY_INFORMATION + PROCESS_VM_READ.
    handle = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), ctypes.sizeof(counters)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        peak = int(counters.PeakWorkingSetSize)
        if peak <= 0:
            raise RuntimeError("INVALID_WINDOWS_PEAK_WORKING_SET")
        return (peak + 1023) // 1024
    finally:
        if not kernel32.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())
