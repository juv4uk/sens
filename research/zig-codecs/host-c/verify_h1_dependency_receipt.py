#!/usr/bin/env python3
"""Manual H1 ELF/link-input receipt; never a SENS semantic oracle.

Build first, without Cargo/Rust: SENS_C_HOST_OUT_DIR=DIR bash
research/zig-codecs/host-c/verify_d3_subset.sh
Then inspect: python3 research/zig-codecs/host-c/verify_h1_dependency_receipt.py
--out-dir DIR --run
"""
import argparse
import hashlib
import json
import os
import posixpath
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
HOST = Path("research/zig-codecs/host-c")
ZIG_ROOT = "research/zig-codecs"
ZIG_ENTRY = f"{ZIG_ROOT}/transport_abi.zig"
INPUTS = (
    HOST / "verify_d3_subset.sh", HOST / "d3_subset.c",
    HOST / "zig_transport_v2.h", Path("research/zig-codecs/transport_abi.zig"),
)


def zig_local_sources(root: Path, entry: str = ZIG_ENTRY) -> dict[str, Path]:
    """Record every physical Zig source contributing to the H1 ABI build.

    Host-independent byte-source evidence only. This does not establish which
    object files the linker included, nor grant Zig semantic authority.
    """
    pending = [entry]
    found: dict[str, Path] = {}
    while pending:
        name = pending.pop()
        if name in found:
            continue
        if not name.startswith(ZIG_ROOT + "/") or (
                name.startswith("/") or ".." in Path(name).parts):
            raise ValueError(f"H1_ZIG_IMPORT_ESCAPE: {name}")
        source = root
        for component in Path(name).parts:
            source = source / component
            if source.is_symlink():
                raise ValueError(f"H1_ZIG_LINKED_SOURCE: {name}")
        if not source.is_file():
            raise ValueError(f"H1_ZIG_MISSING_SOURCE: {name}")
        try:
            content = source.read_text(encoding="utf-8")
        except (UnicodeError, OSError) as exc:
            raise ValueError(f"H1_ZIG_UNREADABLE_SOURCE: {name}") from exc
        found[name] = source
        imports = re.findall(r'@import\s*\(\s*"([^"]+)"\s*\)', content)
        if len(imports) != len(re.findall(r'@import\s*\(', content)):
            raise ValueError(f"H1_ZIG_UNRESOLVED_IMPORT: {name}")
        for imported in imports:
            if imported in ("std", "builtin", "root"):
                continue
            if not imported.endswith(".zig"):
                raise ValueError(f"H1_ZIG_NONFILE_IMPORT: {name} -> {imported}")
            child = posixpath.normpath(
                posixpath.join(posixpath.dirname(name), imported))
            if not child.startswith(ZIG_ROOT + "/"):
                raise ValueError(f"H1_ZIG_IMPORT_ESCAPE: {name} -> {imported}")
            pending.append(child)
    return dict(sorted(found.items()))


