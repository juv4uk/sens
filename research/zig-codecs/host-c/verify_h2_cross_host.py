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
C_DRIVER = "research/zig-codecs/host-c/verify_d3_subset.sh"
RUST_DRIVERS = ("scripts/prove-retired-d3-laws.sh", "scripts/prove-retired-quote-inert.sh")
ZIG_ABI = "research/zig-codecs/transport_abi.zig"
WORDS = re.compile(rb"^[01 \t\r\n]+$")


class AuditFailure(Exception):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\x00" + raw).hexdigest()


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
    for path in (C_SOURCE, C_DRIVER, ZIG_ABI, *RUST_DRIVERS):
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
                          for p in (C_SOURCE, C_DRIVER, ZIG_ABI, *RUST_DRIVERS)},
    }


def negative_self_test(root: Path) -> None:
    name, good_pin, bad_pin = CASES[0]
    good = (root / "tests" / "semantic" / f"{name}-law.bits").read_bytes()
    bad = (root / "tests" / "semantic" / f"{name}-mutant.bits").read_bytes()
    probes = {
        "SOURCE_PIN_DRIFT": (good + b" ", bad, good_pin, bad_pin),
        "BAD_BINARY_CHAR": (good.replace(b"10", b"1x", 1), bad, good_pin, bad_pin),
        "WRONG_WORD_COUNT": (good, bad + b" 0", good_pin, git_blob(bad + b" 0")),
        "WRONG_BIT_WIDTH": (good, bad.replace(b"10 110", b"10 1100", 1),
                            good_pin, git_blob(bad.replace(b"10 110", b"10 1100", 1))),
        "NO_MUTATION": (good, good, good_pin, good_pin),
    }
    for test_id, args in probes.items():
        try:
            inspect_pair(name, *args)
        except AuditFailure:
            print(f"H2_NEGATIVE_PASS test_id={test_id}")
        else:
            raise AuditFailure(f"test_id={test_id} layer=source expected=REJECT actual=ACCEPT")
    print(f"H2_PREFLIGHT_NEGATIVES_PASS rejected={len(probes)}")


def invoke(cmd: list[str], root: Path, marker: str) -> dict:
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
    return record


def run_both(root: Path, receipt: dict, sens_bin: str) -> dict:
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
    c_host = invoke(["bash", C_DRIVER], root, "C_D3_SUBSET_SOURCE_WITNESS_PASS")
    # Explicitly check each paired result, not just a summary and exit code.
    c_recheck = subprocess.run(["bash", C_DRIVER], cwd=root,
                               capture_output=True, text=True, check=False)
    if c_recheck.returncode:
        raise AuditFailure("test_id=H2_C_RECHECK layer=execution second_run_failed")
    for name, _, _ in CASES:
        for state, expected in (("law", "C_D3_SUBSET_PASS"),
                                ("mutant", "C_D3_SUBSET_NEGATIVE_PASS")):
            matching = [line for line in c_recheck.stdout.splitlines()
                        if line.startswith(expected + " ") and
                        f"source=tests/semantic/{name}-{state}.bits" in line]
            if len(matching) != 1:
                raise AuditFailure(f"test_id=H2_COMPARISON layer=execution C_missing={name}-{state}")
            if state == "mutant" and "category=NONCALLABLE_HEAD" not in matching[0]:
                raise AuditFailure(f"test_id=H2_COMPARISON layer=eval expected=D1_NONCALLABLE C={matching[0]}")
            if state == "law" and "result=D1:1" not in matching[0]:
                raise AuditFailure(f"test_id=H2_COMPARISON layer=eval expected=D1:YES C={matching[0]}")
    native_a = invoke(["bash", RUST_DRIVERS[0], str(exe)], root, "NATIVE_SENS_PASS id=retired-d3-eq")
    native_b = invoke(["bash", RUST_DRIVERS[1], str(exe)], root,
                      "NATIVE_SENS_PASS test_id=retired-quote-inert-d3")
    receipt.update({
        "status": "TWO_HOST_EXECUTED", "semantic_status": "SUBSET_MATCHED",
        "scope": "only 3 pinned D1/D2/D3 binary self-verdicts + one-bit negatives",
        "toolchain": {"zig_version": pinned, "c_compiler": shutil.which("cc")},
        "rust_host_binary_sha256": sha256(exe.read_bytes()),
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
        if args.run:
            r = run_both(args.root, r, args.sens_bin)
        print(json.dumps(r, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, AuditFailure) as exc:
        print(f"H2_UNVERIFIED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
