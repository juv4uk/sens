"""Normalize one child process's OS peak resident set into KiB.

Linux wait4 rusage.ru_maxrss is in KiB; Darwin reports *bytes*.
Do not accept unknown OS units or pretend Windows has Unix os.wait4.
"""

import math


class InvalidPeakRSS(ValueError):
    """The physical peak RSS cannot be faithfully reported in KiB."""


def normalize_peak_rss_kib(raw, os_name):
    """Return positive per-child peak RSS in KiB; reject ambiguous data."""
    if os_name not in ("Linux", "Darwin"):
        raise InvalidPeakRSS(f"unsupported peak RSS unit on {os_name!r}")
    if type(raw) not in (int, float) or not math.isfinite(raw) or raw <= 0:
        raise InvalidPeakRSS("peak RSS must be a positive finite OS counter")
    kib = float(raw) / 1024.0 if os_name == "Darwin" else float(raw)
    if not math.isfinite(kib) or kib <= 0:
        raise InvalidPeakRSS("normalized peak RSS must be positive and finite")
    return kib
