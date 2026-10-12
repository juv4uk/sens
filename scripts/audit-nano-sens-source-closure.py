#!/usr/bin/env python3
"""Audit static Rust module/cfg/include edges relevant to Nano-SENS.

This is deliberately a conservative inventory, not a Rust compiler or a
minimum-seed proof. Dynamic include paths, cfg-dependent resolution, Cargo
build-script inputs, toolchain, Git objects, vendor crates, and cross-repository
CML inputs remain separately classified until independently closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "nano-sens-static-source-edges-audit/1"
MODULE_RE = re.compile(r"\bmod\s+([A-Za-z_][A-Za-z0-9_]*)\s*;", re.MULTILINE)
INCLUDE_RE = re.compile(r"\b(include|include_str|include_bytes)!\s*\(")
STRING_RE = re.compile(r'^"((?:\\.|[^"\\])*)"$', re.DOTALL)
CFG_RE = re.compile(r"#\s*\[\s*cfg\s*\((.*?)\)\s*\]", re.DOTALL)
PATH_RE = re.compile(r'#\s*\[\s*path\s*=\s*"((?:\\.|[^"\\])*)"\s*\]')
ENV_RE = re.compile(r"\b(env|option_env)!\s*\(\s*\"([A-Za-z_][A-Za-z0-9_]*)\"\s*\)")

ROOTS = (
    "crates/sens/src/lib.rs",
    "crates/xtask/src/main.rs",
)
MANIFESTS = (
    "Cargo.toml",
    "Cargo.lock",
    ".cargo/config.toml",
    "crates/sens/Cargo.toml",
    "crates/xtask/Cargo.toml",
)
KNOWN_OPEN_BOUNDARIES = [
    "Cargo package/workspace dependency closure is not inferred from Rust module edges.",
    "Build-script/proc-macro execution and environment-dependent inputs require a Cargo/build trace.",
    "Dynamic include!/include_str!/include_bytes! paths are reported as unresolved.",
    "cfg-dependent paths are inventoried conservatively; this is not rustc's active configuration result.",
    "The pinned CML runner, WSM nucleus, required Git refs/objects, vendored crate closure, toolchain, OS and shared libraries are outside this SENS-local source graph.",
    "An observed static source graph is not a minimum-seed or whole-chain closure proof.",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return Path("..", *path.resolve().parts[-max(1, len(path.resolve().parts) - len(root.resolve().parts)):]).as_posix()


def attributes_before(text: str, index: int) -> list[str]:
    """Return immediately attached single-line Rust attributes before an item."""
    line_start = text.rfind("\n", 0, index) + 1
    before = text[:line_start].splitlines()
    attrs: list[str] = []
    for line in reversed(before):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#[") and stripped.endswith("]"):
            attrs.append(stripped)
            continue
        break
    return list(reversed(attrs))


def cfg_context(attrs: list[str]) -> list[str]:
    result: list[str] = []
    for attr in attrs:
        match = re.search(r"#\s*\[\s*cfg\s*\((.*)\)\s*\]", attr)
        if match:
            result.append(match.group(1).strip())
        elif "cfg_attr" in attr:
            result.append("cfg_attr:" + attr)
    return result


def unescape_rust_path(value: str) -> str:
    # Paths in the current graph are ordinary UTF-8 literals. Preserve unknown
    # escapes rather than silently changing a path.
    return (value.replace(r"\\", "\\")
                 .replace(r"\"", '"')
                 .replace(r"\n", "\n")
                 .replace(r"\t", "\t")
                 .replace(r"\r", "\r"))


def call_argument(text: str, open_paren: int) -> str | None:
    """Read a macro's parenthesized argument while respecting strings/nesting."""
    depth = 1
    in_string = False
    escaped = False
    for i in range(open_paren + 1, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i].strip()
    return None


def resolve_module(source: Path, name: str, path_attr: str | None) -> Path:
    if path_attr is not None:
        return (source.parent / unescape_rust_path(path_attr)).resolve()
    if source.name in {"lib.rs", "main.rs", "mod.rs"}:
        base = source.parent
    else:
        base = source.parent / source.stem
    for candidate in (base / f"{name}.rs", base / name / "mod.rs"):
        if candidate.is_file():
            return candidate.resolve()
    # Return the conventional first candidate to retain a useful missing edge.
    return (base / f"{name}.rs").resolve()


