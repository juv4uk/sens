#!/usr/bin/env python3
"""Fail-closed, cross-language domain-ladder guard for canonical SENS paths.

This replaces the old eight-bit identity guard, not the historical evidence.
Its jurisdiction is explicitly enumerated below; unlisted compatibility
consumers remain migration debt and are not falsely declared migrated.
Domain *capacity* never proves a resident callable. D24+ is arithmetic only.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# Canonical code in multiple languages (not archived donors / historical
# benchmark lanes); every listed file must exist and stay free of old names.
CANONICAL = (
    "crates/sens/src/source_words.rs",
    "crates/sens/src/domain_words.rs",
    "crates/sens/src/domain_identity.rs",
    "crates/sens/src/canonical_reader.rs",
    "crates/sens/src/eval/d5_arithmetic.rs",
    "crates/sens/src/eval/d6_arithmetic.rs",
    "scripts/research-2077-binary-word-law.py",
    "scripts/check-core4-d24-migration.py",
    "benchmarks/domain12345678/run.py",
    "benchmarks/domain1234-dispatch/d34_dispatch.c",
)
EXPECTED = {1: 2, 2: 4, 3: 8, 4: 16, 5: 32, 6: 64,
            7: 126, 8: 256, 9: 512, 10: 1024}
D7_RESERVED = {"0100001", "0101010"}
OLD_IDENTITY = re.compile(
    r"(?<![\w])(?:Sid8|Sens8|Function8|sid8|sens8|function8)(?![\w])"
    r"|(?:Value|ExprKind)::Sid\b"
    r"|\b(?:to|from)_sens8\s*\("
    r"|\bsens!\s*\([01]{8}\)"
)
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
C_COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)


def executable_text(path: str, source: str) -> str:
    # Documentation/provenance remains available in comments. Only actual
    # named symbol/code regressions are rejected; no global text erasure.
    if path.endswith((".c", ".cc", ".cpp", ".h", ".hpp", ".rs")):
        return C_COMMENTS.sub("", source)
    if path.endswith(".lisp"):
        return "\n".join(line.split(";", 1)[0] for line in source.splitlines())
    if path.endswith(".py"):
        return "\n".join(
            line for line in source.splitlines()
            if not line.lstrip().startswith("#")
        )
    return source


def inspect_code(path: str, source: str) -> list[str]:
    body = executable_text(path, source)
    findings = []
    for match in OLD_IDENTITY.finditer(body):
        findings.append(match.group(0))
    return findings


def inspect_domains(table_texts: dict[int, str]) -> dict[int, int]:
    counts = {}
    for domain in range(1, 11):
        source = table_texts.get(domain)
        if source is None:
            raise ValueError(f"missing domain table D{domain}")
        words = ROW.findall(source)
        if len(words) != EXPECTED[domain]:
            raise ValueError(f"D{domain}: expected {EXPECTED[domain]} exact rows; got {len(words)}")
        invalid = [word for word in words if len(word) != domain]
        if invalid:
            raise ValueError(f"D{domain}: non-exact-width row {invalid[0]}")
        if len(set(words)) != len(words):
            raise ValueError(f"D{domain}: duplicate domain coordinate")
        expected = {f"{index:0{domain}b}" for index in range(1 << domain)}
        if domain == 7:
            expected -= D7_RESERVED
        if set(words) != expected:
            raise ValueError(f"D{domain}: wrong rows, gaps or unauthorized coordinates")
        counts[domain] = len(words)
    return counts


def inspect_files(root: Path) -> dict[int, int]:
    for rel in CANONICAL:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing active source: {rel}")
        text = path.read_text(encoding="utf-8")
        offenders = inspect_code(rel, text)
        if offenders:
            raise ValueError(f"old identity in {rel}: {', '.join(offenders[:12])}")
    domain_texts = {}
    for domain in EXPECTED:
        rel = f"lib/domains/d{domain}.lisp"
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing domain table: {rel}")
        domain_texts[domain] = path.read_text(encoding="utf-8")
    return inspect_domains(domain_texts)


def self_test() -> None:
    clean = (
        ("source.rs", "use crate::{BinarySourceWord, DomainIdentity};"),
        ("candidate.py", "class DomainCoordinate: pass"),
        ("selector.c", "typedef struct { unsigned width; unsigned bits; } DomainCoordinate;"),
        ("d3.lisp", "(101 (ук тотожне?) (en eq?))"),
    )
    for path, code in clean:
        if inspect_code(path, code):
            raise ValueError(f"clean source rejected: {path}")
    bad = (
        ("code.rs", "use crate::Sens8;"),
        ("code.rs", "Value::Sid(whatever)"),
        ("code.py", "def to_sens8(self): pass"),
        ("code.c", "typedef unsigned char Sid8;"),
        ("code.lisp", "(sid8 legacy-wire-value)"),
    )
    for path, code in bad:
        if not inspect_code(path, code):
            raise ValueError(f"old identity not rejected: {path} {code}")
    if inspect_code("code.c", "/* historical Sens8 */\nstruct DomainCoordinate { int width; };"):
        raise ValueError("historical C comment must not be interpreted as code")

    # Absent / duplicate / out-of-domain / missing-reserved proof inputs fail.
    toy = {n: "(domain-table/1\n" + "".join(
        f" ({i:0{n}b} (ук тест))\n"
        for i in range(1 << n)
        if n != 7 or f"{i:07b}" not in D7_RESERVED
    ) + ")\n" for n in EXPECTED}
    counts = inspect_domains(toy)
    if counts != EXPECTED:
        raise ValueError("ratified domain ladder counts failed")
    for invalid in (
        {**toy, 1: toy[1].replace("(0 ", "(00 ")},
        {**toy, 3: toy[3] + "(001 (ук дубль))\n"},
        {**toy, 7: toy[7].replace("(0000000 ", "(0100001 ")},
        {n: value for n, value in toy.items() if n != 10},
    ):
        try:
            inspect_domains(invalid)
        except ValueError:
            continue
        raise ValueError("invalid domain ladder accepted")
    try:
        inspect_files(Path("/nonexistent-domain-ladder-guard-probe"))
    except ValueError as exc:
        if "missing active source" not in str(exc):
            raise
    else:
        raise ValueError("missing sources were admitted")
    print("DOMAIN-LADDER-IDENTITY: self-test PASS (Rust/Python/C/Lisp + negative controls)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        if args.check:
            counts = inspect_files(ROOT)
            print("DOMAIN-LADDER-IDENTITY: PASS scoped canonical code; "
                  + " ".join(f"D{n}={counts[n]}" for n in counts))
            print("DOMAIN-LADDER-IDENTITY: unscanned historical/compatibility "
                  "consumers remain migration debt; this is not release GO")
        if not (args.self_test or args.check):
            parser.error("specify --check or --self-test")
    except (ValueError, OSError, UnicodeError) as exc:
        print("DOMAIN-LADDER-IDENTITY: BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
