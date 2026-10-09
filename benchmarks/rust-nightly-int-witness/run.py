#!/usr/bin/env python3
"""Nightly-first probe for native Rust arbitrary-width integer syntax."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_WIDTHS = (1, 2, 3, 7, 8, 9, 16)


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def rustc_command(toolchain: str) -> list[str]:
    if toolchain in {"", "current", "default"}:
        return ["rustc"]
    return ["rustup", "run", toolchain, "rustc"]


def rustc_version(toolchain: str) -> dict[str, Any]:
    result = run_command(rustc_command(toolchain) + ["--version", "--verbose"])
    return {
        "ok": result.returncode == 0,
        "command": " ".join(rustc_command(toolchain) + ["--version", "--verbose"]),
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode,
    }


def compiler_diagnostic(stderr: str) -> str | None:
    for line in stderr.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:500]
    return None


def normalize_toolchain_version(stdout: str) -> str | None:
    match = re.search(r"^release:\s*(.+)$", stdout, re.MULTILINE)
    return match.group(1).strip() if match else None


def probe_width(
    toolchain: str, width: int, emit_llvm: bool, workdir: Path
) -> dict[str, Any]:
    spelling = f"u{width}"
    source = f"""
#![allow(dead_code)]

type Probe = {spelling};

fn witness(value: Probe) -> Probe {{
    value
}}

const _: Option<Probe> = None;
""".strip()

    source_path = workdir / f"probe_{width}.rs"
    llvm_path = workdir / f"probe_{width}.ll"
    source_path.write_text(source + "\n", encoding="utf-8")

    command = rustc_command(toolchain) + [
        str(source_path),
        "--crate-name",
        f"rust_nightly_int_probe_{width}",
        "--crate-type",
        "lib",
        "-C",
        "opt-level=0",
    ]
    if emit_llvm:
        command += ["--emit", f"llvm-ir={llvm_path}"]

    result = run_command(command)
    available = result.returncode == 0

    llvm_text = None
    llvm_mentions: list[str] = []
    if available and emit_llvm and llvm_path.exists():
        llvm_text = llvm_path.read_text(encoding="utf-8")
        llvm_mentions = sorted(set(re.findall(r"\bi\d+\b", llvm_text)))

    return {
        "width": width,
        "spelling": spelling,
        "status": (
            "NATIVE_BUILTIN_AVAILABLE"
            if available
            else "NATIVE_BUILTIN_UNAVAILABLE"
        ),
        "returncode": result.returncode,
        "diagnostic": None if available else compiler_diagnostic(result.stderr),
        "llvm_ir_emitted": bool(llvm_text is not None),
        "llvm_integer_types": llvm_mentions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toolchain", default="nightly")
    parser.add_argument(
        "--width",
        action="append",
        type=int,
        dest="widths",
        help="probe one width; repeat to override the default matrix",
    )
    parser.add_argument(
        "--emit-llvm",
        action="store_true",
        help="request LLVM IR for successful native probes",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="write the complete machine-readable result to this path",
    )
    args = parser.parse_args()

    widths = tuple(args.widths) if args.widths else DEFAULT_WIDTHS
    if not widths or any(width <= 0 or width > 4096 for width in widths):
        parser.error("width must be in the range 1..4096")

    version = rustc_version(args.toolchain)
    payload: dict[str, Any] = {
        "experiment": "RUST-NIGHTLY-INT-WITNESS-1",
        "toolchain_request": args.toolchain,
        "rustc": version,
        "rustc_release": normalize_toolchain_version(version["stdout"]),
        "widths": list(widths),
        "probes": [],
        "library_control": {
            "status": "LIBRARY_EXPERIMENT_ONLY",
            "implemented": False,
        },
    }

    with tempfile.TemporaryDirectory(prefix="sens-rust-int-probe-") as temp_dir:
        if not version["ok"]:
            payload["probes"] = [
                {
                    "width": width,
                    "spelling": f"u{width}",
                    "status": "NATIVE_BUILTIN_UNAVAILABLE",
                    "returncode": version["returncode"],
                    "diagnostic": version["stderr"][:500] or version["stdout"][:500],
                    "llvm_ir_emitted": False,
                    "llvm_integer_types": [],
                }
                for width in widths
            ]
        else:
            workdir = Path(temp_dir)
            payload["probes"] = [
                probe_width(args.toolchain, width, args.emit_llvm, workdir)
                for width in widths
            ]

    output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(output, end="")
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(output, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