def scan(root: Path) -> dict[str, Any]:
    root = root.resolve()
    queue: list[Path] = []
    for item in ROOTS:
        path = root / item
        if path.is_file():
            queue.append(path.resolve())
    # Build scripts are possible selected-package inputs even if no mod edge
    # reaches them; record and scan them when present.
    for item in ("crates/sens/build.rs", "crates/xtask/build.rs"):
        path = root / item
        if path.is_file():
            queue.append(path.resolve())

    visited: set[Path] = set()
    edges: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    environment: set[tuple[str, str]] = set()
    source_files: dict[str, dict[str, Any]] = {}

    while queue:
        source = queue.pop(0).resolve()
        if source in visited or not source.is_file():
            continue
        visited.add(source)
        try:
            text = read_text(source)
        except (OSError, UnicodeError) as error:
            gaps.append({"kind": "unreadable_source", "path": relative(source, root), "detail": str(error)})
            continue

        source_rel = relative(source, root)
        raw = source.read_bytes()
        source_files[source_rel] = {
            "sha256": sha256_bytes(raw),
            "size_bytes": len(raw),
            "role": "rust-source-or-build-script",
        }

        for match in ENV_RE.finditer(text):
            environment.add((match.group(1), match.group(2)))

        for match in MODULE_RE.finditer(text):
            name = match.group(1)
            attrs = attributes_before(text, match.start())
            cfg = cfg_context(attrs)
            path_matches = [PATH_RE.search(attr) for attr in attrs]
            path_match = next((m for m in reversed(path_matches) if m), None)
            path_attr = path_match.group(1) if path_match else None
            target = resolve_module(source, name, path_attr)
            exists = target.is_file()
            edge = {
                "kind": "rust-mod",
                "source": source_rel,
                "line": text.count("\n", 0, match.start()) + 1,
                "name": name,
                "cfg": cfg,
                "path_attribute": path_attr,
                "target": relative(target, root),
                "target_exists": exists,
            }
            edges.append(edge)
            if exists and target.suffix == ".rs":
                queue.append(target)
            elif not exists:
                gaps.append({
                    "kind": "missing_module_target",
                    "source": source_rel,
                    "line": edge["line"],
                    "target": edge["target"],
                    "cfg": cfg,
                })

        for match in INCLUDE_RE.finditer(text):
            macro = match.group(1)
            arg = call_argument(text, match.end() - 1)
            line = text.count("\n", 0, match.start()) + 1
            literal = STRING_RE.fullmatch(arg or "")
            if literal is None:
                edges.append({
                    "kind": macro,
                    "source": source_rel,
                    "line": line,
                    "target": None,
                    "target_exists": None,
                    "resolution": "nonliteral-or-dynamic",
                    "argument_prefix": (arg or "")[:120],
                })
                gaps.append({
                    "kind": "unresolved_compile_time_include",
                    "source": source_rel,
                    "line": line,
                    "macro": macro,
                    "argument_prefix": (arg or "")[:120],
                })
                continue
            target = (source.parent / unescape_rust_path(literal.group(1))).resolve()
            exists = target.is_file()
            edge = {
                "kind": macro,
                "source": source_rel,
                "line": line,
                "target": relative(target, root),
                "target_exists": exists,
                "resolution": "literal-relative-to-source",
            }
            edges.append(edge)
            if exists:
                if macro == "include" and target.suffix == ".rs":
                    queue.append(target)
            else:
                gaps.append({
                    "kind": "missing_compile_time_include_target",
                    "source": source_rel,
                    "line": line,
                    "target": edge["target"],
                })

    manifest_files: dict[str, dict[str, Any]] = {}
    for item in MANIFESTS:
        path = root / item
        if path.is_file():
            raw = path.read_bytes()
            manifest_files[item] = {"sha256": sha256_bytes(raw), "size_bytes": len(raw)}
        else:
            gaps.append({"kind": "missing_scope_manifest", "path": item})

    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        head = None

    # Deduplicate only byte-identical gap observations; keep different source
    # locations for the same target because each is a separate dependency edge.
    unique_gaps: list[dict[str, Any]] = []
    seen_gaps: set[str] = set()
    for gap in gaps:
        key = json.dumps(gap, sort_keys=True, ensure_ascii=False)
        if key not in seen_gaps:
            seen_gaps.add(key)
            unique_gaps.append(gap)

    unresolved = sum(1 for edge in edges if edge.get("resolution") == "nonliteral-or-dynamic")
    return {
        "schema": SCHEMA,
        "status": "STATIC_EDGE_AUDIT_ONLY_CLOSURE_NOT_PROVEN",
        "source_revision": head,
        "scope": {
            "roots": list(ROOTS),
            "source_file_count": len(source_files),
            "static_edge_count": len(edges),
            "manifest_file_count": len(manifest_files),
            "unresolved_dynamic_include_count": unresolved,
            "gap_count": len(unique_gaps),
            "minimum_seed_proven": False,
            "whole_chain_closure_proven": False,
        },
        "source_files": dict(sorted(source_files.items())),
        "scope_manifests": dict(sorted(manifest_files.items())),
        "edges": sorted(edges, key=lambda x: (x["source"], x["line"], x["kind"], x.get("target") or "")),
        "environment_reads": [
            {"macro": macro, "variable": variable}
            for macro, variable in sorted(environment)
        ],
        "gaps": unique_gaps,
        "open_boundaries": KNOWN_OPEN_BOUNDARIES,
    }


