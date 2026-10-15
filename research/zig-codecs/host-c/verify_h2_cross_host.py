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
import posixpath
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
H1_VERIFIER = "research/zig-codecs/host-c/verify_h1_dependency_receipt.py"
RUST_DRIVERS = ("scripts/prove-retired-d3-laws.sh", "scripts/prove-retired-quote-inert.sh")
ZIG_ABI = "research/zig-codecs/transport_abi.zig"
WORDS = re.compile(rb"^[01 \t\r\n]+$")


# This pins the selected H2 source path, not every transitive Rust dependency.
# Unrelated dirty worktree files do not block the migration swarm.
H2_TRACKED_INPUTS = (
    "research/zig-codecs/host-c/verify_h2_cross_host.py",
    C_SOURCE, C_ABI_HEADER, C_DRIVER, H1_VERIFIER, ZIG_ABI,
    "research/zig-codecs/t5/t5.zig",
    "research/zig-codecs/f3c/f3c.zig",
    # Zig ABI v2 now imports E1; all transitively compiled Zig sources
    # must be part of the exact HEAD/index/worktree H2 provenance pin.
    "research/zig-codecs/transport/e1.zig",
    "research/zig-codecs/transport/e1_writer.zig",
    "research/zig-codecs/transport/fields.zig",
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


def verify_zig_import_closure(
    root: Path, tracked: tuple[str, ...], entry: str = ZIG_ABI,
) -> tuple[str, ...]:
    """Fail closed unless every local Zig import is pinned for both H2 hosts.

    This only checks mechanical source provenance, not SENS semantics or
    Rust-free linkage. Imports are resolved as repository-relative paths.
    """
    pinned = set(tracked)
    pending = [entry]
    seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        if name not in pinned:
            raise AuditFailure(
                f"test_id=H2_ZIG_IMPORT_PIN layer=provenance "
                f"missing_tracked_zig_dependency={name}")
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise AuditFailure(
                f"test_id=H2_ZIG_IMPORT_PIN layer=provenance invalid_path={name}")
        path = root
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise AuditFailure(
                    f"test_id=H2_ZIG_IMPORT_PIN layer=provenance linked_path={name}")
        if not path.is_file():
            raise AuditFailure(
                f"test_id=H2_ZIG_IMPORT_PIN layer=provenance missing_source={name}")
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise AuditFailure(
                f"test_id=H2_ZIG_IMPORT_PIN layer=provenance unreadable_source={name}") from exc
        seen.add(name)
        # A literal-only scanner must not silently declare closure when a
        # Zig module adds @import(comptime_expression). Either enumerate ALL
        # imports mechanically or fail closed; H2 has no semantic oracle here.
        imports = re.findall(r'@import\s*\(\s*"([^"]+)"\s*\)', source)
        calls = len(re.findall(r'@import\s*\(', source))
        if len(imports) != calls:
            raise AuditFailure(
                f"test_id=H2_ZIG_IMPORT_PIN layer=provenance "
                f"unresolved_import={name} literal={len(imports)} total={calls}")
        for imported in imports:
            if imported in ("std", "builtin", "root"):
                continue
            if not imported.endswith(".zig"):
                raise AuditFailure(
                    f"test_id=H2_ZIG_IMPORT_PIN layer=provenance "
                    f"unsupported_import={imported} source={name}")
            child = posixpath.normpath(posixpath.join(posixpath.dirname(name), imported))
            if child == ".." or child.startswith("../") or child.startswith("/"):
                raise AuditFailure(
                    f"test_id=H2_ZIG_IMPORT_PIN layer=provenance "
                    f"escaped_import={imported} source={name}")
            pending.append(child)
    return tuple(sorted(seen))


def zig_import_closure_self_test() -> None:
    """One positive DAG plus missing/new/dynamic imports and linked parent."""
    with tempfile.TemporaryDirectory(prefix="sens-h2-zig-import-") as tmp:
        root = Path(tmp)
        zig = root / "zig"
        (zig / "transport").mkdir(parents=True)
        (zig / "transport_abi.zig").write_text(
            'const e1 = @import("transport/e1.zig");\n',
            encoding="utf-8",
        )
        (zig / "transport" / "e1.zig").write_text(
            'const field = @import("fields.zig");\n',
            encoding="utf-8",
        )
        (zig / "transport" / "fields.zig").write_text(
            'const std = @import("std");\n',
            encoding="utf-8",
        )
        names = ("zig/transport_abi.zig", "zig/transport/e1.zig", "zig/transport/fields.zig")
        if set(verify_zig_import_closure(root, names, names[0])) != set(names):
            raise AuditFailure("test_id=H2_ZIG_IMPORT_PIN expected=complete_DAG actual=incomplete")
        try:
            verify_zig_import_closure(root, names[:-1], names[0])
        except AuditFailure as exc:
            if "missing_tracked_zig_dependency=" not in str(exc):
                raise
        else:
            raise AuditFailure("test_id=H2_ZIG_IMPORT_PIN expected=missing_pin_REJECT actual=PASS")
        # A new imported module must never be silently omitted from H2.
        (zig / "transport" / "e1.zig").write_text(
            'const next = @import("new.zig");\n',
            encoding="utf-8",
        )
        try:
            verify_zig_import_closure(root, names, names[0])
        except AuditFailure as exc:
            if "missing_tracked_zig_dependency=" not in str(exc):
                raise
        else:
            raise AuditFailure("test_id=H2_ZIG_IMPORT_PIN expected=new_import_REJECT actual=PASS")
        (zig / "transport" / "e1.zig").write_text(
            'const known = @import("fields.zig");\n'
            'const unknown = @import(module_name);\n',
            encoding="utf-8",
        )
        try:
            verify_zig_import_closure(root, names, names[0])
        except AuditFailure as exc:
            if "unresolved_import=" not in str(exc):
                raise
        else:
            raise AuditFailure(
                "test_id=H2_ZIG_IMPORT_PIN expected=dynamic_import_REJECT actual=PASS")
        (zig / "transport" / "e1.zig").write_text(
            'const field = @import("fields.zig");\n',
            encoding="utf-8",
        )
        (zig / "alias").symlink_to(zig / "transport", target_is_directory=True)
        (zig / "transport_abi.zig").write_text(
            'const e1 = @import("alias/e1.zig");\n',
            encoding="utf-8",
        )
        try:
            verify_zig_import_closure(root, names + ("zig/alias/e1.zig",), names[0])
        except AuditFailure as exc:
            if "linked_path=" not in str(exc):
                raise
        else:
            raise AuditFailure("test_id=H2_ZIG_IMPORT_PIN expected=linked_parent_REJECT actual=PASS")
    print("H2_ZIG_IMPORT_PIN_SELF_TEST_PASS: valid, missing, new, dynamic, linked-parent")


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
        relative = Path(name)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                               f"path={name} expected=relative_regular_file actual=invalid_path")
        # The leaf may be regular while a parent redirects outside the
        # checkout. Matching HEAD/index/blob bytes do NOT justify an alias.
        file = root
        for component in relative.parts:
            file = file / component
            if file.is_symlink():
                raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                                   f"path={name} expected=regular_file actual=linked_component")
        if not file.is_file():
            raise AuditFailure(f"test_id=H2_SOURCE_PIN layer=provenance "
                               f"path={name} expected=regular_file actual=missing_or_nonregular")
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
    """Five synthetic provenance cases; never a mock semantic evaluator."""
    with tempfile.TemporaryDirectory(prefix="sens-h2-pin-") as tmp:
        root = Path(tmp)
        def cmd(*args: str) -> None:
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
        cmd("init", "-q")
        path = root / "input.bits"
        path.write_bytes(b"10 001 00\n")
        nested = root / "physical" / "program.sens"
        nested.parent.mkdir()
        nested.write_bytes(bytes.fromhex("63 89 06 a1"))
        cmd("add", "input.bits", "physical/program.sens")
        cmd("-c", "user.name=H2", "-c", "user.email=h2@example.invalid",
            "commit", "-qm", "pin")
        positive = verify_git_provenance(root, ("input.bits", "physical/program.sens"))
        assert positive["tracked"]["input.bits"]["git_mode"] == "100644"
        assert positive["tracked"]["physical/program.sens"]["git_mode"] == "100644"
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
        # The tracked physical bytes and Git hashes still match through this
        # directory alias. A leaf-only symlink guard would incorrectly PASS.
        physical = root / "physical"
        physical.rename(root / "relocated")
        physical.symlink_to(root / "relocated", target_is_directory=True)
        expected_blob = subprocess.check_output(
            ["git", "rev-parse", "HEAD:physical/program.sens"],
            cwd=root, text=True,
        ).strip()
        if git_blob((physical / "program.sens").read_bytes()) != expected_blob:
            raise AuditFailure("test_id=H2_LINKED_PARENT invalid_fixture_blob")
        try:
            verify_git_provenance(root, ("physical/program.sens",))
        except AuditFailure as exc:
            if "actual=linked_component" not in str(exc):
                raise
        else:
            raise AuditFailure("test_id=H2_LINKED_PARENT expected=REJECT actual=ACCEPT")
    print("H2_GIT_SOURCE_PIN_SELF_TEST_PASS cases=5")


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
    zig_imports = verify_zig_import_closure(root, H2_TRACKED_INPUTS)
    cases = []
    for name, pos_pin, neg_pin in CASES:
        base = root / "tests" / "semantic"
        cases.append(inspect_pair(
            name, (base / f"{name}-law.bits").read_bytes(),
            (base / f"{name}-mutant.bits").read_bytes(), pos_pin, neg_pin))
    for path in (C_SOURCE, C_ABI_HEADER, C_DRIVER, H1_VERIFIER, ZIG_ABI, *RUST_DRIVERS):
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
        "zig_import_closure": zig_imports,
        "host_a": "SENS-native-via-Rust", "host_b": "Rust-free-C-through-Zig-ABI-v2",
        "cases": cases,
        "source_sha256": {p: sha256((root / p).read_bytes())
                          for p in (C_SOURCE, C_ABI_HEADER, C_DRIVER, H1_VERIFIER, ZIG_ABI, *RUST_DRIVERS)},
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



