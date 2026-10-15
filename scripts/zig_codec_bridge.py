#!/usr/bin/env python3
"""Zig 0.16 physical carrier and attested migration bridge.

SENS three-pass migration determines exact bit words and the boundaries.
Zig alone emits physical bytes; Python reference packing is parity-only.
Neither this module nor Zig grants semantic callability.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import stat
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN_FILE = ROOT / ".zig-version"
SOURCE = "research/zig-codecs/transport.zig"

# A byte-level migration receipt may only come from the executable built by
# this Python process with the repo-pinned Zig compiler, not an arbitrary stub.
# Attestation covers provenance within this process, not compiler authenticity.
_BUILT_TRANSPORT_DIGESTS: dict[Path, str] = {}


def _binary_sha256(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            return digest.hexdigest()
    except OSError as error:
        raise ZigCodecError(f"ZIG_CODEC_BINARY_UNREADABLE: {error}") from error


def _reject_linked_path_components(path: Path) -> None:
    """Bind the Zig executable to an unaliased physical pathname.

    A symlink parent can resolve to the *same* SHA-attested binary while
    disguising its physical location. Do this before invoking Zig and
    before accepting its output. This is provenance, not SENS semantics.
    """
    if ".." in path.parts:
        raise ZigCodecError(f"ZIG_CODEC_BINARY_NONCANONICAL_PATH path={path}")
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ZigCodecError(
                f"ZIG_CODEC_BINARY_NOT_REGULAR linked_component={current}"
            )


def _built_executable_digest(binary: Path) -> str:
    # The SHA is necessary but NOT sufficient if a parent aliases the file.
    _reject_linked_path_components(binary)
    if binary.is_symlink() or not binary.is_file():
        raise ZigCodecError("ZIG_CODEC_BINARY_NOT_REGULAR")
    try:
        canonical = binary.resolve(strict=True)
    except OSError as error:
        raise ZigCodecError(f"ZIG_CODEC_BINARY_UNREADABLE: {error}") from error
    expected = _BUILT_TRANSPORT_DIGESTS.get(canonical)
    if expected is None:
        raise ZigCodecError("ZIG_CODEC_UNATTESTED_BINARY: build with build_transport first")
    actual = _binary_sha256(binary)
    if actual != expected:
        raise ZigCodecError(
            f"ZIG_CODEC_BINARY_CHANGED expected_sha256={expected} actual_sha256={actual}"
        )
    return actual


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
    binary = directory / "sens-zig-transport"
    # Refuse a redirected output location before probing the compiler or
    # executing any build command, including if the binary does not exist.
    _reject_linked_path_components(binary)
    compiler = pinned_compiler()
    directory.mkdir(parents=True, exist_ok=True)
    if binary.exists() or binary.is_symlink():
        raise ZigCodecError("ZIG_CODEC_OUTPUT_EXISTS: refusing overwrite")
    _command([compiler, "build-exe", SOURCE, "-O", "ReleaseFast", "-lc",
              f"-femit-bin={binary}"])
    _reject_linked_path_components(binary)
    if binary.is_symlink() or not binary.is_file():
        raise ZigCodecError("ZIG_CODEC_MISSING_BUILT_BINARY")
    _BUILT_TRANSPORT_DIGESTS[binary.resolve(strict=True)] = _binary_sha256(binary)
    return binary


def _require_external_source_sha256(
    physical: bytes, trusted_source_sha256: str | None
) -> None:
    # A caller-trusted digest must originate OUTSIDE the bytes being checked.
    # T5 can roundtrip a truncated D10 zero as a DIFFERENT canonical D5 zero.
    if trusted_source_sha256 is None:
        return
    if (not isinstance(trusted_source_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", trusted_source_sha256) is None):
        raise ZigCodecError(
            "ZIG_CODEC_EXTERNAL_SOURCE_SHA_INVALID layer=transport "
            "expected=64_lowercase_hex"
        )
    actual = hashlib.sha256(physical).hexdigest()
    if not hmac.compare_digest(actual, trusted_source_sha256):
        raise ZigCodecError(
            "ZIG_CODEC_EXTERNAL_SOURCE_SHA_MISMATCH layer=transport "
            f"expected_sha256={trusted_source_sha256} actual_sha256={actual} "
            f"actual_bytes={len(physical)}"
        )



def _read_zig_output(path: Path, *, command: str) -> bytes:
    """Read only this Zig subprocess's regular output; no symlink receipts.

    The temporary path belongs to this operation. The inode before/opened/
    after checks protect against a path being rebound during physical readback.
    This is file provenance, never a semantic SENS verdict.
    """
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise ZigCodecError(
                f"ZIG_CODEC_OUTPUT_NOT_REGULAR layer=transport command={command}"
            )
        if before.st_nlink != 1:
            raise ZigCodecError(
                f"ZIG_CODEC_OUTPUT_LINKED layer=transport command={command} "
                f"nlink={before.st_nlink}"
            )
        with path.open("rb") as stream:
            physical = stream.read()
            opened = os.fstat(stream.fileno())
        after = path.lstat()
    except OSError as error:
        raise ZigCodecError(
            f"ZIG_CODEC_OUTPUT_UNREADABLE layer=transport command={command}: {error}"
        ) from error
    inode = (before.st_dev, before.st_ino)
    if (not stat.S_ISREG(after.st_mode)
            or opened.st_nlink != 1 or after.st_nlink != 1
            or (opened.st_dev, opened.st_ino) != inode
            or (after.st_dev, after.st_ino) != inode):
        raise ZigCodecError(
            f"ZIG_CODEC_OUTPUT_CHANGED layer=transport command={command}"
        )
    return physical


def carry_t5(
    binary: Path, canonical_view: str, *,
    trusted_source_sha256: str | None = None,
) -> bytes:
    """Zig mints T5 from upstream words; no Python physical writer.

    Word separators are replaced with trit 2 for mechanical carrying only.
    Every execution uses the exact pinned, SHA-attested Zig binary.
    """
    valid_view_pattern = r"[01]+(?: [01]+)*" + chr(10)
    if (not isinstance(canonical_view, str) or
            re.fullmatch(valid_view_pattern, canonical_view) is None):
        raise ZigCodecError("ZIG_CARRY_NONCANONICAL_VIEW layer=transport")
    binary_digest = _built_executable_digest(binary)
    raw_trits = canonical_view[:-1].replace(" ", "2").encode("ascii")
    with tempfile.TemporaryDirectory(prefix="sens-zig-t5-carry-") as directory:
        source = Path(directory) / "source.trits"
        output = Path(directory) / "out.sens"
        source.write_bytes(raw_trits)
        _command([str(binary), "t5-carry", str(source), str(output)])
        physical = _read_zig_output(output, command="t5-carry")
    _require_external_source_sha256(physical, trusted_source_sha256)
    if _built_executable_digest(binary) != binary_digest:
        raise ZigCodecError("ZIG_CODEC_BINARY_CHANGED_DURING_CARRY")
    return physical

def verify_t5(
    binary: Path, physical: bytes, *, trusted_source_sha256: str | None = None
) -> dict[str, str]:
    # Fail BEFORE observing/build attestation or executing Zig; the pin is
    # externally supplied, not inferred from this candidate physical input.
    _require_external_source_sha256(physical, trusted_source_sha256)
    binary_digest = _built_executable_digest(binary)
    with tempfile.TemporaryDirectory(prefix="sens-zig-t5-verify-") as directory:
        source = Path(directory) / "input.sens"
        restored = Path(directory) / "roundtrip.sens"
        source.write_bytes(physical)
        # D10 is valid transport but intentionally rejected by runnable D1..D9.
        # The migration verifier must use the explicit coordinate-only profile.
        _command([str(binary), "t5-coordinates-check", str(source)])
        _command([str(binary), "t5-coordinates-roundtrip", str(source), str(restored)])
        replay = _read_zig_output(restored, command="t5-coordinates-roundtrip")
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
    # Detect a changed executable after the two checks as well. This cannot
    # replace a trusted Zig toolchain installation, but prevents stale or
    # substituted binaries from claiming this session's Zig build receipt.
    if _built_executable_digest(binary) != binary_digest:
        raise ZigCodecError("ZIG_CODEC_BINARY_CHANGED_DURING_VERIFY")
    return {"zig_version": "0.16.0", "codec": "T5",
            "profile": "D1-D10_COORDINATES_NOT_EXECUTION",
            "physical_sha256": hashlib.sha256(physical).hexdigest(),
            "zig_binary_sha256": binary_digest,
            "source_pin_status": (
                "MATCHED_CALLER_SUPPLIED_SHA256"
                if trusted_source_sha256 is not None else "NOT_SUPPLIED"
            ),
            "verdict": "PHYSICAL_BYTES_IDENTICAL_ONLY"}
