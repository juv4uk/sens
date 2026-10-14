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
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HOST = Path("research/zig-codecs/host-c")
INPUTS = (
    HOST / "verify_d3_subset.sh", HOST / "d3_subset.c",
    HOST / "zig_transport_v2.h", Path("research/zig-codecs/transport_abi.zig"),
)


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
    if path.is_symlink() or not path.is_file():
        raise ValueError("MISSING_OR_SYMLINK_ARTIFACT: " + str(path))
    return path


def run_audit(root: Path, output: Path) -> dict:
    for tool in ("readelf", "ar", "nm"):
        if not shutil.which(tool):
            raise ValueError("MISSING_DEPENDENCY_INSPECTION_TOOL: " + tool)
    paths = {str(p): artifact(root / p) for p in INPUTS}
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
    print("H1_DEPENDENCY_SELF_TEST_PASS cases=8")


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out-dir", type=Path)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--run", action="store_true")
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    try:
        if args.self_test:
            self_test()
        if args.run:
            if args.out_dir is None:
                raise ValueError("OUT_DIR_REQUIRED_FOR_ACTUAL_ELF_INSPECTION")
            print(json.dumps(run_audit(args.root, args.out_dir), sort_keys=True))
        if not args.self_test and not args.run:
            raise ValueError("CHOOSE_SELF_TEST_OR_RUN")
        return 0
    except (ValueError, OSError, AssertionError) as exc:
        print("H1_DEPENDENCY_UNVERIFIED " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