def zig_source_self_test() -> None:
    """Real files: positive import chain and three fail-closed negatives."""
    with TemporaryDirectory(prefix="sens-h1-zig-deps-") as temp:
        root = Path(temp)
        directory = root / ZIG_ROOT
        (directory / "transport").mkdir(parents=True)
        entry = directory / "transport_abi.zig"
        field = directory / "transport" / "fields.zig"
        entry.write_text('const x = @import("transport/fields.zig");\n',
                         encoding="utf-8")
        field.write_text('const std = @import("std");\n', encoding="utf-8")
        if set(zig_local_sources(root)) != {
            ZIG_ENTRY, f"{ZIG_ROOT}/transport/fields.zig"
        }:
            raise AssertionError("H1_ZIG_IMPORT positive closure incomplete")
        entry.write_text('const x = @import("transport/absent.zig");\n',
                         encoding="utf-8")
        try:
            zig_local_sources(root)
        except ValueError as exc:
            assert "H1_ZIG_MISSING_SOURCE" in str(exc)
        else:
            raise AssertionError("H1_ZIG_IMPORT missing dependency accepted")
        alias = directory / "alias"
        alias.symlink_to(directory / "transport", target_is_directory=True)
        entry.write_text('const x = @import("alias/fields.zig");\n',
                         encoding="utf-8")
        try:
            zig_local_sources(root)
        except ValueError as exc:
            assert "H1_ZIG_LINKED_SOURCE" in str(exc)
        else:
            raise AssertionError("H1_ZIG_IMPORT linked directory accepted")
        entry.write_text('const x = @import("../../../foreign.zig");\n',
                         encoding="utf-8")
        try:
            zig_local_sources(root)
        except ValueError as exc:
            assert "H1_ZIG_IMPORT_ESCAPE" in str(exc)
        else:
            raise AssertionError("H1_ZIG_IMPORT outside repository accepted")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rust_marker(name: str) -> bool:
    """Recognize Rust-named artifacts/symbols, not ordinary C++ libstdc++."""
    basename = name.replace("\\", "/").rsplit("/", 1)[-1]
    return bool(
        basename.endswith(".rlib")
        or re.search(r"(?:^|_)(?:__rust_|rust_eh_personality|rust_alloc)", basename)
        or re.fullmatch(r"lib(?:rust[^/]*|std-[0-9a-f]+|core-[0-9a-f]+|alloc-[0-9a-f]+)\.(?:a|so(?:\.[0-9.]+)?|dylib)", basename)
        or re.match(r"_?RN[A-Za-z0-9_]+$", basename)
    )


def dynamic_needed(stdout: str) -> list[str]:
    needed = []
    for line in stdout.splitlines():
        if "(NEEDED)" in line:
            match = re.search(r"Shared library: \[([^\]]+)\]", line)
            if not match:
                raise ValueError("BAD_ELF_NEEDED_ENTRY: " + line.strip())
            needed.append(match.group(1))
    if not needed and not ("Dynamic section" in stdout or
                           "There is no dynamic section" in stdout):
        raise ValueError("UNRECOGNIZED_ELF_DYNAMIC_OUTPUT")
    return needed


def inspect_recipe(source: str) -> None:
    active = "\n".join(line for line in source.splitlines()
                       if line.strip() and not line.lstrip().startswith("#"))
    expected = (
        'build-lib research/zig-codecs/transport_abi.zig',
        'research/zig-codecs/host-c/d3_subset.c',
        '"$out/libsens_zig_transport.a"',
        '"$out/sens-c-host-d3"',
    )
    for part in expected:
        if part not in active:
            raise ValueError("H1_BUILD_RECIPE_MISSING: " + part)
    if re.search(r"\b(?:cargo|rustc)\b|\.rlib\b", active):
        raise ValueError("RUST_TOOL_IN_H1_BUILD_RECIPE")


