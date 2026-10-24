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
REGISTRY_SCHEMA = "sens-rust-sens-corridor-coverage/v1"
CRATE_KEY = re.compile(r"crates/[a-z][a-z0-9_-]*\Z")

# Host-side calls into the physical codec surface.
CODEC_API = re.compile(
    r"\b(encode_binary_frame|decode_binary_frame|"
    r"decode_ternary_words|encode_ternary_words|"
    r"ternary_transport|frame3_small|PhysicalT5Program)\b"
)
# A bare module name is not evidence of using the physical ABI. Require an
# actual call; comments, strings and char literals are stripped below.
CORRIDOR_API = re.compile(
    r"\b(?:zig_transport::[A-Za-z_][A-Za-z0-9_]*|sens_zig_[a-z0-9_]+)\s*\("
)
RAW_STRING = re.compile(r'(?:br|rb|r)(?P<hashes>#{0,16})"')
CHAR_LITERAL = re.compile(r"'(?:\\.|[^'\\\n])'")


def _live_rust(source: str) -> str:
    """Erase comments and literals before matching physical-codec routes.

    Handles Rust raw strings and nested block comments; this remains a
    structural guard, not a Rust parser or independent SENS oracle.
    """
    active: list[str] = []
    i = 0
    size = len(source)
    while i < size:
        if source.startswith("//", i):
            stop = source.find("\n", i + 2)
            i = stop if stop >= 0 else size
            active.append(" ")
            continue
        if source.startswith("/*", i):
            i += 2
            depth = 1
            while i < size and depth:
                if source.startswith("/*", i):
                    depth += 1
                    i += 2
                elif source.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            active.append(" ")
            continue
        raw = RAW_STRING.match(source, i)
        if raw:
            ending = '"' + raw.group("hashes")
            stop = source.find(ending, raw.end())
            i = stop + len(ending) if stop >= 0 else size
            active.append(" ")
            continue
        if source[i] == '"':
            i += 1
            while i < size:
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            active.append(" ")
            continue
        char = CHAR_LITERAL.match(source, i)
        if char:
            i = char.end()
            active.append(" ")
            continue
        active.append(source[i])
        i += 1
    return "".join(active)


CFG_ATTR = re.compile(r"#\s*\[\s*cfg\s*\(")


def _cfg_requires_test(expression: str) -> bool:
    """Prove that a cfg predicate implies `test` in every active branch.

    `all` requires test when any operand requires it; `any` requires it
    only when every operand does. Unknown predicates stay production-visible.
    """
    expression = expression.strip()
    if expression == "test":
        return True
    compound = re.match(r"^(all|any)\s*\(", expression)
    if compound is not None and expression.endswith(")"):
        operator = compound.group(1)
        inner = expression[compound.end():-1]
        operands: list[str] = []
        depth = 0
        split = 0
        for index, char in enumerate(inner):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == "," and depth == 0:
                operands.append(inner[split:index])
                split = index + 1
        operands.append(inner[split:])
        required = [_cfg_requires_test(value) for value in operands if value.strip()]
        return any(required) if operator == "all" else bool(required) and all(required)
    return False


def _production_rust(active: str) -> str:
    """Erase all Rust cfg items proven test-only, preserving later items.

    Do not let a test-only Zig call attest production codec access. Ambiguous
    item boundaries fail closed instead of legitimizing a transport bypass.
    """
    output = list(active)
    position = 0
    while (match := CFG_ATTR.search(active, position)) is not None:
        start = match.start()
        scan = match.end()
        depth = 1
        while scan < len(active) and depth:
            if active[scan] == "(":
                depth += 1
            elif active[scan] == ")":
                depth -= 1
            scan += 1
        if depth:
            raise ValueError("unterminated cfg predicate")
        expression = active[match.end():scan - 1]
        close = scan
        while close < len(active) and active[close].isspace():
            close += 1
        if close >= len(active) or active[close] != "]":
            raise ValueError("cfg attribute has no closing bracket")
        position = close + 1
        if not _cfg_requires_test(expression):
            continue
        item = position
        # Additional attributes may decorate the same test-only item.
        while True:
            while item < len(active) and active[item].isspace():
                item += 1
            attribute = re.match(r"#\s*\[", active[item:])
            if attribute is None:
                break
            attr_depth = 1
            item += attribute.end()
            while item < len(active) and attr_depth:
                if active[item] == "[":
                    attr_depth += 1
                elif active[item] == "]":
                    attr_depth -= 1
                item += 1
            if attr_depth:
                raise ValueError("unterminated test-only attribute")
        if item >= len(active):
            raise ValueError("test-only cfg has no Rust item")
        brace = active.find("{", item)
        semicolon = active.find(";", item)
        if semicolon >= 0 and (brace < 0 or semicolon < brace):
            end = semicolon + 1
        elif brace >= 0:
            brace_depth = 1
            end = brace + 1
            while end < len(active) and brace_depth:
                if active[end] == "{":
                    brace_depth += 1
                elif active[end] == "}":
                    brace_depth -= 1
                end += 1
            if brace_depth:
                raise ValueError("unterminated cfg Rust item")
        else:
            raise ValueError("test-only cfg Rust item has no terminator")
        output[start:end] = " " * (end - start)
        position = end
    return "".join(output)


