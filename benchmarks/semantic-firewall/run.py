#!/usr/bin/env python3
"""Негативний турнір точнодоменного реєстру SENS (аудит, не виконання)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "lib/domains/d3.lisp"
CHECKER = ROOT / "scripts/check_semantic_registry.py"
WIDTH = 3


def load_checker():
    spec = importlib.util.spec_from_file_location("semantic_registry_checker", CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError("неможливо завантажити статичний контролер доменів")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mutations(source: str) -> dict[str, str]:
    return {
        "bad_identity_width": source.replace("(001 (ук як-є)", "(00000001 (ук як-є)", 1),
        "duplicate_identity": source.replace("(001 (ук як-є)", "(000 (ук як-є)", 1),
        "coordinate_displacement": source.replace("(000 (ук ())", "(001 (ук ())", 1),
        "missing_ukr_surface": source.replace("(укр як-є)", "(ukr як-є)", 1),
        "unknown_surface_namespace": source.replace("(san svarūpa)", "(sa svarūpa)", 1),
        "truncated_registry": source[:-2],
        "extra_surface_slot": source.replace("(en quote)", "(en quote) (extra unexpected)", 1),
        "missing_row": source.replace(
            '  (001 (ук як-є) (укр як-є) (san svarūpa) (en quote) (LISP QUOTE) (sym "\'"))\n',
            "",
            1,
        ),
    }


def run(registry: Path) -> dict:
    checker = load_checker()
    source = registry.read_text(encoding="utf-8")
    roots = checker.parse_all(checker.tokens(source))
    if len(roots) != 1:
        raise ValueError("доменна таблиця мусить бути єдиною формою")
    checker.check(roots[0], WIDTH)
    rows = mutations(source)
    rejected: list[str] = []
    escaped: list[str] = []
    errors: dict[str, str] = {}
    for name, mutant in rows.items():
        if mutant == source:
            raise ValueError(f"мутація нічого не змінила: {name}")
        try:
            changed = checker.parse_all(checker.tokens(mutant))
            if len(changed) != 1:
                raise ValueError("доменна таблиця мусить бути єдиною формою")
            checker.check(changed[0], WIDTH)
        except (OSError, ValueError) as error:
            rejected.append(name)
            errors[name] = str(error)
        else:
            escaped.append(name)
    if escaped:
        raise SystemExit("мутація обійшла аудит: " + ", ".join(escaped))
    return {
        "schema": "sens-semantic-firewall/v2",
        "authority": str(registry.relative_to(ROOT)),
        "authority_sha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
        "domain_width": WIDTH,
        "mutation_cases": len(rows),
        "rejected_cases": len(rejected),
        "escaped_cases": len(escaped),
        "rejection_coverage": len(rejected) / len(rows),
        "rejected": rejected,
        "errors": errors,
        "oracle": "each deliberate mutation rejected by exact-domain table audit",
        "scope": "negative source-conformance; not SENS runtime or T5M proof",
    }


def render(result: dict) -> str:
    lines = [
        "# Доменний негативний турнір",
        "",
        f"- Спроби порушення: **{result['mutation_cases']}**.",
        f"- Відхилено: **{result['rejected_cases']}**.",
        f"- Обійшли перевірку: **{result['escaped_cases']}**.",
        f"- Покриття негативних випадків: **{result['rejection_coverage']:.1%}**.",
        "",
        "Це контроль форми джерела, а не доказ виконання SENS.",
        "",
        "Відхилені: " + ", ".join(result["rejected"]),
        "",
        f"SHA-256 джерела: `{result['authority_sha256']}`",
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
