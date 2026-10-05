#!/usr/bin/env python3
"""Shared per-process peak-RSS primitive for Reality Matrix (#3698).

Linux first. Each measurement is delegated to a fresh GNU /usr/bin/time process
so peak RSS is not contaminated by Python's cumulative RUSAGE_CHILDREN state.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

GNU_TIME = Path("/usr/bin/time")
METHOD = "gnu-time-per-process-v1"


def measure_peak_rss_kb(command: list[str]) -> tuple[str, str, int]:
    if not GNU_TIME.is_file():
        raise RuntimeError("/usr/bin/time is required for Linux RSS evidence")
    if not command:
        raise ValueError("command must be non-empty")

    with tempfile.NamedTemporaryFile(prefix="sens-rss-", delete=False) as handle:
        metric_path = Path(handle.name)

    try:
        proc = subprocess.run(
            [
                str(GNU_TIME),
                "-q",
                "-f",
                "%M",
                "-o",
                str(metric_path),
                "--",
                *command,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        metric_text = metric_path.read_text(encoding="utf-8").strip()
        if proc.returncode != 0:
            raise RuntimeError(
                f"measured command failed ({proc.returncode}): {command!r}\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )
        try:
            peak_kb = int(metric_text)
        except ValueError as exc:
            raise RuntimeError(f"GNU time returned invalid RSS metric: {metric_text!r}") from exc
        if peak_kb <= 0:
            raise RuntimeError(f"GNU time returned non-positive RSS metric: {peak_kb}")
        return proc.stdout, proc.stderr, peak_kb
    finally:
        try:
            metric_path.unlink()
        except FileNotFoundError:
            pass


def probe_command(mib: int) -> list[str]:
    code = (
        "import sys;"
        f"n={mib}*1024*1024;"
        "b=bytearray(n);"
        "[b.__setitem__(i, (i//4096)&255) for i in range(0,n,4096)];"
        "print(len(b))"
    )
    return [sys.executable, "-c", code]


def self_test() -> None:
    # Two orders are mandatory: this specifically falsifies cumulative-child-max bugs.
    low_mib = 8
    high_mib = 96

    _, _, low_first = measure_peak_rss_kb(probe_command(low_mib))
    _, _, high_second = measure_peak_rss_kb(probe_command(high_mib))
    _, _, high_first = measure_peak_rss_kb(probe_command(high_mib))
    _, _, low_second = measure_peak_rss_kb(probe_command(low_mib))

    minimum_gap_kb = 48 * 1024
    for label, low, high in (
        ("low->high", low_first, high_second),
        ("high->low", low_second, high_first),
    ):
        if high - low < minimum_gap_kb:
            raise RuntimeError(
                f"{label}: RSS ordering/gap failed: low={low} KiB high={high} KiB"
            )

    # A cumulative RUSAGE_CHILDREN bug would make the second low measurement
    # approximately equal to the prior high peak. Require both low probes to remain low.
    low_ceiling_kb = 40 * 1024
    if low_first >= low_ceiling_kb or low_second >= low_ceiling_kb:
        raise RuntimeError(
            "low-memory probe retained a prior high peak: "
            f"low_first={low_first} KiB low_second={low_second} KiB"
        )

    print(
        "RSS_SELF_TEST\tPASS"
        f"\tlow_first_kb={low_first}"
        f"\thigh_second_kb={high_second}"
        f"\thigh_first_kb={high_first}"
        f"\tlow_second_kb={low_second}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("provide --self-test or a command after --")

    stdout, stderr, peak_kb = measure_peak_rss_kb(command)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    print(f"PEAK_RSS_KB={peak_kb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