def _crate_sources(crate: Path) -> list[Path]:
    src = crate / "src"
    return sorted(p for p in src.rglob("*.rs") if p.is_file()) if src.is_dir() else []


def check(root: Path) -> list[str]:
    problems: list[str] = []
    registry_path = root / REGISTRY
    if not registry_path.is_file() or registry_path.is_symlink():
        return [f"registry `{REGISTRY}` is missing or not a regular file"]
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"registry `{REGISTRY}` invalid JSON: {type(exc).__name__}: {exc}"]
    if not isinstance(registry, dict):
        return [f"registry `{REGISTRY}` must be a JSON object"]
    if registry.get("schema") != REGISTRY_SCHEMA:
        problems.append(
            f"registry schema mismatch: expected={REGISTRY_SCHEMA!r} "
            f"actual={registry.get('schema')!r}"
        )
    if registry.get("codec_owner") != CODEC_OWNER:
        problems.append(
            f"registry codec_owner mismatch: expected={CODEC_OWNER!r} "
            f"actual={registry.get('codec_owner')!r}"
        )
    entries = registry.get("exemptions")
    if not isinstance(entries, list):
        problems.append("registry exemptions must be a JSON list")
        return problems
    exempt: dict[str, dict] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            problems.append(f"registry exemptions[{index}] must be an object")
            continue
        name = entry.get("crate")
        if not isinstance(name, str) or CRATE_KEY.fullmatch(name) is None:
            problems.append(f"registry exemptions[{index}] invalid crate path={name!r}")
            continue
        if name == CODEC_OWNER:
            problems.append(f"registry exemptions[{index}] cannot exempt codec owner")
            continue
        if name in exempt:
            problems.append(f"registry duplicate exemption for {name}")
            continue
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            problems.append(f"registry exemption {name} lacks nonblank reason")
        issue = entry.get("issue")
        if type(issue) is not int or issue <= 0:
            problems.append(f"registry exemption {name} requires a positive GitHub issue number")
        exempt[name] = entry

    crates_dir = root / "crates"
    if not crates_dir.is_dir() or crates_dir.is_symlink():
        problems.append("no trustworthy `crates/` directory (missing or symlinked)")
        return problems

    used_exemptions: set[str] = set()
    # A symlink can make rglob omit a Rust subtree or follow source bytes
    # outside the checkout. Neither outcome proves that all SENS edges were
    # inventoried; no host (including the codec owner) can waive this gate.
    for crate in sorted(p for p in crates_dir.iterdir() if p.is_dir() or p.is_symlink()):
        rel = f"crates/{crate.name}"
        if crate.is_symlink():
            problems.append(f"host `{rel}` is a symlink: Rust source inventory is not closed")
            continue
        src_root = crate / "src"
        if src_root.is_symlink():
            problems.append(f"host `{rel}` source `{rel}/src` is a symlink")
            continue
        if src_root.is_dir():
            for link in sorted(p for p in src_root.rglob("*") if p.is_symlink()):
                problems.append(
                    f"host `{rel}` source `{link.relative_to(root).as_posix()}` "
                    "is a symlink: Rust source inventory is not closed"
                )
        if rel == CODEC_OWNER:
            continue  # only physical codec ownership is exempt, not path safety
        sources = _crate_sources(crate)
        # A Zig call in another source file does NOT attest this codec edge.
        # Per-file fail-closed coverage prevents unrelated calls from masking
        # physical SENS bypasses within the same Rust crate.
        unbridged = []
        for source in sources:
            active = _live_rust(source.read_text(encoding="utf-8", errors="replace"))
            # Test-only Zig calls cannot attest a production SENS codec edge,
            # regardless of whether cfg(test) appears before or after it.
            try:
                production = _production_rust(active)
            except ValueError as exc:
                problems.append(
                    f"host `{rel}` source `{source.relative_to(root).as_posix()}` "
                    f"cfg(test) boundary is ambiguous: {exc}"
                )
                continue
            physical = CODEC_API.search(active) is not None
            zig_anywhere = CORRIDOR_API.search(active) is not None
            production_codec = CODEC_API.search(production) is not None
            production_zig = CORRIDOR_API.search(production) is not None
            if (physical and not zig_anywhere) or (production_codec and not production_zig):
                unbridged.append(source.relative_to(root).as_posix())
        if not unbridged:
            continue
        entry = exempt.get(rel)
        if entry is None:
            for path in unbridged:
                problems.append(
                    f"host `{rel}` source `{path}` reaches SENS physical bytes "
                    "without the Zig corridor and is not registered in corridor_host_coverage.json"
                )
        else:
            used_exemptions.add(rel)
    # A host that migrated to Zig must retire its old bypass record. Stale
    # exceptions otherwise silently keep a physical Rust bypass authorized.
    for name in sorted(exempt.keys() - used_exemptions):
        problems.append(f"registry stale exemption {name}: no active unbridged Rust codec route")
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
