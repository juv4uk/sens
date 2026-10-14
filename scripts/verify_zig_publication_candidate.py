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
TRANSLATION_SCHEMA = "sens-zig-translation-provenance/v1"
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
           zig_bin: Path, sens_bin: Path, *, runner=subprocess.run,
           trusted_translation_sha256: str | None = None) -> dict:
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
    origin_snapshot = None
    origin_path = None
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
        # A hash provided by the SAME candidate manifest cannot authenticate
        # an era. Require a second, independently supplied trust pin.
        if trusted_translation_sha256 is None:
            raise Rejected("translated source requires independent provenance pin")
        pinned("independent_translation_pin",
               digest(translation_snapshot), trusted_translation_sha256)
        try:
            evidence = json.loads(translation_snapshot)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise Rejected("invalid translation provenance document") from exc
        if not isinstance(evidence, dict) or evidence.get("schema") != TRANSLATION_SCHEMA:
            raise Rejected("translation provenance schema mismatch")
        if evidence.get("origin_era") != "historical":
            raise Rejected("translation origin era must be explicit")
        pinned("post_translation_source", digest(initial_source),
               evidence.get("post_translation_source_sha256"))
        pinned("post_translation_physical", digest(original),
               evidence.get("candidate_physical_sha256"))
        name = evidence.get("origin_path")
        if not isinstance(name, str):
            raise Rejected("translation origin requires separate source path")
        origin_path = Path(name)
        if (not origin_path.is_absolute()
                or origin_path in (source, candidate, receipt_path, translation_path)):
            raise Rejected("translation origin must be a distinct absolute file")
        origin_snapshot = read_fixed(origin_path)
        pinned("translation_origin", digest(origin_snapshot),
               evidence.get("origin_sha256"))
    elif "translation_receipt" in receipt or trusted_translation_sha256 is not None:
        raise Rejected("current-era source must not carry translation evidence")
    # Never interpret validity from Zig's physical success alone.
    backend = run_checked([str(sens_bin), "backend"], runner=runner)
    if (b"transport=zig" not in backend.stdout
            or b"semantic_authority=SENS" not in backend.stdout):
        raise Rejected("SENS executable has no evidenced Zig mechanical backend")
    # A digest of the source and a digest of the carrier are NOT a binding:
    # both could be separately pinned while referring to different programs.
    # Only the language-owned canonical SENS source admission can produce the
    # corresponding physical T5 file. This step deliberately stays OUTSIDE Zig.
    # A translated-era receipt identifies the upstream historical source;
    # the supplied .lisp here must be the admitted POST-translation bit source.
    if source.suffix != ".lisp":
        raise Rejected("post-admission source must have .lisp suffix")
    with tempfile.TemporaryDirectory(prefix="sens-pub-preflight-") as temp:
        temp_dir = Path(temp)
        replay_path = temp_dir / "replay.sens"
        run_checked([str(zig_bin), "t5-roundtrip", str(candidate), str(replay_path)],
                    runner=runner)
        replay = read_fixed(replay_path)
        if replay != original:
            raise Rejected(
                f"Zig byte replay mismatch original_sha={digest(original)} "
                f"replay_sha={digest(replay)}"
            )
        # Execute SENS source→transport; never rely on an unverified
        # Python/Rust projection or on the two independent manifest hashes.
        source_snapshot = temp_dir / "admitted-source.lisp"
        source_snapshot.write_bytes(initial_source)
        run_checked([str(sens_bin), "encode", str(source_snapshot)], runner=runner)
        encoded_path = source_snapshot.with_suffix(".sens")
        if not encoded_path.is_file() or encoded_path.is_symlink():
            raise Rejected("SENS source encode produced no regular physical .sens")
        encoded = read_fixed(encoded_path)
        if encoded != original:
            raise Rejected(
                f"SENS source/physical mismatch source_sha={digest(initial_source)} "
                f"candidate_sha={digest(original)} encoded_sha={digest(encoded)}"
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
    if origin_path is not None and read_fixed(origin_path) != origin_snapshot:
        raise Rejected("translation origin mutated during verification")
    if (read_fixed(zig_bin, max_size=MAX_EXECUTABLE_SIZE) != zig_binary
            or read_fixed(sens_bin, max_size=MAX_EXECUTABLE_SIZE) != sens_binary):
        raise Rejected("executor changed during admission")
    return {
        "status": "CANDIDATE_VERIFIED_NOT_PUBLISHED",
        "source_era": receipt["source_era"],
        "physical_sha256": digest(original),
        "native_stdout_sha256": digest(native.stdout),
        "semantic_authority": "SENS_EXECUTED_NOT_RATIFIED_BY_THIS_SCRIPT",
        "provenance_status": ("EXTERNAL_PIN_AND_SOURCE_BOUND_NOT_AUTHENTICATED"
                              if translation_path is not None else "EXPLICIT_CURRENT_UNAUTHENTICATED"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for opt in ("candidate", "source", "receipt", "zig", "sens"):
        parser.add_argument("--" + opt, type=Path, required=True)
    parser.add_argument("--trusted-translation-sha256",
                        help="independently established exact provenance SHA256; mandatory for translated era")
    args = parser.parse_args()
    try:
        record = verify(
            args.candidate, args.source, args.receipt, args.zig, args.sens,
            trusted_translation_sha256=args.trusted_translation_sha256,
        )
    except Rejected as exc:
        print(f"ZIG_PUBLICATION_CANDIDATE_RED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
