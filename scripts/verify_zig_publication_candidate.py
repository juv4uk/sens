#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: verify a SENS physical publication *candidate*.

Outside the Zig corridor by design. Verifies pinned origin, real Zig byte
replay, and a real pinned SENS executor producing an expected output digest.
Never rewrites files, publishes, or decides SENS meaning. The attestation
file is an externally approved trust root: hashes alone cannot prove origin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SCHEMA = "sens-zig-publication-candidate/v1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_SIZE = 4 * 1024 * 1024
MAX_EXECUTABLE_SIZE = 256 * 1024 * 1024


class Rejected(ValueError):
    """Explicit fail-closed transport, provenance, or witnessed-result error."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_fixed(path: Path, *, max_size: int = MAX_SIZE) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise Rejected(f"untrusted/missing regular file: {path}")
    size = path.stat().st_size
    if not 0 < size <= max_size:
        raise Rejected(f"empty/oversize file: {path}")
    return path.read_bytes()


def pinned(name: str, actual: str, expected: object) -> None:
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        raise Rejected(f"{name}: expected an exact lowercase SHA-256")
    if actual != expected:
        raise Rejected(f"{name}: digest mismatch expected={expected} actual={actual}")


def run_checked(command: list[str], *, runner, timeout: int = 30):
    try:
        result = runner(command, capture_output=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Rejected(f"executor unavailable/timeout: {type(exc).__name__}") from exc
    if result.returncode != 0:
        raise Rejected(
            f"executor rejected (exit={result.returncode}, "
            f"stderr_sha256={digest(result.stderr)})"
        )
    return result


def verify(candidate: Path, source: Path, receipt_path: Path,
           zig_bin: Path, sens_bin: Path, *, runner=subprocess.run) -> dict:
    if candidate.suffix != ".sens":
        raise Rejected("candidate must be physical .sens")
    original = read_fixed(candidate)
    initial_source = read_fixed(source)
    zig_binary = read_fixed(zig_bin, max_size=MAX_EXECUTABLE_SIZE)
    sens_binary = read_fixed(sens_bin, max_size=MAX_EXECUTABLE_SIZE)
    receipt_bytes = read_fixed(receipt_path)
    try:
        receipt = json.loads(receipt_bytes)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise Rejected("malformed admission receipt") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise Rejected("wrong publication candidate schema")
    if receipt.get("source_era") not in ("current", "translated"):
        raise Rejected("source era must be explicit, never auto or inferred")
    pinned("source", digest(initial_source), receipt.get("source_sha256"))
    pinned("physical", digest(original), receipt.get("physical_sha256"))
    pinned("zig_executor", digest(zig_binary), receipt.get("zig_executor_sha256"))
    pinned("sens_executor", digest(sens_binary), receipt.get("sens_executor_sha256"))
    pinned(
        "expected_native_verdict",
        receipt.get("expected_native_stdout_sha256", ""),
        receipt.get("expected_native_stdout_sha256"),
    )
    translation_snapshot = None
    translation_path = None
    if receipt["source_era"] == "translated":
        # Translation happened OUTSIDE Zig. This is a content-binding check,
        # not an authentication signature or approval of that translation.
        item = receipt.get("translation_receipt")
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise Rejected("translated source requires separate provenance receipt")
        translation = Path(item["path"])
        if not translation.is_absolute() or translation == candidate:
            raise Rejected("translation receipt requires distinct absolute path")
        translation_path = translation
        translation_snapshot = read_fixed(translation)
        pinned("translation_receipt", digest(translation_snapshot), item.get("sha256"))
    elif "translation_receipt" in receipt:
        raise Rejected("current-era source must not carry translation evidence")
    # Never interpret validity from Zig's physical success alone.
    backend = run_checked([str(sens_bin), "backend"], runner=runner)
    if (b"transport=zig" not in backend.stdout
            or b"semantic_authority=SENS" not in backend.stdout):
        raise Rejected("SENS executable has no evidenced Zig mechanical backend")
    with tempfile.TemporaryDirectory(prefix="sens-pub-preflight-") as temp:
        replay_path = Path(temp) / "replay.sens"
        run_checked([str(zig_bin), "t5-roundtrip", str(candidate), str(replay_path)],
                    runner=runner)
        if not replay_path.is_file() or replay_path.is_symlink():
            raise Rejected("Zig did not produce the exact physical replay")
        replay = replay_path.read_bytes()
        if replay != original:
            raise Rejected(
                f"Zig byte replay mismatch original_sha={digest(original)} "
                f"replay_sha={digest(replay)}"
            )
    native = run_checked([str(sens_bin), "eval", str(candidate)], runner=runner)
    pinned("native_SENS_verdict", digest(native.stdout),
           receipt["expected_native_stdout_sha256"])
    # Reject concurrent substitution between initial admission and verdict.
    if read_fixed(source) != initial_source or read_fixed(candidate) != original:
        raise Rejected("source/candidate mutated during admission")
    if read_fixed(receipt_path) != receipt_bytes:
        raise Rejected("admission receipt mutated during verification")
    if (translation_path is not None
            and read_fixed(translation_path) != translation_snapshot):
        raise Rejected("translation provenance mutated during verification")
    if (read_fixed(zig_bin, max_size=MAX_EXECUTABLE_SIZE) != zig_binary
            or read_fixed(sens_bin, max_size=MAX_EXECUTABLE_SIZE) != sens_binary):
        raise Rejected("executor changed during admission")
    return {
        "status": "CANDIDATE_VERIFIED_NOT_PUBLISHED",
        "source_era": receipt["source_era"],
        "physical_sha256": digest(original),
        "native_stdout_sha256": digest(native.stdout),
        "semantic_authority": "SENS_EXECUTED_NOT_RATIFIED_BY_THIS_SCRIPT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for opt in ("candidate", "source", "receipt", "zig", "sens"):
        parser.add_argument("--" + opt, type=Path, required=True)
    args = parser.parse_args()
    try:
        record = verify(args.candidate, args.source, args.receipt, args.zig, args.sens)
    except Rejected as exc:
        print(f"ZIG_PUBLICATION_CANDIDATE_RED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
