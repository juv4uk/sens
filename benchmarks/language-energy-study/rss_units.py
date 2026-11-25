"""Normalize one child process's OS peak resident set into KiB.

Linux wait4 rusage.ru_maxrss is in KiB; Darwin reports bytes.
Unknown platforms and invalid physical counters must not enter paired data.
"""
import math


class InvalidPeakRSS(ValueError):
    """The physical peak RSS cannot be faithfully reported in KiB."""


def normalize_peak_rss_kib(raw, os_name):
    """Return positive per-child peak RSS in KiB; reject ambiguous data."""
    if os_name not in ("Linux", "Darwin"):
        raise InvalidPeakRSS(f"unsupported peak RSS unit on {os_name!r}")
    if type(raw) not in (int, float):
        raise InvalidPeakRSS("peak RSS must be a positive finite OS counter")
    try:
        value = float(raw)
    except (OverflowError, ValueError) as exc:
        raise InvalidPeakRSS("peak RSS is outside the supported numeric range") from exc
    if not math.isfinite(value) or value <= 0:
        raise InvalidPeakRSS("peak RSS must be a positive finite OS counter")
    kib = value / 1024.0 if os_name == "Darwin" else value
    if not math.isfinite(kib) or kib <= 0:
        raise InvalidPeakRSS("normalized peak RSS must be positive and finite")
    return kib
