#!/usr/bin/env python3
"""Manual H1 C+Zig link-closure evidence (NEVER a SENS semantic oracle).

Static mode checks the exact current source/import/build recipe. --self-test
rejects synthetic contamination. --run actually builds Zig and C, links with
an explicit map, inspects dependencies, and executes the C witness.
No CI workflow, Rust toolchain, online access, or SENS law changes.
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
BASE = "research/zig-codecs/"
C_FILE = BASE + "host-c/d3_subset.c"
HEADER = BASE + "host-c/zig_transport_v2.h"
DRIVER = BASE + "host-c/verify_d3_subset.sh"
ZIG_ABI = BASE + "transport_abi.zig"
T5 = BASE + "t5/t5.zig"
F3C = BASE + "f3c/f3c.zig"
SOURCE_PATHS = (C_FILE, HEADER, DRIVER, ZIG_ABI, T5, F3C, ".zig-version")
EXPECTED_IMPORTS = {
    ZIG_ABI: {"std", "t5/t5.zig", "f3c/f3c.zig"},
    T5: {"std"},
    F3C: {"std", "../t5/t5.zig"},
}
EXPECTED_INCLUDES = {
    "<stdint.h>", "<stddef.h>", "<stdio.h>", "<stdlib.h>",
    "<string.h>", '"zig_transport_v2.h"',
}
ZIG_RECIPE = (
    '"$zig_bin" build-lib research/zig-codecs/transport_abi.zig '
    '-O ReleaseFast -lc -fPIC "-femit-bin=$out/libsens_zig_transport.a"'
)
C_RECIPE = (
    '"$cc_bin" -std=c11 -Wall -Wextra -Werror -pedantic -O2 '
    'research/zig-codecs/host-c/d3_subset.c '
    '"$out/libsens_zig_transport.a" -lm -ldl -pthread '
    '-o "$out/sens-c-host-d3"'
)


class AuditFailure(Exception):
    pass


def require(ok: bool, label: str, detail: str) -> None:
    if not ok:
        raise AuditFailure(f"test_id={label} layer=build-dependency {detail}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def scan(data: dict[str, str]) -> dict:
    """Reject an extra build input, Zig import or C header before any build."""
    c = data[C_FILE]
    actual_includes = set(re.findall(r'(?m)^\s*#include\s+(<[^>\n]+>|"[^"\n]+")\s*$', c))
    require(actual_includes == EXPECTED_INCLUDES, "H1_C_INCLUDE_CLOSURE",
            f"expected={sorted(EXPECTED_INCLUDES)} actual={sorted(actual_includes)}")
    # Every #include must be recognized; a malformed/macro include cannot hide.
    require(len(re.findall(r'(?m)^\s*#\s*include\b', c)) == len(EXPECTED_INCLUDES),
            "H1_C_INCLUDE_CLOSURE", "additional or malformed C include")
    for path, expected in EXPECTED_IMPORTS.items():
        source = data[path]
        imports = re.findall(r'@import\("([^"\n]+)"\)', source)
        require(set(imports) == expected and len(imports) == len(expected),
                "H1_ZIG_IMPORT_CLOSURE",
                f"file={path} expected={sorted(expected)} actual={imports}")
        # Reject alternate imports/macro C imports in active source, not comments.
        active = "\n".join(line.split("//", 1)[0] for line in source.splitlines())
        require("@cImport(" not in active and
                len(re.findall(r'@import\s*\(', active)) == len(expected),
                "H1_ZIG_IMPORT_CLOSURE", f"file={path} indirect import")
    script = data[DRIVER]
    normalized = re.sub(r'\\\r?\n[ \t]*', " ", script)
    active = "\n".join(s for s in normalized.splitlines()
                       if not s.lstrip().startswith("#"))
    for cmd, expected, label in (
        ("zig_bin", ZIG_RECIPE, "H1_ZIG_BUILD_RECIPE"),
        ("cc_bin", C_RECIPE, "H1_C_LINK_RECIPE"),
    ):
        found = re.findall(r'(?m)^[ \t]*"\$' + cmd + r'" (?:build-lib|-std=c11[^\n]*)',
                           active)
        found = [x.strip() for x in found]
        if cmd == "cc_bin":
            found = [x for x in found if "-fsyntax-only" not in x]
        require(found == [expected], label,
                f"expected_one={expected!r} actual={found!r}")
    require("cargo" not in active and "rustc" not in active and
            ".rlib" not in active and "--extern" not in active and
            "-l:lib" not in active, "H1_RUST_BUILD_CONTAMINATION",
            "C build driver mentions Rust toolchain or external archive")
    require('"$out/sens-c-host-d3"' in active and
            '"$out/libsens_zig_transport.a"' in active,
            "H1_EXECUTOR_PATH", "output executable/archive not explicitly linked")
    return {
        "test_id": "H1_RUST_FREE_BUILD_RECIPE",
        "layer": "build-dependency",
        "status": "STATIC_RECIPE_VERIFIED",
        "semantics": "NOT_EVALUATED",
        "host_independence": "PENDING_ACTUAL_LINK_AND_RUN",
        "import_closure": {path: sorted(k) for path, k in EXPECTED_IMPORTS.items()},
        "source_sha256": {path: sha256(data[path].encode("utf-8"))
                          for path in SOURCE_PATHS},
    }


def synthetic_negatives(original: dict[str, str]) -> int:
    cases = (
        ("H1_C_INCLUDE_CLOSURE", C_FILE, '#include "host_value_rust.h"\n'),
        ("H1_ZIG_IMPORT_CLOSURE", ZIG_ABI, '\nconst leaked = @import("foreign.zig");\n'),
        ("H1_C_LINK_RECIPE", DRIVER, '\n"$cc_bin" -std=c11 hidden.c -o "$out/other"\n'),
        ("H1_RUST_BUILD_CONTAMINATION", DRIVER, '\ncargo build --locked\n'),
    )
    for expected, path, injected in cases:
        bad = dict(original)
        bad[path] += injected
        try:
            scan(bad)
        except AuditFailure as exc:
            require(f"test_id={expected}" in str(exc),
                    "H1_NEGATIVE_WRONG_REASON",
                    f"case={expected} actual={exc}")
        else:
            raise AuditFailure(f"test_id=H1_NEGATIVE_ACCEPTED case={expected}")
        print(f"H1_RUST_FREE_NEGATIVE_PASS test_id={expected}")
    return len(cases)


def check_result(args: list[str], *, cwd: Path, label: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          errors="replace", check=False)
    require(proc.returncode == 0, label,
            f"argv={args!r} exit={proc.returncode} "
            f"stderr={proc.stderr[-1200:]!r} stdout={proc.stdout[-500:]!r}")
    return proc


def link_and_run(root: Path, result: dict) -> dict:
    require(sys.platform.startswith("linux"), "H1_PLATFORM",
            "link map and ELF inspection currently Linux-specific")
    for tool in ("zig", "cc", "readelf"):
        require(shutil.which(tool) is not None, "H1_TOOLCHAIN",
                f"missing_tool={tool} status=UNVERIFIED")
    expected_zig = (root / ".zig-version").read_text(encoding="ascii").strip()
    version = check_result(["zig", "version"], cwd=root, label="H1_ZIG_PIN").stdout.strip()
    require(version == expected_zig, "H1_ZIG_PIN",
            f"expected={expected_zig} actual={version}")
    with tempfile.TemporaryDirectory(prefix="sens-h1-link-") as folder:
        out = Path(folder)
        archive = out / "libsens_zig_transport.a"
        exe = out / "sens-c-host-d3"
        map_file = out / "sens-c-host-d3.map"
        check_result(
            ["zig", "build-lib", ZIG_ABI, "-O", "ReleaseFast", "-lc", "-fPIC",
             f"-femit-bin={archive}"], cwd=root, label="H1_ZIG_BUILD")
        check_result(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic", "-O2",
             C_FILE, str(archive), "-lm", "-ldl", "-pthread",
             f"-Wl,-Map={map_file}", "-o", str(exe)],
            cwd=root, label="H1_C_BUILD")
        linked = map_file.read_text(encoding="utf-8", errors="replace")
        require(archive.name in linked and C_FILE.split("/")[-1] in linked,
                "H1_LINK_MAP", "missing explicit C source or Zig archive in link map")
        # No Rust-specific archives, compiler objects or .rlibs in actual map.
        forbid = re.search(r"(?i)(?:[^\s()]*\.rlib\b|(?:^|/|\\)librust[^\s/]*\.(?:a|so)\b)",
                           linked)
        require(forbid is None, "H1_RUST_ARCHIVE",
                f"link_map_contamination={forbid.group(0) if forbid else ''}")
        dynamic = check_result(["readelf", "-d", str(exe)],
                               cwd=root, label="H1_READ_ELF").stdout
        needed = re.findall(r'\(NEEDED\)\s+Shared library: \[([^\]]+)\]', dynamic)
        require(not any("rust" in x.lower() or x.endswith(".rlib") for x in needed),
                "H1_DYNAMIC_RUST", f"linked_needed={needed!r}")
        execution = check_result([str(exe)], cwd=root, label="H1_C_EXECUTE")
        for marker in ("C_D3_SUBSET_SOURCE_WITNESS_PASS",
                       "C_D3_SUBSET_PASS", "C_D3_SUBSET_NEGATIVE_PASS"):
            require(marker in execution.stdout, "H1_C_WITNESS",
                    f"expected_marker={marker} observed=missing")
        result.update({
            "status": "C_AND_ZIG_LINK_RUN_VERIFIED",
            "host_independence": "BOUNDED_LINK_CLOSURE_VERIFIED",
            "two_host_semantic_parity": "NOT_VERIFIED_BY_THIS_SCRIPT",
            "zig_version": version,
            "c_binary_sha256": sha256(exe.read_bytes()),
            "zig_archive_sha256": sha256(archive.read_bytes()),
            "link_map_sha256": sha256(map_file.read_bytes()),
            "elf_needed": needed,
            "c_stdout_sha256": sha256(execution.stdout.encode("utf-8")),
            "c_stderr_sha256": sha256(execution.stderr.encode("utf-8")),
            "limitations": "Only C+Zig link recipe, ELF and C execution; H2 requires an independent native SENS runner",
        })
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    try:
        root = args.root.resolve()
        data = {p: (root / p).read_text(encoding="utf-8") for p in SOURCE_PATHS}
        result = scan(data)
        if args.self_test:
            result["negatives_rejected"] = synthetic_negatives(data)
        if args.run:
            result = link_and_run(root, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (AuditFailure, OSError, ValueError, UnicodeError) as exc:
        print(f"H1_RUST_FREE_UNVERIFIED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
