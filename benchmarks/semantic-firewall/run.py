#!/usr/bin/env python3
"""Deterministic negative-control tournament for the canonical registry."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "lib/surface/semantic-registry.lisp"
CHECKER = ROOT / "scripts/check_semantic_registry.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("semantic_registry_checker", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load registry checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mutations(source: str) -> dict[str, str]:
    first, second = "(00000000 (en ())", "(00000001 (en quote)"
    return {
        "bad_identity_width": source.replace("(00000000 ", "(0000000 ", 1),
        "duplicate_identity": source.replace("(00000001 ", "(00000000 ", 1),
        "identity_order_swap": source.replace(first, "__FIRST__", 1).replace(second, first, 1).replace("__FIRST__", second, 1),
        "missing_first_wave_surface": source.replace("(sa svarūpa)", "", 1),
        "human_symbolic_surface": source.replace("(en quote)", "(en +)", 1),
        "unknown_surface_namespace": source.replace("(sym ())", "(xx extra)", 1),
        "truncated_registry": source[:-2],
        "extra_surface_slot": source.replace("(sym ())", "(sym ()) (extra value)", 1),
    }


def run(registry: Path) -> dict:
    checker = load_checker()
    source = registry.read_text(encoding="utf-8")
    base = checker.parse_all(checker.tokens(source))
    checker.check(base[0])
    rows = mutations(source)
    rejected: list[str] = []
    escaped: list[str] = []
    errors: dict[str, str] = {}
    for name, mutant in rows.items():
        try:
            roots = checker.parse_all(checker.tokens(mutant))
            if len(roots) != 1:
                raise ValueError("registry must contain exactly one top-level table form")
            checker.check(roots[0])
        except (OSError, ValueError) as error:
            rejected.append(name)
            errors[name] = str(error)
        else:
            escaped.append(name)
    if escaped:
        raise SystemExit("mutation escaped firewall: " + ", ".join(escaped))
    raw = registry.read_bytes()
    return {
        "schema": "sens-semantic-firewall/v1",
        "authority": str(registry.relative_to(ROOT)),
        "authority_sha256": hashlib.sha256(raw).hexdigest(),
        "mutation_cases": len(rows),
        "rejected_cases": len(rejected),
        "escaped_cases": len(escaped),
        "rejection_coverage": len(rejected) / len(rows),
        "rejected": rejected,
        "errors": errors,
        "oracle": "every named authority mutation is rejected by the canonical checker",
        "scope": "negative source-conformance; not a runtime security proof",
    }


def render(result: dict) -> str:
    lines = [
        "# Semantic Firewall Tournament",
        "",
        f"- Mutation cases: **{result['mutation_cases']}**.",
        f"- Rejected: **{result['rejected_cases']}**.",
        f"- Escaped: **{result['escaped_cases']}**.",
        f"- Rejection coverage: **{result['rejection_coverage']:.1%}**.",
        "",
        "> This is a negative source-conformance witness. It shows that these named mutations are rejected; it is not a general runtime security proof.",
        "",
        "Rejected controls: " + ", ".join(result["rejected"]),
        "",
        f"Authority SHA-256: `{result['authority_sha256']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.registry)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "report.md").write_text(render(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