def command(argv: list[str]) -> str:
    env = {**os.environ, "LC_ALL": "C"}
    run = subprocess.run(argv, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", env=env, check=False)
    if run.returncode:
        raise ValueError(f"TOOL_FAILED argv={argv!r} exit={run.returncode} stderr={run.stderr[-300:]!r}")
    return run.stdout


def artifact(path: Path) -> Path:
    """Accept only a regular physical file with NO symlink path component.

    ELF/archive hashes must refer to the selected binary's actual path:
    checking only the leaf permits a symlinked build/output directory.
    """
    if ".." in path.parts:
        raise ValueError("NONCANONICAL_ARTIFACT_PATH: " + str(path))
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if current.is_symlink():
            raise ValueError("LINKED_ARTIFACT_COMPONENT: " + str(current))
    if not absolute.is_file():
        raise ValueError("MISSING_OR_SYMLINK_ARTIFACT: " + str(path))
    return path


def artifact_path_self_test() -> None:
    """Same bytes through an alias directory must NEVER authenticate H1."""
    with TemporaryDirectory(prefix="sens-h1-physical-path-") as tmp:
        root = Path(tmp)
        physical = root / "physical"
        physical.mkdir()
        binary = physical / "sens-c-host-d3"
        archive = physical / "libsens_zig_transport.a"
        binary.write_bytes(bytes.fromhex("63 89 06 a1"))
        archive.write_bytes(bytes.fromhex("f3 40 60"))
        assert artifact(binary) == binary
        assert artifact(archive) == archive

        alias = root / "alias"
        alias.symlink_to(physical, target_is_directory=True)
        assert (alias / binary.name).read_bytes() == binary.read_bytes()
        for name in (binary.name, archive.name):
            try:
                artifact(alias / name)
            except ValueError as exc:
                if "LINKED_ARTIFACT_COMPONENT" not in str(exc):
                    raise
            else:
                raise AssertionError("H1_LINKED_ARTIFACT_PARENT accepted: " + name)

        leaf = root / "binary-alias"
        leaf.symlink_to(binary)
        try:
            artifact(leaf)
        except ValueError as exc:
            if "LINKED_ARTIFACT_COMPONENT" not in str(exc):
                raise
        else:
            raise AssertionError("H1_LINKED_ARTIFACT_LEAF accepted")

        try:
            artifact(physical / ".." / "physical" / binary.name)
        except ValueError as exc:
            if "NONCANONICAL_ARTIFACT_PATH" not in str(exc):
                raise
        else:
            raise AssertionError("H1_NONCANONICAL_ARTIFACT_PATH accepted")

        try:
            artifact(physical / "missing-archive.a")
        except ValueError as exc:
            if "MISSING_OR_SYMLINK_ARTIFACT" not in str(exc):
                raise
        else:
            raise AssertionError("H1_MISSING_ARTIFACT accepted")




def run_audit(root: Path, output: Path) -> dict:
    for tool in ("readelf", "ar", "nm"):
        if not shutil.which(tool):
            raise ValueError("MISSING_DEPENDENCY_INSPECTION_TOOL: " + tool)
    paths = {str(p): artifact(root / p) for p in INPUTS}
    # Hash the ENTIRE local Zig compilation source closure, not only the
    # transport_abi.zig entrypoint. The C/Zig linker audit remains separate.
    paths.update(zig_local_sources(root))
    inspect_recipe(paths[str(INPUTS[0])].read_text(encoding="utf-8"))
    executable = artifact(output / "sens-c-host-d3")
    archive = artifact(output / "libsens_zig_transport.a")
    required = dynamic_needed(command(["readelf", "--wide", "--dynamic", str(executable)]))
    members = [line for line in command(["ar", "t", str(archive)]).splitlines() if line.strip()]
    if not members:
        raise ValueError("EMPTY_ZIG_STATIC_ARCHIVE")
    undefined = [line.split()[-1] for line in command(["nm", "-u", str(executable)]).splitlines()
                 if line.split()]
    suspect = [f"needed:{x}" for x in required if rust_marker(x)]
    suspect += [f"archive_member:{x}" for x in members if rust_marker(x)]
    suspect += [f"undefined:{x}" for x in undefined if rust_marker(x)]
    if suspect:
        raise ValueError("RUST_MARKER_IN_LINK_INSPECTION: " + ",".join(suspect[:12]))
    return {
        "test_id": "H1_C_ZIG_ELF_DEPENDENCY_RECEIPT",
        "status": "INSPECTED_NO_RUST_MARKERS",
        "layer": "host-dependency-provenance",
        "abi": "Zig-transport-v2-BE3",
        "binary_sha256": digest(executable),
        "zig_archive_sha256": digest(archive),
        "source_sha256": {k: digest(v) for k, v in paths.items()},
        "elf_dt_needed": required,
        "zig_archive_member_count": len(members),
        "undefined_symbol_count": len(undefined),
        "checked": "explicit H1 build recipe, ELF DT_NEEDED, Zig archive members, unresolved ELF symbols",
        "full_static_dependency_closure_proven": False,
        "semantic_conformance_proven": False,
        "limits": "Static linked objects and private compiler inputs require independent linker-map/toolchain provenance; name scanning alone cannot prove full Rust absence. H2 semantic parity is separate.",
        "reproduce": "SENS_C_HOST_OUT_DIR=DIR bash research/zig-codecs/host-c/verify_d3_subset.sh && python3 research/zig-codecs/host-c/verify_h1_dependency_receipt.py --out-dir DIR --run",
    }



C_D10_RECEIPT = (
    "C_ZIG_D10_COORDINATE_ONLY_PASS host=C abi=2 "
    "d10_golden=3 ordinary_positive=2 negative=6 "
    "d10_callable=NO semantic_authority=SENS"
)
C_D3_FINAL_RECEIPT = (
    "C_D3_SUBSET_SOURCE_WITNESS_PASS tests=6 host=C rust_linked=false "
    "semantic_scope=D1+D2+D3 cross_host_parity=NOT_VERIFIED"
)
C_D3_FIXTURES = ("retired-d3-cond", "retired-d3-eq", "retired-quote-inert-d3")


def verify_c_host_stdout(stdout: str) -> dict:
    """Fail closed on a no-op C binary, skipped D10 proof or partial fixtures.

    Only verifies the real Zig-linked C process's exact stdout transcript.
    Source validity, ELF/AR provenance and H2 SENS semantics remain separate.
    """
    lines = stdout.splitlines()
    if not lines or lines[0] != C_D10_RECEIPT or lines[-1] != C_D3_FINAL_RECEIPT:
        raise ValueError("H1_C_HOST_RECEIPT missing_first_D10_or_final_D3")
    expected_line_count = 2 + len(C_D3_FIXTURES) * 5
    if len(lines) != expected_line_count:
        raise ValueError(
            f"H1_C_HOST_RECEIPT unexpected_line_count "
            f"expected={expected_line_count} actual={len(lines)}")
    at = 1
    counts = {"d10_golden": 3, "ordinary_positive": 2, "negative": 6,
              "d3_laws": 0, "d3_negative": 0, "one_bit_mutations": 0}
    # The C executable publishes each law + mutant in order, then all
    # one-bit mutation receipts. This is transcript validation, not an oracle.
    for name in C_D3_FIXTURES:
        law = f"tests/semantic/{name}-law.bits"
        mutant = f"tests/semantic/{name}-mutant.bits"
        for fixture, role in ((law, "law"), (mutant, "mutant")):
            pattern = rf"C_D3_SUBSET_T5 source={re.escape(fixture)} bytes=([1-9][0-9]*) hex=([0-9a-f]+)"
            match = re.fullmatch(pattern, lines[at])
            if match is None or len(match.group(2)) != 2 * int(match.group(1)):
                raise ValueError(
                    f"H1_C_HOST_RECEIPT missing_or_malformed_physical "
                    f"path={fixture} line={at}")
            byte_count = int(match.group(1))
            at += 1
            if role == "law":
                expected = (f"C_D3_SUBSET_PASS source={fixture} "
                            f"physical_bytes={byte_count} "
                            r"exact_be3_bytes=([1-9][0-9]*) result=D1:1")
                law_match = re.fullmatch(expected, lines[at])
                if law_match is None or int(law_match.group(1)) % 3 != 0:
                    raise ValueError(f"H1_C_HOST_RECEIPT law_missing_or_inexact={fixture}")
                counts["d3_laws"] += 1
            else:
                if lines[at] != (f"C_D3_SUBSET_NEGATIVE_PASS source={fixture} "
                                 "category=NONCALLABLE_HEAD"):
                    raise ValueError(f"H1_C_HOST_RECEIPT negative_missing={fixture}")
                counts["d3_negative"] += 1
            at += 1
    for name in C_D3_FIXTURES:
        law = f"tests/semantic/{name}-law.bits"
        mutant = f"tests/semantic/{name}-mutant.bits"
        expected = (f"C_D3_SUBSET_MUTATION_PASS source={law} "
                    f"mutant={mutant} exact_changed_bits=1")
        if lines[at] != expected:
            raise ValueError(f"H1_C_HOST_RECEIPT one_bit_mutation_missing={name}")
        at += 1
        counts["one_bit_mutations"] += 1
    if at != len(lines) - 1:
        raise ValueError("H1_C_HOST_RECEIPT trailing_or_missing_evidence")
    return counts


def c_host_stdout_self_test() -> None:
    """Receipt mutation probes only; not a fake runtime or semantic GO."""
    lines = [C_D10_RECEIPT]
    for name in C_D3_FIXTURES:
        for role in ("law", "mutant"):
            fixture = f"tests/semantic/{name}-{role}.bits"
            lines.append(f"C_D3_SUBSET_T5 source={fixture} bytes=2 hex=a135")
            if role == "law":
                lines.append(f"C_D3_SUBSET_PASS source={fixture} "
                             "physical_bytes=2 exact_be3_bytes=9 result=D1:1")
            else:
                lines.append(f"C_D3_SUBSET_NEGATIVE_PASS source={fixture} "
                             "category=NONCALLABLE_HEAD")
    for name in C_D3_FIXTURES:
        lines.append(
            f"C_D3_SUBSET_MUTATION_PASS "
            f"source=tests/semantic/{name}-law.bits "
            f"mutant=tests/semantic/{name}-mutant.bits exact_changed_bits=1")
    lines.append(C_D3_FINAL_RECEIPT)
    assert verify_c_host_stdout("\n".join(lines))["d3_negative"] == 3
    mutants = (
        lines[1:],                            # old host without D10
        lines[:-1],                           # early process success
        [*lines, C_D3_FINAL_RECEIPT],        # duplicate receipt
        [lines[0].replace("d10_callable=NO", "d10_callable=YES"), *lines[1:]],
        [*lines[:2], lines[2].replace("result=D1:1", "result=D1:0"), *lines[3:]],
        [*lines[:3], lines[3].replace("bytes=2", "bytes=3"), *lines[4:]],
        [*lines[:4], *lines[5:]],             # missing negative witness
        [*lines[:4], lines[4], *lines[4:]],  # duplicate source witness
        [*lines[:-2], lines[-2].replace("exact_changed_bits=1", "exact_changed_bits=0"), lines[-1]],
        [*lines[:-1], "C_D3_SUBSET_FAIL layer=transport", lines[-1]],
    )
    for index, mutant in enumerate(mutants):
        try:
            verify_c_host_stdout("\n".join(mutant))
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"H1_C_HOST_RECEIPT_SELF_TEST accepted mutant={index}")
    print(f"H1_C_HOST_RECEIPT_SELF_TEST_PASS negatives={len(mutants)}")


