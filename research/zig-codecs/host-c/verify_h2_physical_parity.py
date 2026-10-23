#!/usr/bin/env python3
"""Manual H2 physical parity: actual C -> Zig T5 bytes vs native-input T5 bytes.

Only exact-width transport is compared. Python is mechanical fixture glue.
Semantic SENS conformance is a SEPARATE proof (#5788), never inferred here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_t5m_codec import decode_bytes, encode_projection, parse_words  # noqa: E402
from verify_h2_cross_host import AuditFailure, CASES, preflight  # noqa: E402

C_SOURCE = "research/zig-codecs/host-c/h2_t5_dump.c"
ABI_SOURCE = "research/zig-codecs/transport_abi.zig"
REF_SOURCE = "scripts/sens_t5_t5m_codec.py"
REPRODUCE = "python3 research/zig-codecs/host-c/verify_h2_physical_parity.py --run"


class PhysicalError(Exception):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def exact_be3(words: list[str]) -> bytes:
    """Physical bit packing ONLY: width and two BE payload bytes; no meaning."""
    out = bytearray()
    if not words:
        raise PhysicalError("test_id=H2_BE3 layer=source empty_words")
    for index, word in enumerate(words):
        if not 1 <= len(word) <= 9 or any(bit not in "01" for bit in word):
            raise PhysicalError(f"test_id=H2_BE3 layer=source word={index} invalid_exact_width")
        bits = 0
        for bit in word:
            bits = (bits << 1) | (bit == "1")
        out.extend((len(word), (bits >> 8) & 255, bits & 255))
    return bytes(out)


def corpus(root: Path) -> list[dict]:
    # The existing H2 preflight pins six independent Git blob SHA1s and checks
    # three width-preserving, D1 one-bit pairs; we reuse rather than fork it.
    preflight(root)
    records = []
    for family, _, _ in CASES:
        for role in ("law", "mutant"):
            path = f"tests/semantic/{family}-{role}.bits"
            raw = (root / path).read_bytes()
            try:
                words = parse_words(raw.decode("ascii"))
            except (ValueError, UnicodeError) as exc:
                raise PhysicalError(f"test_id={family} layer=source invalid_binary={exc}") from exc
            if any(len(word) > 9 for word in words):
                raise PhysicalError(f"test_id={family} layer=source unadmitted_ordinary_width")
            t5 = encode_projection(" ".join(words))
            if decode_bytes(t5) != words:
                raise PhysicalError(f"test_id={family} layer=transport reference_roundtrip_changed_width")
            records.append({
                "test_id": family, "role": role, "path": path, "source_sha256": digest(raw),
                "be3": exact_be3(words), "reference_t5": t5, "words": len(words),
            })
    return records


def first_mismatch(a: bytes, b: bytes) -> int | None:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    if len(a) != len(b):
        return min(len(a), len(b))
    return None


def call(args: list[str], cwd: Path, *, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, cwd=cwd, input=input_bytes, capture_output=True,
                              check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PhysicalError(f"test_id=H2_TOOL layer=toolchain cmd={args!r} reason={exc}") from exc


def tool_path(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise PhysicalError(f"test_id=H2_TOOL layer=toolchain missing={name} status=UNVERIFIED")
    return found


def source_snapshot_ok(head: str, top: str, dirty: bytes, root: Path) -> bool:
    """Exact source SHA + canonical repository root + no tracked/untracked drift.

    Structural Git source identity only, NOT a signed supply-chain attestation.
    """
    return (
        re.fullmatch(r"[0-9a-f]{40}", head) is not None
        and Path(top).resolve() == root.resolve()
        and not dirty
    )


def require_same_source_head(before: str, after: str) -> None:
    if before != after:
        raise PhysicalError(
            f"test_id=H2_SOURCE_DRIFT layer=provenance "
            f"expected_head={before} actual_head={after} reproduce={REPRODUCE}"
        )


def ensure_clean_git(root: Path) -> str:
    tool_path("git")
    head = call(["git", "rev-parse", "--verify", "HEAD"], root)
    top = call(["git", "rev-parse", "--show-toplevel"], root)
    status = call(["git", "status", "--porcelain=v1", "--untracked-files=all"], root)
    if head.returncode or top.returncode or status.returncode:
        raise PhysicalError("test_id=H2_SOURCE layer=provenance git_source_probe_failed")
    try:
        exact_sha = head.stdout.decode("ascii").strip()
        top_path = top.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise PhysicalError("test_id=H2_SOURCE layer=provenance noncanonical_git_output") from exc
    if not source_snapshot_ok(exact_sha, top_path, status.stdout, root):
        raise PhysicalError(
            f"test_id=H2_SOURCE layer=provenance source_not_clean_exact_sha "
            f"actual_head={exact_sha} root_matches={Path(top_path).resolve() == root.resolve()} "
            f"status_sha256={digest(status.stdout)} reproduce={REPRODUCE}"
        )
    return exact_sha


def require_controlled_rejection(
    r: subprocess.CompletedProcess, test_id: str, expected_category: str
) -> None:
    """Check the actual C-host failure reason, not just a generic red exit."""
    if expected_category not in ("MALFORMED_BE3_LENGTH", "ZIG_ENCODE"):
        raise PhysicalError(
            f"test_id={test_id} layer=harness unsupported_expected_category="
            f"{expected_category}"
        )
    if r.returncode != 2 or r.stdout:
        raise PhysicalError(
            f"test_id={test_id} layer=transport expected_exit=2 "
            f"expected_stdout=EMPTY actual_exit={r.returncode} "
            f"stdout_sha256={digest(r.stdout)}")
    expected_stderr = (
        f"H2_T5_DUMP_REJECT layer=transport category={expected_category}\n"
    ).encode("ascii")
    if r.stderr != expected_stderr:
        raise PhysicalError(
            f"test_id={test_id} layer=transport "
            f"expected_category={expected_category} "
            f"expected_stderr_sha256={digest(expected_stderr)} "
            f"actual_stderr_sha256={digest(r.stderr)}"
        )


def reject_run(
    executable: Path, root: Path, test_id: str, payload: bytes, expected_category: str
) -> None:
    require_controlled_rejection(
        call([str(executable)], root, input_bytes=payload),
        test_id, expected_category
    )


def real_run(root: Path, records: list[dict]) -> dict:
    zig = tool_path(os.environ.get("ZIG", "zig"))
    cc = tool_path(os.environ.get("CC", "cc"))
    pinned = (root / ".zig-version").read_text(encoding="ascii").strip()
    actual = call([zig, "version"], root)
    if actual.returncode or actual.stdout.decode().strip() != pinned:
        raise PhysicalError(f"test_id=H2_ZIG_PIN layer=toolchain expected={pinned} "
                            f"actual={actual.stdout.decode(errors='replace').strip()}")
    git_head = ensure_clean_git(root)
    for path in (C_SOURCE, ABI_SOURCE, REF_SOURCE):
        if not (root / path).is_file():
            raise PhysicalError(f"test_id=H2_SOURCE layer=provenance missing={path}")
    with tempfile.TemporaryDirectory(prefix="sens-h2-t5-") as temp:
        directory = Path(temp)
        library = directory / "libsens_zig_transport.a"
        executable = directory / "sens-h2-t5-dump"
        zig_build = call([zig, "build-lib", ABI_SOURCE, "-O", "ReleaseFast", "-lc",
                          "-fPIC", f"-femit-bin={library}"], root)
        if zig_build.returncode or not library.is_file():
            raise PhysicalError(f"test_id=H2_ZIG_BUILD layer=toolchain exit={zig_build.returncode} "
                                f"stderr={zig_build.stderr.decode(errors='replace')[-1200:]!r}")
        c_build = call([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2",
                        C_SOURCE, str(library), "-lm", "-ldl", "-pthread",
                        "-o", str(executable)], root)
        if c_build.returncode or not executable.is_file():
            raise PhysicalError(f"test_id=H2_C_BUILD layer=toolchain exit={c_build.returncode} "
                                f"stderr={c_build.stderr.decode(errors='replace')[-1200:]!r}")

        checks = []
        for row in records:
            observed = call([str(executable)], root, input_bytes=row["be3"])
            if observed.returncode:
                raise PhysicalError(f"test_id={row['test_id']} role={row['role']} "
                                    f"layer=transport C_Zig_exit={observed.returncode} "
                                    f"stderr={observed.stderr.decode(errors='replace')[-900:]!r}")
            expected = row["reference_t5"]
            diff = first_mismatch(expected, observed.stdout)
            if diff is not None:
                raise PhysicalError(
                    f"test_id={row['test_id']} role={row['role']} layer=transport "
                    f"first_mismatch_byte={diff} expected_sha256={digest(expected)} "
                    f"actual_sha256={digest(observed.stdout)} reproduce={REPRODUCE}")
            checks.append({
                "test_id": row["test_id"], "role": row["role"], "source": row["path"],
                "input_sha256": row["source_sha256"], "be3_sha256": digest(row["be3"]),
                "expected_t5_sha256": digest(expected),
                "actual_t5_sha256": digest(observed.stdout),
                "physical_bytes": len(expected), "first_mismatch_byte": None,
                "status": "BYTE_EXACT",
            })
        # Independent C-host -> Zig ABI -> T5 positive width pair.
        # The numeric payload is equal (=1), but D1:1 and D2:01 MUST
        # remain physically distinct. Neither case grants callability.
        exact_width_pair = []
        for name, words in (("D1_ONE", ["1"]), ("D2_LEADING_ZERO_ONE", ["01"])):
            be3 = exact_be3(words)
            expected_t5 = encode_projection(" ".join(words))
            observed = call([str(executable)], root, input_bytes=be3)
            mismatch = first_mismatch(expected_t5, observed.stdout)
            if observed.returncode or mismatch is not None:
                raise PhysicalError(
                    f"test_id=H2_EXACT_WIDTH_{name} layer=transport "
                    f"expected_sha256={digest(expected_t5)} "
                    f"actual_sha256={digest(observed.stdout)} "
                    f"first_mismatch_byte={mismatch} actual_exit={observed.returncode} "
                    f"reproduce={REPRODUCE}"
                )
            exact_width_pair.append({
                "test_id": name, "be3_sha256": digest(be3),
                "physical_sha256": digest(observed.stdout),
                "width_bits": len(words[0]), "status": "BYTE_EXACT",
            })
        if exact_width_pair[0]["physical_sha256"] == exact_width_pair[1]["physical_sha256"]:
            raise PhysicalError(
                f"test_id=H2_EXACT_WIDTH layer=transport "
                f"expected=D1_D2_DISTINCT actual=COLLISION reproduce={REPRODUCE}"
            )
        negatives = [
            ("EMPTY", b"", "MALFORMED_BE3_LENGTH"),
            ("INCOMPLETE_BE3", b"\x01\x00", "MALFORMED_BE3_LENGTH"),
            ("ZERO_WIDTH", b"\x00\x00\x00", "ZIG_ENCODE"),
            ("D10_ORDINARY_REJECT", b"\x0a\x00\x01", "ZIG_ENCODE"),
            ("D11_UNADMITTED_REJECT", b"\x0b\x00\x00", "ZIG_ENCODE"),
            ("PAYLOAD_EXCEEDS_WIDTH", b"\x01\x00\x02", "ZIG_ENCODE"),
            ("D2_PAYLOAD_OVERFLOW", b"\x02\x00\x04", "ZIG_ENCODE"),
            ("D9_PAYLOAD_OVERFLOW", b"\x09\x02\x00", "ZIG_ENCODE"),
            ("BE3_HIGH_BYTE_NONCANONICAL", b"\x01\x01\x00", "ZIG_ENCODE"),
        ]
        for test_id, invalid, category in negatives:
            reject_run(executable, root, test_id, invalid, category)
        # A successful physical replay belongs to one immutable source
        # revision. Refuse a receipt if another writer mutated HEAD or any
        # tracked/untracked file during the build and C→Zig replay.
        require_same_source_head(git_head, ensure_clean_git(root))
        return {
            "test_id": "H2_C_ZIG_PHYSICAL_EQUALITY", "status": "PHYSICAL_PARITY_PASS",
            "semantic_status": "NOT_VERIFIED_BY_THIS_TEST",
            "git_head": git_head, "zig_version": pinned,
            "abi_source_sha256": digest((root / ABI_SOURCE).read_bytes()),
            "c_source_sha256": digest((root / C_SOURCE).read_bytes()),
            "reference_codec_sha256": digest((root / REF_SOURCE).read_bytes()),
            "zig_library_sha256": digest(library.read_bytes()),
            "c_binary_sha256": digest(executable.read_bytes()),
            "positive_and_mutant_corpus": checks,
            "exact_width_h2_pair": exact_width_pair,
            "negative_transport_rejected": [n for n, _, _ in negatives],
            "reproduce": REPRODUCE,
        }


def self_test() -> None:
    for label, sample in [
        ("EMPTY", []), ("D10", ["0" * 10]), ("D11", ["0" * 11]),
        ("NON_BINARY", ["01x"]),
    ]:
        try:
            exact_be3(sample)
        except PhysicalError:
            print(f"H2_BE3_NEGATIVE_PASS test_id={label}")
        else:
            raise PhysicalError(f"test_id={label} layer=source invalid_word_accepted")
    # D1:1 and D2:01 carry the same low bit but DIFFERENT exact widths.
    if exact_be3(["1"]) == exact_be3(["01"]):
        raise PhysicalError("test_id=EXACT_WIDTH layer=transport collapsed_D1_and_D2")
    # Fixed independent physical sentinels: a leading zero is part of identity.
    if (encode_projection("1") != b"\xa1" or
            encode_projection("01") != b"\x35"):
        raise PhysicalError("test_id=H2_EXACT_WIDTH layer=transport reference_golden_drift")
    if first_mismatch(b"\x01\x02", b"\x01\x03") != 1:
        raise PhysicalError("test_id=FIRST_MISMATCH layer=diagnostics index_wrong")
    # An exit=2 is not enough: assert the precise C/Zig error category.
    marker = b"H2_T5_DUMP_REJECT layer=transport category=ZIG_ENCODE\n"

    def synthetic(
        rc: int, stdout: bytes = b"", stderr: bytes = marker
    ) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(["h2-controlled-negative"], rc, stdout, stderr)

    require_controlled_rejection(
        synthetic(2), "H2_CONTROLLED_REJECT_POSITIVE", "ZIG_ENCODE"
    )
    require_controlled_rejection(
        synthetic(2, stderr=b"H2_T5_DUMP_REJECT layer=transport category=MALFORMED_BE3_LENGTH\n"),
        "H2_CONTROLLED_LENGTH_POSITIVE", "MALFORMED_BE3_LENGTH"
    )
    for label, response in [
        ("EXIT_ZERO", synthetic(0)),
        ("SIGSEGV", synthetic(-11)),
        ("OTHER_FAILURE", synthetic(1)),
        ("COMMAND_NOT_FOUND", synthetic(127)),
        ("STDOUT_LEAK", synthetic(2, stdout=b"\x00")),
        ("MISSING_DIAGNOSTIC", synthetic(2, stderr=b"")),
        ("WRONG_ZIG_CATEGORY", synthetic(2, stderr=b"H2_T5_DUMP_REJECT layer=transport category=ABI_VERSION\n")),
        ("LENGTH_INSTEAD_OF_ZIG", synthetic(2, stderr=b"H2_T5_DUMP_REJECT layer=transport category=MALFORMED_BE3_LENGTH\n")),
        ("EXTRA_DIAGNOSTIC", synthetic(2, stderr=marker + b"extra\n")),
    ]:
        try:
            require_controlled_rejection(
                response, f"H2_REJECT_{label}", "ZIG_ENCODE"
            )
        except PhysicalError:
            pass
        else:
            raise PhysicalError(
                f"test_id=H2_REJECT_{label} layer=transport false_reject_pass"
            )
    print("H2_CONTROLLED_REJECT_SYNTHETIC_PASS positive=2 negative=9 categories=PINNED")
    # Synthetic source provenance controls do not run Zig or grant release GO.
    sample = "a" * 40
    sample_root = Path("/tmp/sens-h2-provenance-synthetic")
    assert source_snapshot_ok(sample, str(sample_root), b"", sample_root)
    for label, candidate_sha, candidate_top, candidate_dirty in (
        ("UNKNOWN_SHA", "UNKNOWN", str(sample_root), b""),
        ("SHORT_SHA", "abc", str(sample_root), b""),
        ("UPPERCASE_SHA", "A" * 40, str(sample_root), b""),
        ("NONHEX_SHA", "g" * 40, str(sample_root), b""),
        ("WRONG_ROOT", sample, "/tmp/other-h2-repository", b""),
        ("TRACKED_DIRTY", sample, str(sample_root), b" M source.zig\n"),
        ("UNTRACKED_DIRTY", sample, str(sample_root), b"?? injected.c\n"),
    ):
        if source_snapshot_ok(candidate_sha, candidate_top, candidate_dirty, sample_root):
            raise PhysicalError(
                f"test_id=H2_SOURCE_{label} layer=provenance synthetic_false_pass"
            )
    try:
        require_same_source_head(sample, "b" * 40)
    except PhysicalError as exc:
        if "H2_SOURCE_DRIFT" not in str(exc):
            raise
    else:
        raise PhysicalError("test_id=H2_SOURCE_DRIFT layer=provenance head_change_accepted")
    print("H2_SOURCE_SNAPSHOT_SELFTEST_PASS positive=1 negative=8 postflight=REQUIRED")
    print("H2_BE3_SYNTHETIC_PASS rejected=4 width_distinct=true physical_goldens=a1,35")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--self-test", action="store_true", help="source + synthetic tests, NO runtime parity")
    ap.add_argument("--run", action="store_true", help="actually compile C+Zig and compare physical bytes")
    opts = ap.parse_args()
    try:
        records = corpus(opts.root)
        if opts.self_test:
            self_test()
        if opts.run:
            result = real_run(opts.root, records)
        else:
            result = {
                "test_id": "H2_C_ZIG_PHYSICAL_EQUALITY", "status": "SOURCE_PREFLIGHT_ONLY",
                "semantic_status": "NOT_VERIFIED", "runtime_parity": "NOT_RUN",
                "fixtures": [
                    {"test_id": r["test_id"], "role": r["role"], "source_sha256": r["source_sha256"],
                     "reference_t5_sha256": digest(r["reference_t5"])}
                    for r in records
                ],
                "reproduce": REPRODUCE,
            }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (PhysicalError, AuditFailure, OSError, ValueError, KeyError) as exc:
        print(f"H2_PHYSICAL_UNVERIFIED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
