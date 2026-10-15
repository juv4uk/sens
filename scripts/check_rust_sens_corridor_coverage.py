#!/usr/bin/env python3
"""Coverage guard: EVERY Rust<->SENS host must cross the sterile Zig corridor (#5777).

The `sens` crate legitimately owns the physical codecs (binary_framing,
ternary_transport, frame3_small). Any OTHER crate that reaches SENS physical
bytes must do so through the sterile Zig corridor (`zig_transport` / `sens_zig_*`),
never through a private in-crate codec path.

Fail-closed: a host that touches the physical codec API but does NOT reference the
corridor must be registered in the coverage registry with a reason + issue, else
the guard fails. A new bypass cannot land silently.

Registry: research/zig-codecs/corridor_host_coverage.json
Exit 0 = COVERAGE_OK; exit 1 = COVERAGE_BLOCKED with reasons.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CODEC_OWNER = "crates/sens"
REGISTRY = "research/zig-codecs/corridor_host_coverage.json"

# Host-side calls into the physical codec surface.
CODEC_API = re.compile(
    r"\b(encode_binary_frame|decode_binary_frame|"
    r"decode_ternary_words|encode_ternary_words|"
    r"ternary_transport|frame3_small|PhysicalT5Program)\b"
)
# Anything that proves the host goes through the corridor.
CORRIDOR_API = re.compile(r"\b(zig_transport|sens_zig_[a-z0-9_]+)\b")


def _crate_sources(crate: Path) -> list[Path]:
    src = crate / "src"
    return sorted(p for p in src.rglob("*.rs") if p.is_file()) if src.is_dir() else []


def check(root: Path) -> list[str]:
    problems: list[str] = []
    registry_path = root / REGISTRY
    if not registry_path.exists():
        problems.append(f"registry `{REGISTRY}` is missing")
        return problems
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    exempt = {entry["crate"]: entry for entry in registry.get("exemptions", [])}

    crates_dir = root / "crates"
    if not crates_dir.is_dir():
        problems.append("no `crates/` directory")
        return problems

    for crate in sorted(p for p in crates_dir.iterdir() if p.is_dir()):
        rel = f"crates/{crate.name}"
        if rel == CODEC_OWNER:
            continue  # the codec owner is allowed to own the physical codec
        sources = _crate_sources(crate)
        touches_codec = any(CODEC_API.search(p.read_text(encoding="utf-8", errors="replace")) for p in sources)
        if not touches_codec:
            continue
        on_corridor = any(CORRIDOR_API.search(p.read_text(encoding="utf-8", errors="replace")) for p in sources)
        if on_corridor:
            continue
        entry = exempt.get(rel)
        if entry is None:
            problems.append(
                f"host `{rel}` reaches SENS physical bytes without the Zig corridor "
                "and is not registered in corridor_host_coverage.json"
            )
        elif not entry.get("reason") or not entry.get("issue"):
            problems.append(f"host `{rel}` exemption lacks a reason/issue (silent bypass)")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except FileNotFoundError as exc:
        print(f"COVERAGE_BLOCKED missing file: {exc}", flush=True)
        return 1
    if problems:
        print("COVERAGE_BLOCKED a Rust<->SENS host bypasses the sterile Zig corridor:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "COVERAGE_OK every Rust<->SENS host either crosses the Zig corridor "
        "or is a registered, reasoned exemption",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