def self_test() -> None:
    sample = "Dynamic section at offset 0x3000 contains 2 entries:\n 0x1 (NEEDED) Shared library: [libc.so.6]"
    assert dynamic_needed(sample) == ["libc.so.6"]
    assert dynamic_needed("There is no dynamic section in this file.") == []
    assert rust_marker("libstd-1234abcd.so")
    assert rust_marker("libcore-1234abcd.rlib")
    assert rust_marker("rust_eh_personality")
    assert not rust_marker("libstdc++.so.6")
    try:
        dynamic_needed("0x1 (NEEDED) invalid-record")
    except ValueError as exc:
        assert "BAD_ELF_NEEDED_ENTRY" in str(exc)
    else:
        raise AssertionError("malformed DT_NEEDED must fail")
    try:
        inspect_recipe('cargo build; rustc;')
    except ValueError as exc:
        assert "H1_BUILD_RECIPE_MISSING" in str(exc)
    else:
        raise AssertionError("Rust-only recipe must fail")
    zig_source_self_test()
    artifact_path_self_test()
    c_host_stdout_self_test()
    print("H1_PHYSICAL_ARTIFACT_SELF_TEST_PASS")
    print("H1_DEPENDENCY_SELF_TEST_PASS cases=12 (including Zig closure)")


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out-dir", type=Path)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--run", action="store_true")
    cli.add_argument("--self-test", action="store_true")
    cli.add_argument("--verify-host-stdout", action="store_true",
                     help="validate real Zig-linked C process stdout from stdin")
    args = cli.parse_args()
    try:
        if args.self_test:
            self_test()
        if args.verify_host_stdout:
            receipt = verify_c_host_stdout(sys.stdin.read())
            print("H1_C_HOST_STDOUT_RECEIPT_PASS " +
                  " ".join(f"{k}={v}" for k, v in sorted(receipt.items())))
        if args.run:
            if args.out_dir is None:
                raise ValueError("OUT_DIR_REQUIRED_FOR_ACTUAL_ELF_INSPECTION")
            print(json.dumps(run_audit(args.root, args.out_dir), sort_keys=True))
        if not args.self_test and not args.run and not args.verify_host_stdout:
            raise ValueError("CHOOSE_SELF_TEST_OR_RUN_OR_VERIFY_HOST_STDOUT")
        return 0
    except (ValueError, OSError, AssertionError) as exc:
        print("H1_DEPENDENCY_UNVERIFIED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
