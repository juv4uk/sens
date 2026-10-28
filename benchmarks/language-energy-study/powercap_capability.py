#!/usr/bin/env python3
"""Read-only Linux powercap *capability* diagnosis for SENS energy research.

THIS IS NOT A RAPL COLLECTOR. A one-time counter read can establish that the
file is readable, not measure a joule delta, attribute a process, authenticate
physical hardware, calibrate a meter, or prove independent sessions.
The actual package energy collector belongs to #6275.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import re

SCHEMA = "sens-powercap-capability/v1"
ZONE = re.compile(r"(?:intel|amd)-rapl:[0-9]+", re.ASCII)
PACKAGE = re.compile(r"package-[0-9]+", re.ASCII)
UINT = re.compile(r"[0-9]+", re.ASCII)
STATUSES = {
    "LINUX_POWERCAP_NOT_APPLICABLE",
    "POWERCAP_SYSFS_MISSING",
    "POWERCAP_ROOT_UNREADABLE",
    "NO_PACKAGE_ZONE",
    "COUNTER_MISSING_OR_UNREADABLE",
    "COUNTER_READABLE_UNCALIBRATED",
    "MULTIPLE_PACKAGE_COUNTERS_UNCALIBRATED",
}


def _read_limited(path: Path) -> str | None:
    """Read a bounded amount of sysfs text. Never return raw sensor values."""
    try:
        with path.open("r", encoding="ascii") as f:
            value = f.read(65)
    except (OSError, UnicodeError):
        return None
    if len(value) > 64:
        return None
    return value.strip()


def _uint(value: str | None, *, positive: bool = False) -> bool:
    return (value is not None and UINT.fullmatch(value) is not None
            and (not positive or int(value) > 0))


def probe(
    root: Path = Path("/sys/class/powercap"),
    *,
    system_name: str | None = None,
) -> dict:
    """Return only observed accessibility, never inferred physical energy.

    root and system_name injection are for synthetic negative controls.
    A synthetic counter cannot demonstrate physical calibration.
    """
    os_name = system_name if system_name is not None else platform.system()
    candidate_names: list[str] = []
    readable_names: list[str] = []

    if os_name != "Linux":
        status = "LINUX_POWERCAP_NOT_APPLICABLE"
    elif not root.is_dir():
        status = "POWERCAP_SYSFS_MISSING"
    else:
        try:
            children = sorted(
                (child for child in root.iterdir()
                 if ZONE.fullmatch(child.name) is not None and child.is_dir()),
                key=lambda p: p.name,
            )
        except OSError:
            status = "POWERCAP_ROOT_UNREADABLE"
            children = None
        if children is not None:
            for child in children:
                label = _read_limited(child / "name")
                if label is None or PACKAGE.fullmatch(label) is None:
                    continue  # sub-zone, not whole-package energy
                candidate_names.append(child.name)
                # Read once only for accessibility/format. The value is NEVER
                # retained, subtracted, exposed or converted to joules.
                energy = _read_limited(child / "energy_uj")
                maximum = _read_limited(child / "max_energy_range_uj")
                if _uint(energy) and _uint(maximum, positive=True):
                    readable_names.append(child.name)

            if not candidate_names:
                status = "NO_PACKAGE_ZONE"
            elif not readable_names:
                status = "COUNTER_MISSING_OR_UNREADABLE"
            elif len(readable_names) == 1 and len(candidate_names) == 1:
                status = "COUNTER_READABLE_UNCALIBRATED"
            else:
                status = "MULTIPLE_PACKAGE_COUNTERS_UNCALIBRATED"

    assert status in STATUSES
    # "readable" does NOT imply meter calibration or hardware identity.
    return {
        "schema": SCHEMA,
        "os": os_name,
        "powercap_path": str(root),
        "status": status,
        "package_zone_candidates": candidate_names,
        "readable_package_counters": readable_names,
        "energy_status": "ENERGY_NOT_MEASURED",
        "energy_joules": None,
        "physical_calibration_verified": False,
        "scope": "CPU_PACKAGE_NOT_PROCESS",
        "notice": (
            "No time-bracketed counter delta, physical calibration, or "
            "process-level energy inference was performed."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/sys/class/powercap"))
    args = parser.parse_args(argv)
    print(json.dumps(probe(args.root), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
