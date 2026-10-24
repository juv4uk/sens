#!/usr/bin/env python3
"""Перевіряти математичну драбину D12+ окремо від фізичного профілю D24+.

Чинна семантична влада: contracts/numeric-domains-ratification.lisp,
форма numeric-d12-start-extension-1, закон D(12 * 2^n).
Історичний D24-профіль у тому самому файлі лишається джерелом
реально підтримуваних фізичних ширин Zig.

Цей генератор створює тільки механічні дзеркала для Rust/Python.
Zig numeric_domains.zig перевіряється на відповідність фізичному
профілю, але його нативні тести та код не перезаписуються.

Використання: python3 scripts/generate-numeric-domain-constants.py [--check]
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path
from domain_tables import number_domains

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "numeric-domains-ratification.lisp"
ZIG_OUT = ROOT / "research" / "zig-codecs" / "numeric_domains.zig"
RS_OUT = ROOT / "crates" / "sens" / "src" / "numeric_domains_generated.rs"
PY_OUT = ROOT / "scripts" / "numeric_domains_generated.py"

HEADER = "GENERATED from contracts/numeric-domains-ratification.lisp — DO NOT EDIT BY HAND."


def read_contract() -> dict:
    """Повернути чинні D12+ домени та окремий історичний фізичний профіль."""
    source = CONTRACT.read_text(encoding="utf-8")
    domains = number_domains(CONTRACT)
    widths = [width for _name, width in domains]
    marker = "(schema . numeric-domains-ratification-1)"
    end_marker = "(schema . numeric-d24-signed-extension-1)"
    if source.count(marker) != 1 or source.count(end_marker) != 1:
        raise ValueError("Очікували одну історичну форму D24 і одну її межу")
    historical = source.split(marker, 1)[1].split(end_marker, 1)[0]
    match = re.search(r"\(canonical-domain-names\s*\.\s*\(([^()]*)\)\)", historical)
    if match is None:
        raise ValueError("Історичний фізичний профіль D24 відсутній")
    names = match.group(1).split()
    if not names or any(re.fullmatch(r"D[1-9][0-9]*", name) is None for name in names):
        raise ValueError(f"Некоректні фізичні домени: {names!r}")
    physical = [int(name[1:]) for name in names]
    if physical != widths[1:1 + len(physical)]:
        raise ValueError(f"Фізичний D24-профіль не є префіксом наступників D12: {physical!r}")
    return {
        "widths": widths,
        "first": widths[0],
        "rule": "D(12 * 2^n), n >= 0",
        "physical_widths": physical,
    }


def validate_zig_profile(source: str, physical_widths: list[int]) -> None:
    """Zig зберігає лише фізичні ширини; не домислюємо ратифікацію з байтів."""
    matches = re.findall(
        r"(?m)^\s*pub\s+const\s+WIDE_WIDTHS\s*=\s*\[_\]u16\s*\{([^{}]*)\}\s*;",
        source,
    )
    if len(matches) != 1:
        raise ValueError("Очікували рівно одне фізичне визначення Zig WIDE_WIDTHS")
    parts = [part.strip() for part in matches[0].split(",") if part.strip()]
    if any(re.fullmatch(r"(?:0|[1-9][0-9]*)", part) is None for part in parts):
        raise ValueError("Zig WIDE_WIDTHS містить неканонічне слово")
    actual = [int(part) for part in parts]
    if actual != physical_widths:
        raise ValueError(f"Zig physical widths: expected={physical_widths!r} actual={actual!r}")


def rust(c: dict) -> str:
    semantic = ", ".join(str(w) for w in c["widths"])
    physical = ", ".join(str(w) for w in c["physical_widths"])
    return f"""// {HEADER}
// Чинний D12+ закон: {c['rule']}.
// Rust переносить точні ширини, а не визначає семантику або виконання.

/// Початковий префікс ратифікованих математичних ширин.
pub const NUMERIC_DOMAIN_WIDTHS: [u16; {len(c['widths'])}] = [ {semantic} ];
pub const FIRST_NUMERIC_DOMAIN_WIDTH: u16 = {c['first']};

/// Реально підтримуваний фізичний профіль, без D12.
pub const PHYSICAL_NUMERIC_WIDTHS: [u16; {len(c['physical_widths'])}] = [ {physical} ];
pub const FIRST_PHYSICAL_NUMERIC_WIDTH: u16 = {c['physical_widths'][0]};

/// Подвоєння ширини не надає права виклику чи фізичної підтримки.
pub const fn next_width(w: u16) -> u16 {{ w * 2 }}
"""


def python(c: dict) -> str:
    semantic = ", ".join(str(w) for w in c["widths"])
    physical = ", ".join(str(w) for w in c["physical_widths"])
    return f'''# {HEADER}
# Чинний D12+ закон: {c["rule"]}.
# Механічний опис ширин; не виконання семантики SENS.

WIDE_WIDTHS = [{semantic}]
FIRST_WIDTH = {c["first"]}
PHYSICAL_WIDE_WIDTHS = [{physical}]
FIRST_PHYSICAL_WIDTH = {c["physical_widths"][0]}


def next_width(w):
    return w * 2


def is_wide(w):
    return w in WIDE_WIDTHS


def is_physically_supported(w):
    return w in PHYSICAL_WIDE_WIDTHS
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    c = read_contract()
    zig_source = ZIG_OUT.read_text(encoding="utf-8")
    validate_zig_profile(zig_source, c["physical_widths"])
    outs = {RS_OUT: rust(c), PY_OUT: python(c)}
    if args.check:
        bad = []
        for path, want in outs.items():
            have = path.read_text(encoding="utf-8") if path.exists() else ""
            if have != want:
                bad.append(path.relative_to(ROOT))
        if bad:
            print("DIVERGED from contract (run the generator):")
            for b in bad:
                print("  -", b)
            return 1
        print(f"ЧИННІ D12+ {c['widths']}; ФІЗИЧНІ Zig {c['physical_widths']}; Rust/Python узгоджено")
        return 0
    for path, text in outs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print("wrote", path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