def self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="nano-sens-edges-") as tmp:
        root = Path(tmp)
        (root / "crates/sens/src").mkdir(parents=True)
        (root / "crates/xtask/src").mkdir(parents=True)
        (root / ".cargo").mkdir()
        for item in MANIFESTS:
            target = root / item
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# fixture\n", encoding="utf-8")
        (root / "crates/sens/src/lib.rs").write_text(
            'mod child;\n#[cfg(test)]\nmod tests;\n'
            'const TEXT: &str = include_str!("data.txt");\n'
            'const DYNAMIC: &str = include_str!(concat!(env!("ROOT"), "/dyn.txt"));\n',
            encoding="utf-8",
        )
        (root / "crates/sens/src/child.rs").write_text("pub fn child() {}\n", encoding="utf-8")
        (root / "crates/sens/src/tests.rs").write_text("#[test] fn ok() {}\n", encoding="utf-8")
        (root / "crates/sens/src/data.txt").write_text("fixture\n", encoding="utf-8")
        (root / "crates/xtask/src/main.rs").write_text("fn main() {}\n", encoding="utf-8")
        report = scan(root)
        checks = [
            any(e["kind"] == "rust-mod" and e["name"] == "child" and e["target_exists"] for e in report["edges"]),
            any(e["kind"] == "rust-mod" and e["name"] == "tests" and "test" in " ".join(e["cfg"]) and e["target_exists"] for e in report["edges"]),
            any(e["kind"] == "include_str" and e.get("target") == "crates/sens/src/data.txt" and e["target_exists"] for e in report["edges"]),
            any(g["kind"] == "unresolved_compile_time_include" for g in report["gaps"]),
            report["scope"]["minimum_seed_proven"] is False,
        ]
        if not all(checks):
            raise RuntimeError(f"self-test failed: {checks}; report={json.dumps(report, ensure_ascii=False)[:4000]}")
    print("NANO-SENS STATIC SOURCE EDGE AUDIT SELF-TEST: PASS (5 checks)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="SENS repository checkout")
    parser.add_argument("--out", help="write JSON report to this path; otherwise print to stdout")
    parser.add_argument("--self-test", action="store_true", help="run parser/resolution falsifiers")
    parser.add_argument(
        "--strict-missing-modules",
        action="store_true",
        help="exit nonzero when any declared module source cannot be resolved (experimental)",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        if args.out is None:
            return 0

    report = scan(Path(args.repo_root))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(
            "NANO-SENS STATIC SOURCE EDGES: "
            f"{report['scope']['source_file_count']} Rust files, "
            f"{report['scope']['static_edge_count']} edges, "
            f"{report['scope']['gap_count']} open observations; closure remains unproven"
        )
    else:
        sys.stdout.write(rendered)
    if args.strict_missing_modules and any(g["kind"] == "missing_module_target" for g in report["gaps"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
