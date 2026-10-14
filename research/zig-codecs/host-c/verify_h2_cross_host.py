#!/usr/bin/env python3
"""Manual H2 orchestrator: same binary SENS self-verdict corpus, Rust/C hosts.

No language semantics live here. This script verifies input provenance and
compares two ACTUALLY EXECUTED, pre-existing proof runners; it never emulates
SENS or substitutes a mock Zig ABI. H2 can PASS only when both hosts run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
CASES = (
    ("retired-d3-cond", "fb0a68205bb80e3f8e14dfab6da14c5b70f1e0dc",
     "6432daaa5979b4ba25091b87921c35be8030d91d"),
    ("retired-d3-eq", "2b784c881d67a9afc755985782c1bbbed5aa48fd",
     "8a0568e31d11fed716370cb5d57049c42556f36e"),
    ("retired-quote-inert-d3", "bb04950a253a125c60c9c823ef47de1d8a3f0d8e",
     "81cc330df7fda46c52317d2c11cda19e7a72f2e1"),
)
C_SOURCE = "research/zig-codecs/host-c/d3_subset.c"
C_ABI_HEADER = "research/zig-codecs/host-c/zig_transport_v2.h"
C_DRIVER = "research/zig-codecs/host-c/verify_d3_subset.sh"
RUST_DRIVERS = ("scripts/prove-retired-d3-laws.sh", "scripts/prove-retired-quote-inert.sh")
ZIG_ABI = "research/zig-codecs/transport_abi.zig"
WORDS = re.compile(rb"^[01 \t\r\n]+$")


# This pins the selected H2 source path, not every transitive Rust dependency.
# Unrelated dirty worktree files do not block the migration swarm.
H2_TRACKED_INPUTS = (
    "research/zig-codecs/host-c/verify_h2_cross_host.py",
    C_SOURCE, C_ABI_HEADER, C_DRIVER, ZIG_ABI,
    "research/zig-codecs/t5/t5.zig",
    "research/zig-codecs/f3c/f3c.zig",
    "scripts/sens_t5_codec.py", ".zig-version", *RUST_DRIVERS,
    *(f"tests/semantic/{name}-{role}.bits"
      for name, _, _ in CASES for role in ("law", "mutant")),
)


class AuditFailure(Exception):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()


def verify_git_provenance(root: Path, paths: tuple[str, ...]) -> dict:
    """Pin exact regular Git-tracked H2 inputs: HEAD == index == worktree."""
    root = root.resolve()

    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True,
                                text=True, errors="replace", check=False)
        if result.returncode:
            raise AuditFailure(
                f"test_id=H2_SOURCE_PIN layer=provenance command=git_{args[0]} "
                f"exit={result.returncode} stderr={result.stderr.strip()[:220]!r}")
        return result.stdout.strip()

    actual_root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if actual_root != root:
        raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                           f"expected_root={root} actual_root={actual_root}")
    head = git("rev-parse", "--verify", "HEAD")
    pinned = {}
    for name in paths:
        file = root / name
        if file.is_symlink() or not file.is_file():
            raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                               f"path={name} expected=regular_file actual=missing_or_symlink")
        rows = git("ls-files", "--stage", "--", name).splitlines()
        if len(rows) != 1 or "\t" not in rows[0]:
            raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                               f"path={name} expected=one_index_entry actual={len(rows)}")
        attrs, recorded_path = rows[0].split("\t", 1)
        fields = attrs.split()
        if (recorded_path != name or len(fields) != 3
                or fields[0] not in ("100644", "100755") or fields[2] != "0"):
            raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                               f"path={name} expected=regular_stage_zero actual={attrs!r}")
        mode, index_blob, _stage = fields
        expected = git("rev-parse", f"HEAD:{name}")
        actual = git_blob(file.read_bytes())
        if expected != index_blob or expected != actual:
            raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance path={name} "
                               f"expected_head_blob={expected} index_blob={index_blob} "
                               f"actual_worktree_blob={actual}")
        pinned[name] = {"git_blob_sha1": expected, "git_mode": mode}
    return {
        "head_sha": head, "tracked": pinned,
        "scope": "selected H2 caller/codec/native scripts and six fixtures",
        "not_claimed": "complete Rust build dependency closure",
    }


def git_provenance_self_test() -> None:
    """Four synthetic provenance cases; never a mock semantic evaluator."""
    with tempfile.TemporaryDirectory(prefix="sens-h2-pin-") as tmp:
        root = Path(tmp)
        def cmd(*args: str) -> None:
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
        cmd("init", "-q")
        path = root / "input.bits"
        path.write_bytes(b"10 001 00\n")
        cmd("add", "input.bits")
        cmd("-c", "user.name=H2", "-c", "user.email=h2@example.invalid",
            "commit", "-qm", "pin")
        assert verify_git_provenance(root, ("input.bits",))["tracked"]["input.bits"]["git_mode"] == "100644"
        path.write_bytes(b"10 001 01\n")
        for label in ("WORKTREE_CHANGED", "INDEX_STAGED"):
            if label == "INDEX_STAGED":
                cmd("add", "input.bits")
            try:
                verify_git_provenance(root, ("input.bits",))
            except AuditFailure as exc:
                if "expected_head_blob=" not in str(exc):
                    raise
            else:
                raise AuditFailure(f"test_id=H2_{label} expected=REJECT actual=ACCEPT")
        path.write_bytes(b"10 001 00\n")
        cmd("add", "input.bits")
        try:
            verify_git_provenance(root, ("untracked.bits",))
        except AuditFailure as exc:
            if "expected=regular_file" not in str(exc):
                raise
        else:
            raise AuditFailure("test_id=H2_UNTRACKED expected=REJECT actual=ACCEPT")
    print("H2_GIT_SOURCE_PIN_SELF_TEST_PASS cases=4")


def inspect_pair(name: str, pos_raw: bytes, neg_raw: bytes, pos_pin: str, neg_pin: str) -> dict:
    for label, raw, pin in (("law", pos_raw, pos_pin), ("mutant", neg_raw, neg_pin)):
        if git_blob(raw) != pin:
            raise AuditFailure(f"test_id={name} layer=provenance fixture={label} "
                               f"expected_blob={pin} actual_blob={git_blob(raw)}")
        if not raw or not WORDS.fullmatch(raw):
            raise AuditFailure(f"test_id={name} layer=source fixture={label} invalid_binary_source")
    positive = pos_raw.split()
    negative = neg_raw.split()
    if len(positive) != len(negative):
        raise AuditFailure(f"test_id={name} layer=source expected=same_word_count "
                           f"actual={len(positive)}/{len(negative)}")
    changes = []
    for index, (a, b) in enumerate(zip(positive, negative)):
        if len(a) != len(b):
            raise AuditFailure(f"test_id={name} layer=source word={index} "
                               f"expected=exact_same_width actual={len(a)}/{len(b)}")
        for bit_idx, (left, right) in enumerate(zip(a, b)):
            if left != right:
                changes.append((index, bit_idx, chr(left), chr(right)))
    if len(changes) != 1 or changes[0][2:] != ("0", "1"):
        raise AuditFailure(f"test_id={name} layer=source expected=one_bit_0_to_1 actual={changes[:4]}")
    index = changes[0][0]
    if len(positive[index]) != 1:
        raise AuditFailure(f"test_id={name} layer=source expected=mutated_D1 actual_width={len(positive[index])}")
    return {
        "test_id": name, "layer": "source", "words": len(positive),
        "first_mismatch": {"word": index, "bit": changes[0][1], "expected": "0", "actual": "1"},
        "law": {"git_blob_sha1": pos_pin, "sha256": sha256(pos_raw)},
        "mutant": {"git_blob_sha1": neg_pin, "sha256": sha256(neg_raw)},
        "negative_category": "D1_NONCALLABLE",
    }


def preflight(root: Path) -> dict:
    cases = []
    for name, pos_pin, neg_pin in CASES:
        base = root / "tests" / "semantic"
        cases.append(inspect_pair(
            name, (base / f"{name}-law.bits").read_bytes(),
            (base / f"{name}-mutant.bits").read_bytes(), pos_pin, neg_pin))
    for path in (C_SOURCE, C_ABI_HEADER, C_DRIVER, ZIG_ABI, *RUST_DRIVERS):
        if not (root / path).is_file():
            raise AuditFailure(f"test_id=H2_SOURCE layer=provenance missing={path}")
    c_src = (root / C_SOURCE).read_text(encoding="utf-8")
    c_driver = (root / C_DRIVER).read_text(encoding="utf-8")
    abi = (root / ZIG_ABI).read_text(encoding="utf-8")
    for name, _, _ in CASES:
        for role in ("law", "mutant"):
            path = f"tests/semantic/{name}-{role}.bits"
            if path not in c_src:
                # C executor uses family/role construction; confirm prefix and file construction.
                if f'"{name}"' not in c_src and f'"{name}-{role}.bits"' not in c_src:
                    raise AuditFailure(f"test_id=H2_CORPUS layer=source C_does_not_select={path}")
    for api in ("sens_zig_t5_encode_be3", "sens_zig_t5_decode_be3", "sens_zig_codec_abi_version"):
        if api not in abi or api not in c_src:
            raise AuditFailure(f"test_id=H2_CORRIDOR layer=transport missing_abi={api}")
    if "transport_abi.zig" not in c_driver or "d3_subset.c" not in c_driver:
        raise AuditFailure("test_id=H2_C_BUILD layer=provenance C_driver_does_not_link_Zig")
    if "cargo" in c_driver or "rustc" in c_driver or "crates/sens" in c_driver:
        raise AuditFailure("test_id=H2_C_BUILD layer=dependency C_driver_includes_Rust")
    return {
        "test_id": "H2_SENS_SAME_CORPUS", "status": "SOURCE_PREFLIGHT_PASS",
        "semantic_status": "UNVERIFIED_UNTIL_TWO_HOST_RUN",
        "host_a": "SENS-native-via-Rust", "host_b": "Rust-free-C-through-Zig-ABI-v2",
        "cases": cases,
        "source_sha256": {p: sha256((root / p).read_bytes())
                          for p in (C_SOURCE, C_ABI_HEADER, C_DRIVER, ZIG_ABI, *RUST_DRIVERS)},
    }


def negative_self_test(root: Path) -> None:
    name, good_pin, bad_pin = CASES[0]
    good = (root / "tests" / "semantic" / f"{name}-law.bits").read_bytes()
    bad = (root / "tests" / "semantic" / f"{name}-mutant.bits").read_bytes()
    malformed = good.replace(b"10", b"1x", 1)
    wrong_count = bad + b" 0"
    wrong_width = bad.replace(b"10 110", b"10 1100", 1)
    probes = {
        "SOURCE_PIN_DRIFT": ((good + b" ", bad, good_pin, bad_pin), "actual_blob="),
        "BAD_BINARY_CHAR": ((malformed, bad, git_blob(malformed), bad_pin), "invalid_binary_source"),
        "WRONG_WORD_COUNT": ((good, wrong_count, good_pin, git_blob(wrong_count)), "actual="),
        "WRONG_BIT_WIDTH": ((good, wrong_width, good_pin, git_blob(wrong_width)),
                            "expected=exact_same_width"),
        "NO_MUTATION": ((good, good, good_pin, good_pin), "expected=one_bit_0_to_1"),
    }
    for test_id, (args, expected_diagnostic) in probes.items():
        try:
            inspect_pair(name, *args)
        except AuditFailure as exc:
            if expected_diagnostic not in str(exc):
                raise AuditFailure(f"test_id={test_id} layer=source wrong_negative_reason={exc}") from exc
            print(f"H2_NEGATIVE_PASS test_id={test_id} category={expected_diagnostic}")
        else:
            raise AuditFailure(f"test_id={test_id} layer=source expected=REJECT actual=ACCEPT")

    # These parser negatives concern physical bytes only, not SENS meaning.
    fixture = "tests/semantic/retired-d3-cond-law.bits"
    example = f"C_D3_SUBSET_T5 source={fixture} bytes=1 hex=a1"
    missing = "test_id=H2_C_T5"
    for label, stream in (
        ("MISSING_PHYSICAL_T5", ""),
        ("DUPLICATE_PHYSICAL_T5", example + "\n" + example),
        ("SHORT_PHYSICAL_T5", example.replace("bytes=1", "bytes=2")),
        ("BAD_PHYSICAL_HEX", example.replace("hex=a1", "hex=zz")),
    ):
        try:
            parse_c_physical(stream)
        except (AuditFailure, ValueError) as exc:
            if missing not in str(exc) and label != "BAD_PHYSICAL_HEX":
                raise AuditFailure(f"test_id={label} layer=transport wrong_reason={exc}") from exc
            print(f"H2_NEGATIVE_PASS test_id={label} category=H2_C_T5")
        else:
            raise AuditFailure(f"test_id={label} layer=transport expected=REJECT actual=ACCEPT")
    print(f"H2_PREFLIGHT_NEGATIVES_PASS rejected={len(probes) + 4}")



def parse_c_physical(stdout: str) -> dict[str, dict]:
    """Read ACTUAL Zig T5 bytes reported by the C process (all six inputs)."""
    observed = {}
    for line in stdout.splitlines():
        if not line.startswith("C_D3_SUBSET_T5"):
            continue
        match = re.fullmatch(
            r"C_D3_SUBSET_T5 source=(tests/semantic/[a-z0-9-]+-(?:law|mutant)\.bits)"
            r" bytes=([1-9][0-9]*) hex=([0-9a-f]+)", line)
        if not match:
            raise AuditFailure(f"test_id=H2_C_T5 layer=transport malformed_receipt={line[:200]}")
        source, length, hexdump = match.groups()
        if source in observed:
            raise AuditFailure(f"test_id=H2_C_T5 layer=transport duplicate_receipt={source}")
        if len(hexdump) != 2 * int(length):
            raise AuditFailure(f"test_id=H2_C_T5 layer=transport fixture={source} "
                               f"expected_hex_len={2 * int(length)} actual={len(hexdump)}")
        data = bytes.fromhex(hexdump)
        observed[source] = {"bytes": len(data), "sha256": sha256(data)}
    expected = {f"tests/semantic/{name}-{role}.bits"
                for name, _, _ in CASES for role in ("law", "mutant")}
    if set(observed) != expected:
        raise AuditFailure(f"test_id=H2_C_T5 layer=transport "
                           f"missing={sorted(expected - set(observed))} "
                           f"extra={sorted(set(observed) - expected)}")
    return observed


def verify_native_physical(stdout: str, physical: dict, files: tuple[tuple[str, str], ...]) -> None:
    """Compare C/Zig actual physical T5 SHA to hashes of native SENS input files."""
    for source, suffix in files:
        regex = rf"(?m)^([0-9a-f]{{64}})[ \t]+\S*/{re.escape(suffix)}[ \t]*$"
        hits = re.findall(regex, stdout)
        if len(hits) != 1:
            raise AuditFailure(f"test_id=H2_NATIVE_T5 layer=transport "
                               f"fixture={source} expected=one_native_SHA actual={len(hits)}")
        actual = hits[0]
        expected = physical[source]["sha256"]
        if actual != expected:
            raise AuditFailure(f"test_id=H2_T5_PARITY layer=transport fixture={source} "
                               f"expected_zig_c_sha256={expected} actual_native_sha256={actual} "
                               "first_diff=unavailable_without_native_raw")

def invoke(cmd: list[str], root: Path, marker: str, validator=None) -> dict:
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, errors="replace", check=False)
    record = {
        "argv": cmd, "exit_code": result.returncode, "stdout_sha256": sha256(result.stdout.encode()),
        "stderr_sha256": sha256(result.stderr.encode()), "expected_marker": marker,
        "marker_observed": marker in result.stdout,
    }
    if result.returncode or marker not in result.stdout:
        excerpt = (result.stderr or result.stdout)[-1800:]
        raise AuditFailure(f"test_id=H2_RUN layer=execution command={cmd!r} "
                           f"exit={result.returncode} expected_marker={marker!r} diagnostic={excerpt!r}")
    if validator is not None:
        validator(result.stdout)
    return record


def run_both(root: Path, receipt: dict, sens_bin: str) -> dict:
    receipt["git_source_pin"] = verify_git_provenance(root, H2_TRACKED_INPUTS)
    for tool in ("zig", "cc", "cargo", "bash"):
        if not shutil.which(tool):
            raise AuditFailure(f"test_id=H2_RUN layer=toolchain missing={tool} "
                               "status=UNVERIFIED_NO_MOCK")
    pinned = (root / ".zig-version").read_text(encoding="ascii").strip()
    zig = invoke(["zig", "version"], root, pinned)
    build = invoke(["cargo", "build", "--locked", "-p", "sens-cli", "--bin", "sens"], root, "")
    exe = root / sens_bin
    if not exe.is_file():
        raise AuditFailure(f"test_id=H2_RUN layer=executor missing={exe}")
    c_binary_digest: list[str] = []
    c_physical: dict[str, dict] = {}
    def check_c_verdicts(stdout: str) -> None:
        # These are observations from the C process, not Python-authored SENS laws.
        receipt = re.search(r"^C_D3_SUBSET_RECEIPT zig=\S+ c_binary_sha256=([0-9a-f]{64})$",
                            stdout, re.MULTILINE)
        if receipt is None:
            raise AuditFailure("test_id=H2_C_BINARY layer=dependency missing_binary_sha256")
        c_binary_digest.append(receipt.group(1))
        for name, _, _ in CASES:
            for state, expected in (("law", "C_D3_SUBSET_PASS"),
                                    ("mutant", "C_D3_SUBSET_NEGATIVE_PASS")):
                matching = [line for line in stdout.splitlines()
                            if line.startswith(expected + " ") and
                            f"source=tests/semantic/{name}-{state}.bits" in line]
                if len(matching) != 1:
                    raise AuditFailure(f"test_id=H2_COMPARISON layer=execution C_missing={name}-{state}")
                if state == "mutant" and "category=NONCALLABLE_HEAD" not in matching[0]:
                    raise AuditFailure(f"test_id=H2_COMPARISON layer=eval expected=D1_NONCALLABLE C={matching[0]}")
                if state == "law" and "result=D1:1" not in matching[0]:
                    raise AuditFailure(f"test_id=H2_COMPARISON layer=eval expected=D1:YES C={matching[0]}")
        # Unlike source hashes, these six bytestrings are emitted by the
        # actual C process after Zig ABI v2 has encoded the exact BE3 words.
        c_physical.update(parse_c_physical(stdout))
    c_host = invoke(["bash", C_DRIVER], root,
                    "C_D3_SUBSET_SOURCE_WITNESS_PASS", validator=check_c_verdicts)
    native_a = invoke(
        ["bash", RUST_DRIVERS[0], str(exe)], root, "NATIVE_SENS_PASS id=retired-d3-eq",
        validator=lambda output: verify_native_physical(
            output, c_physical, tuple(
                (f"tests/semantic/retired-d3-{kind}-{role}.bits", f"{kind}-{role}.sens")
                for kind in ("cond", "eq") for role in ("law", "mutant"))))
    native_b = invoke(
        ["bash", RUST_DRIVERS[1], str(exe)], root,
        "NATIVE_SENS_PASS test_id=retired-quote-inert-d3",
        validator=lambda output: verify_native_physical(
            output, c_physical, tuple(
                (f"tests/semantic/retired-quote-inert-d3-{role}.bits", f"{role}.sens")
                for role in ("law", "mutant"))))
    receipt.update({
        "status": "TWO_HOST_EXECUTED", "semantic_status": "SUBSET_MATCHED",
        "scope": "only 3 pinned D1/D2/D3 binary self-verdicts + one-bit negatives",
        "toolchain": {"zig_version": pinned, "c_compiler": shutil.which("cc")},
        "rust_host_binary_sha256": sha256(exe.read_bytes()),
        "c_host_binary_sha256": c_binary_digest[0],
        "physical_t5_sha256": {p: item["sha256"] for p, item in sorted(c_physical.items())},
        "physical_t5_bytes": {p: item["bytes"] for p, item in sorted(c_physical.items())},
        "transport_status": "ZIG_C_AND_NATIVE_SENS_PHYSICAL_SHA256_MATCHED_SIX_OF_SIX",
        "runs": {"zig": zig, "rust_build": build, "c": c_host, "native_d3": native_a, "native_quote": native_b},
    })
    return receipt


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--sens-bin", default="target/debug/sens")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="actually build and execute both hosts; no mock/fallback")
    args = ap.parse_args()
    try:
        r = preflight(args.root)
        if args.self_test:
            negative_self_test(args.root)
            git_provenance_self_test()
        if args.run:
            r = run_both(args.root, r, args.sens_bin)
        print(json.dumps(r, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, AuditFailure) as exc:
        print(f"H2_UNVERIFIED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