# The C host is built and checked by H1, not independently authenticated by
# seeing a valid C program verdict. The exact SHA of its already-executed
# binary must agree with the ELF/AR verifier and the Git-pinned source bytes.
H1_D10 = ("C_ZIG_D10_COORDINATE_ONLY_PASS host=C abi=2 "
          "d10_golden=3 ordinary_positive=2 negative=6 "
          "d10_callable=NO semantic_authority=SENS")
H1_VERIFIED = ("H1_C_HOST_STDOUT_RECEIPT_PASS d10_golden=3 d3_laws=3 "
               "d3_negative=3 negative=6 one_bit_mutations=3 ordinary_positive=2")
H1_READY = ("C_D3_SUBSET_H1_SOURCE_READY runtime_subset=D1-D3 "
            "dependency_receipt=INSPECTED_NO_RUST_MARKERS "
            "full_static_dependency_closure=NOT_VERIFIED "
            "cross_host_parity=NOT_VERIFIED semantic_authority=SENS")


def verify_h1_execution_receipt(stdout: str, trusted_sources: dict[str, str]) -> dict:
    """Bind the actual C process, H1 source checker and ELF audit to H2.

    This is mechanical executable/source provenance, NOT callable admission,
    an extra language evaluator, or a substitute for running both H2 hosts.
    """
    lines = stdout.splitlines()
    for label, marker in (("D10", H1_D10), ("H1_STDOUT", H1_VERIFIED),
                          ("H1_FINAL", H1_READY)):
        if lines.count(marker) != 1:
            raise AuditFailure(
                f"test_id=H2_H1_CHAIN layer=transport "
                f"marker={label} expected=one_exact actual={lines.count(marker)}")
    if not (lines.index(H1_D10) < lines.index(H1_VERIFIED) < lines.index(H1_READY)):
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance actual=out_of_order")

    # H1 --run prints exactly one JSON receipt, after verifying ELF, AR, NM
    # and the actual Zig build sources, including its own verifier script.
    json_lines = [line for line in lines if line.startswith("{")]
    if len(json_lines) != 1:
        raise AuditFailure(f"test_id=H2_H1_CHAIN layer=provenance "
                           f"expected=one_H1_ELF_JSON actual={len(json_lines)}")
    try:
        audit = json.loads(json_lines[0])
    except (ValueError, TypeError) as exc:
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance malformed_H1_JSON") from exc
    if (not isinstance(audit, dict) or
        audit.get("test_id") != "H1_C_ZIG_ELF_DEPENDENCY_RECEIPT" or
        audit.get("status") != "INSPECTED_NO_RUST_MARKERS" or
        audit.get("semantic_conformance_proven") is not False or
        audit.get("full_static_dependency_closure_proven") is not False):
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance invalid_H1_ELF_status")

    binary_lines = [re.fullmatch(
        r"C_D3_SUBSET_RECEIPT zig=(\S+) c_binary_sha256=([0-9a-f]{64})", line)
        for line in lines if line.startswith("C_D3_SUBSET_RECEIPT")]
    if len(binary_lines) != 1 or binary_lines[0] is None:
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance "
                           "expected=one_exact_C_binary_SHA")
    binary_sha = binary_lines[0].group(2)
    archive_sha = audit.get("zig_archive_sha256")
    if (audit.get("binary_sha256") != binary_sha or
            not isinstance(archive_sha, str) or
            re.fullmatch(r"[0-9a-f]{64}", archive_sha) is None):
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance "
                           "actual=C_binary_or_Zig_archive_SHA_mismatch")

    sources = audit.get("source_sha256")
    if not isinstance(sources, dict):
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance missing_H1_source_map")
    for path in (C_SOURCE, C_ABI_HEADER, C_DRIVER, H1_VERIFIER, ZIG_ABI):
        expected = trusted_sources.get(path)
        if (not isinstance(expected, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected) is None or
            sources.get(path) != expected):
            raise AuditFailure(
                f"test_id=H2_H1_CHAIN layer=provenance "
                f"source={path} expected_sha256={expected} actual={sources.get(path)}")
    if not (lines.index(H1_VERIFIED) < lines.index(json_lines[0]) <
            next(i for i, line in enumerate(lines) if line.startswith("C_D3_SUBSET_RECEIPT")) <
            lines.index(H1_READY)):
        raise AuditFailure("test_id=H2_H1_CHAIN layer=provenance "
                           "actual=H1_ELF_chain_out_of_order")
    return {
        "c_binary_sha256": binary_sha,
        "zig_archive_sha256": archive_sha,
        "h1_source_sha256": {path: sources[path] for path in
                             (C_SOURCE, C_ABI_HEADER, C_DRIVER, H1_VERIFIER, ZIG_ABI)},
        "h1_elf_status": audit["status"],
        "d10_abi_physical": "COORDINATE_ONLY",
    }


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
    c_h1: list[dict] = []
    c_physical: dict[str, dict] = {}
    def check_c_verdicts(stdout: str) -> None:
        # These are observations from the C process, not Python-authored SENS laws.
        h1 = verify_h1_execution_receipt(stdout, receipt["source_sha256"])
        c_h1.append(h1)
        c_binary_digest.append(h1["c_binary_sha256"])
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
        "h1_zig_c_elf_provenance": c_h1[0],
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
            zig_import_closure_self_test()
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
