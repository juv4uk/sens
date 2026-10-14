#!/usr/bin/env python3
"""Physical Zig 0.16 T5 cross-check for migration; never a SENS semantic oracle.

The canonical SENS three-pass migrator still determines the exact typed words.
This helper only independently validates and replays the generated physical T5
bytes for declared D1..D10 coordinates (not executable program admission).
It fails closed on missing/wrong Zig or any byte difference.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / ".zig-version"
SOURCE = "research/zig-codecs/transport.zig"


class ZigCodecError(ValueError):
    pass


def _command(argv: list[str]) -> None:
    try:
        completed = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ZigCodecError(f"ZIG_CODEC_UNAVAILABLE command={argv[:2]!r}: {error}") from error
    if completed.returncode:
        raise ZigCodecError(
            f"ZIG_CODEC_FAILURE exit={completed.returncode} command={argv[:2]!r} "
            f"stderr={completed.stderr[-1200:]}"
        )


def pinned_compiler() -> str:
    expected = PIN_FILE.read_text(encoding="utf-8").strip()
    if expected != "0.16.0":
        raise ZigCodecError(f"ZIG_CODEC_PIN_DRIFT expected=0.16.0 actual={expected!r}")
    compiler = os.environ.get("ZIG", "zig")
    try:
        probe = subprocess.run([compiler, "version"], cwd=ROOT,
                               capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ZigCodecError(f"ZIG_CODEC_UNAVAILABLE: {error}") from error
    actual = probe.stdout.strip()
    if probe.returncode != 0 or actual != expected:
        raise ZigCodecError(f"ZIG_CODEC_VERSION expected={expected} actual={actual!r} "
                            f"stderr={probe.stderr[-300:]!r}")
    return compiler


def build_transport(directory: Path) -> Path:
    compiler = pinned_compiler()
    directory.mkdir(parents=True, exist_ok=True)
    binary = directory / "sens-zig-transport"
    if binary.exists() or binary.is_symlink():
        raise ZigCodecError("ZIG_CODEC_OUTPUT_EXISTS: refusing overwrite")
    _command([compiler, "build-exe", SOURCE, "-O", "ReleaseFast", "-lc",
              f"-femit-bin={binary}"])
    if not binary.is_file():
        raise ZigCodecError("ZIG_CODEC_MISSING_BUILT_BINARY")
    return binary


def verify_t5(binary: Path, physical: bytes) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="sens-zig-t5-verify-") as directory:
        source = Path(directory) / "input.sens"
        restored = Path(directory) / "roundtrip.sens"
        source.write_bytes(physical)
        # D10 is valid transport but intentionally rejected by runnable D1..D9.
        # The migration verifier must use the explicit coordinate-only profile.
        _command([str(binary), "t5-coordinates-check", str(source)])
        _command([str(binary), "t5-coordinates-roundtrip", str(source), str(restored)])
        replay = restored.read_bytes()
        if replay != physical:
            a = hashlib.sha256(physical).hexdigest()
            b = hashlib.sha256(replay).hexdigest()
            offset = next((i for i, (x, y) in enumerate(zip(physical, replay)) if x != y),
                          min(len(physical), len(replay)))
            raise ZigCodecError(
                f"ZIG_CODEC_PHYSICAL_MISMATCH layer=transport input_sha256={a} "
                f"actual_sha256={b} first_byte={offset} "
                f"input_len={len(physical)} actual_len={len(replay)}"
            )
    return {"zig_version": "0.16.0", "codec": "T5",
            "profile": "D1-D10_COORDINATES_NOT_EXECUTION",
            "physical_sha256": hashlib.sha256(physical).hexdigest(),
            "verdict": "PHYSICAL_BYTES_IDENTICAL_ONLY"}
