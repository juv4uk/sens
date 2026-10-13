#!/usr/bin/env python3
"""Fail-closed domain-ladder and decimal-identity-bridge guard for SENS.

This replaces the old eight-bit identity guard, not the historical evidence.
Its jurisdiction is explicitly enumerated below; unlisted compatibility
consumers remain migration debt and are not falsely declared migrated.
Domain *capacity* never proves a resident callable. D24+ is arithmetic only.
Identity transport is bits+width; decimal strings may not bridge identities.
"""
from __future__ import annotations

import argparse
import json
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
    "crates/sens/src/bignum.rs",
    "crates/sens/src/binary_execution.rs",
    "crates/sens/src/binary_number.rs",
    "crates/sens/src/bit9.rs",
    "crates/sens/src/bits.rs",
    "crates/sens/src/bootstrap_measurement.rs",
    "crates/sens/src/compiler_bootstrap.rs",
    "crates/sens/src/compiler_language.rs",
    "crates/sens/src/compiler_role.rs",
    "crates/sens/src/d5_definition_bindings_generated.rs",
    "crates/sens/src/d7_display_registry_generated.rs",
    "crates/sens/src/d9_definition_bindings_generated.rs",
    "crates/sens/src/domain_ladder.rs",
    "crates/sens/src/domain_numeric.rs",
    "crates/sens/src/domain_owner_generated.rs",
    "crates/sens/src/domain_surface_registry_generated.rs",
    "crates/sens/src/error.rs",
    "crates/sens/src/eval/arithmetic.rs",
    "crates/sens/src/eval/builtins.rs",
    "crates/sens/src/eval/macro_substrate.rs",
    "crates/sens/src/eval/necessary_forms_generated.rs",
    "crates/sens/src/eval/selector_law.rs",
    "crates/sens/src/eval/special_forms/codepoint.rs",
    "crates/sens/src/eval/special_forms/digest.rs",
    "crates/sens/src/eval/special_forms/io.rs",
    "crates/sens/src/eval/special_forms/json.rs",
    "crates/sens/src/eval/special_forms/strings.rs",
    "crates/sens/src/eval/special_forms.rs",
    "crates/sens/src/frame3_domain.rs",
    "crates/sens/src/frame3_grammar.rs",
    "crates/sens/src/frame3_micro.rs",
    "crates/sens/src/frame3_micro_enumerator.rs",
    "crates/sens/src/frame3_micro_v5.rs",
    "crates/sens/src/frame3_micro_v5_lambda.rs",
    "crates/sens/src/frame3_micro_v5_lambda_app.rs",
    "crates/sens/src/frame3_semantic.rs",
    "crates/sens/src/frame3_small.rs",
    "crates/sens/src/frame3_v2.rs",
    "crates/sens/src/function_signatures_generated.rs",
    "crates/sens/src/gpu_execution_packet.rs",
    "crates/sens/src/outer_envelope.rs",
    "crates/sens/src/packed_bits.rs",
    "crates/sens/src/semantic_registry_generated.rs",
    "crates/sens/src/source_packing.rs",
    "crates/sens/src/ternary_transport.rs",
    "crates/sens/src/text7.rs",
    "crates/sens/src/text7_projection.rs",
    "crates/sens/src/text7_projection_generated.rs",
    "crates/sens/src/universal_frame3.rs",
)
EXPECTED = {1: 2, 2: 4, 3: 8, 4: 16, 5: 32, 6: 64,
            7: 128, 8: 256, 9: 512, 10: 1024}
OLD_IDENTITY = re.compile(
    r"(?<![\w])(?:Sid8|Sens8|Function8|sid8|sens8|function8)(?![\w])"
    r"|(?:Value|ExprKind)::Sid\b"
    r"|\b(?:to|from)_sens8\s*\("
    r"|\bsens!\s*\([01]{8}\)"
)
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
C_COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)

# Identity paths are deliberately narrow: general D24+ arithmetic and ordinary
# CLI values may use numeric projections, but a domain identity must never cross
# decimal text between its width-qualified binary source and the next domain.
IDENTITY_PATHS = (
    *(f"lib/domains/d{n}.lisp" for n in range(1, 11)),
    "crates/sens/src/domain_ladder.rs",
    "crates/sens/src/domain_identity.rs",
    "crates/sens/src/domain_words.rs",
    "crates/sens/src/source_words.rs",
    "crates/sens/src/canonical_reader.rs",
    "crates/sens/src/mixed_source.rs",
    "crates/sens/src/source_packing.rs",
    "crates/sens/src/packed_bits.rs",
    "crates/sens/src/ternary_transport.rs",
    "crates/sens/src/semantic_registry.rs",
    "crates/sens/src/compiler_bootstrap.rs",
    "crates/sens/src/binary_execution.rs",
    "crates/sens-cli/src/main.rs",
    "crates/sens-cli/src/bin/sens-trit.rs",
    "scripts/sens_t5_codec.py",
)
# Human-entered CLI transport configuration is not a domain identity. Such a
# decimal boundary must be marked on the exact line, never whitelisted by file.
HUMAN_PROJECTION_PATHS = frozenset({
    "crates/sens-cli/src/main.rs",
})
INTEGER_TYPE = r"(?:u8|u16|u32|u64|u128|usize|i8|i16|i32|i64|i128|isize)"
DECIMAL_IDENTITY_RULES = (
    ("implicit/default-base integer parse",
     re.compile(r"\.parse\s*(?:::\s*<\s*" + INTEGER_TYPE + r"\s*>)?\s*\(")),
    ("decimal or autodetected radix parse",
     re.compile(r"\bfrom_str_radix\s*\([^;\n]*,\s*(?:0|10)\s*\)")),
    ("Python default/base-10 integer parse",
     re.compile(r"\bint\s*\(\s*[^,()\n]+\s*(?:,\s*(?:0|10)\s*)?\)")),
    ("decimal-only number formatter",
     re.compile(r"\bto_decimal_string\s*\(")),
    ("numeric identity payload converted to decimal text",
     re.compile(r"(?:\b(?:self\.)?(?:bits|payload|packed|raw|ordinal)\b|packed_bits\s*\(\s*\))\s*\.\s*to_string\s*\(")),
    ("Python string conversion of numeric identity payload",
     re.compile(r"\bstr\s*\(\s*(?:self\.)?(?:bits|payload|packed|raw|ordinal)\b")),
)
IDENTITY_NUMERIC_FIELD = re.compile(
    r"\b(?:bits|payload|packed|raw|ordinal|coordinate_bits|domain_bits)\b"
    r"|packed_bits\s*\("
)
RUST_FORMAT_CALL = re.compile(r"\b(?:format|write|writeln)!\s*\(\s*\"([^\"]*)\"")
PYTHON_FSTRING = re.compile(r"""(?i)\bf(?P<quote>['"])(?P<body>.*?)(?P=quote)""")
PYTHON_FORMAT_CALL = re.compile(r"""(?P<quote>['"])(?P<body>.*?)(?P=quote)\.format\s*\(""")


def _marked_human_projection(path: str, line: str) -> bool:
    if path not in HUMAN_PROJECTION_PATHS:
        return False
    # The marker must be a real comment, not merely text inside a string.
    if path.endswith(".rs"):
        comment = line.split("//", 1)[1] if "//" in line else ""
    elif path.endswith(".py"):
        comment = line.split("#", 1)[1] if "#" in line else ""
    elif path.endswith(".lisp"):
        comment = line.split(";", 1)[1] if ";" in line else ""
    else:
        return False
    return bool(re.search(r"\bprojection-human\b", comment))


def _decimal_default_placeholder(template: str, arguments: str = "") -> bool:
    # Inspect actual interpolation expressions/arguments, not ordinary prose in
    # an error message (e.g. "packed binary reader rejected: {err}").
    # Default formatting of an identity payload loses leading zeroes. Explicit
    # binary (:b / b) formatting is a source projection, not a decimal bridge.
    for field in re.findall(r"\{([^{}]*)\}", template):
        expression = field.split(":", 1)[0].split("!", 1)[0].strip()
        is_identity = bool(
            IDENTITY_NUMERIC_FIELD.search(expression)
            or IDENTITY_NUMERIC_FIELD.search(arguments)
        )
        if not is_identity:
            continue
        if ":" not in field:
            return True
        spec = field.split(":", 1)[1]
        if spec == "" or spec.endswith("d"):
            return True
    return False


def inspect_decimal_identity_bridges(path: str, source: str) -> list[str]:
    if path not in IDENTITY_PATHS:
        return []
    source_lines = source.splitlines()
    masked_lines = [
        "" if _marked_human_projection(path, line) else line
        for line in source_lines
    ]
    body = executable_text(path, "\n".join(masked_lines))
    findings = []
    for label, pattern in DECIMAL_IDENTITY_RULES:
        for match in pattern.finditer(body):
            line = body.count("\n", 0, match.start()) + 1
            findings.append(f"line {line}: {label}")

    for line_no, line in enumerate(body.splitlines(), 1):
        if not IDENTITY_NUMERIC_FIELD.search(line):
            continue
        if path.endswith(".rs"):
            for match in RUST_FORMAT_CALL.finditer(line):
                if _decimal_default_placeholder(match.group(1), match.group(2)):
                    findings.append(f"line {line_no}: default/decimal format of identity payload")
        elif path.endswith(".py"):
            for match in PYTHON_FSTRING.finditer(line):
                if _decimal_default_placeholder(match.group("body")):
                    findings.append(f"line {line_no}: default/decimal f-string of identity payload")
            for match in PYTHON_FORMAT_CALL.finditer(line):
                if _decimal_default_placeholder(match.group("body"), match.group("args")):
                    findings.append(f"line {line_no}: default/decimal .format() of identity payload")
    return findings


def inspect_identity_paths(root: Path) -> None:
    for rel in IDENTITY_PATHS:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing identity-boundary source: {rel}")
        source = path.read_text(encoding="utf-8")
        findings = inspect_decimal_identity_bridges(rel, source)
        if findings:
            raise ValueError(f"decimal intermediary in {rel}: {'; '.join(findings[:8])}")


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
        if set(words) != expected:
            raise ValueError(f"D{domain}: wrong rows, gaps or unauthorized coordinates")
        counts[domain] = len(words)
    return counts



# Негативні, а не правотворчі докази: однаковий W8 не стає D8.
# Запис = old label, classification, незалежний target, поточний D8 label.
W8_COLLISION = {
    "10101000": ("invoke", "MECHANISM-HOLD", None, "round"),
    "01001011": ("read-all", "DIRECT-CURRENT-IDENTITY", "D9:110101001", "abs∘recip"),
    "10100110": ("read-file", "DIRECT-CURRENT-IDENTITY", "D9:110110111", "1/"),
}
ACTIVE_GATES = (
    "scripts/test-binary-language-pipeline.sh",
    ".github/workflows/domain-bitness-laws.yml",
    ".github/workflows/domain-logic-laws.yml",
)


def inspect_w8_d8_collision(coverage: dict, d8_source: str) -> None:
    rows = coverage.get("rows")
    if coverage.get("status") != "AUDIT-COMPLETE" or not isinstance(rows, list):
        raise ValueError("W8 provenance lacks verified historical inventory")
    legacy = {}
    for row in rows:
        bits = row.get("legacy_code")
        if bits in legacy:
            raise ValueError(f"historical W8 duplicate: {bits}")
        legacy[bits] = row
    if len(legacy) != 256:
        raise ValueError("historical W8 inventory incomplete")
    for bits, (name, classification, target, current_name) in W8_COLLISION.items():
        row = legacy.get(bits)
        if row is None or row.get("legacy_name") != name:
            raise ValueError(f"historical W8 collision missing: {bits}")
        if row.get("classification") != classification:
            raise ValueError(f"historical W8 classification changed: {bits}")
        actual_target = row.get("current_target")
        if target is None:
            if actual_target is not None:
                raise ValueError(f"W8 mechanism HOLD improperly admitted: {bits}")
        elif not isinstance(actual_target, str) or target not in actual_target:
            raise ValueError(f"W8 cross-domain successor lost: {bits}")
        row_lines = [
            line for line in d8_source.splitlines()
            if line.lstrip().startswith("(" + bits + " ")
        ]
        if len(row_lines) != 1 or f"(en {current_name})" not in row_lines[0]:
            raise ValueError(f"D8 ratified resident drift: {bits}")
        if actual_target is not None and actual_target.startswith("D8:"):
            raise ValueError(f"historical W8 reclassified by same D8 bits: {bits}")


def inspect_active_gates(root: Path) -> None:
    for rel in ACTIVE_GATES:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"active migration gate missing: {rel}")
        data = path.read_text(encoding="utf-8")
        if "scripts/sid-binary-identity-guard.sh" in data:
            raise ValueError(f"retired flat-eight guard reintroduced: {rel}")
        for mode in ("--check", "--self-test"):
            if "scripts/check-domain-ladder-identity.py " + mode not in data:
                raise ValueError(f"domain-ladder {mode} gate missing: {rel}")
    if (root / "scripts/sid-binary-identity-guard.sh").exists():
        raise ValueError("retired eight-bit guard reintroduced in active tree")


def inspect_files(root: Path) -> dict[int, int]:
    inspect_identity_paths(root)
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
    counts = inspect_domains(domain_texts)
    provenance = root / "knowledge/sens8-current-coverage-v1.json"
    if not provenance.is_file() or provenance.is_symlink():
        raise ValueError("historical collision evidence missing")
    inspect_w8_d8_collision(
        json.loads(provenance.read_text(encoding="utf-8")), domain_texts[8]
    )
    inspect_active_gates(root)
    return counts


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

    decimal_clean = (
        ("crates/sens/src/domain_ladder.rs",
         'format!("{:0width$b}", bits, width = width);'),
        ("crates/sens/src/mixed_source.rs",
         "u16::from_str_radix(word, 2).unwrap();"),
        ("scripts/sens_t5_codec.py",
         "int(word, 2); int(trits, 3)"),
        ("crates/sens-cli/src/main.rs",
         "port.parse::<u16>().ok() // projection-human: TCP port is human transport configuration"),
    )
    for path, code in decimal_clean:
        if inspect_decimal_identity_bridges(path, code):
            raise ValueError(f"bit-preserving/human-boundary conversion rejected: {path} {code}")

    decimal_bad = (
        ("crates/sens/src/domain_ladder.rs", "let source = self.bits.to_string();"),
        ("crates/sens/src/source_words.rs", "let payload = token.parse::<u16>()?;"),
        ("crates/sens/src/mixed_source.rs", "u16::from_str_radix(word, 10).unwrap();"),
        ("scripts/sens_t5_codec.py", "payload = int(word)"),
        ("crates/sens/src/domain_identity.rs", 'format!("{bits}", bits = identity.packed_bits());'),
        ("crates/sens-cli/src/main.rs", "port.parse::<u16>().ok()"),
    )
    for path, code in decimal_bad:
        if not inspect_decimal_identity_bridges(path, code):
            raise ValueError(f"decimal identity bridge escaped ratchet: {path} {code}")
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
        if not any(marker in str(exc) for marker in (
            "missing identity-boundary source",
            "missing active source",
        )):
            raise
    else:
        raise ValueError("missing sources were admitted")
    # Механізми backend, що вже не відновлюють історичну identity,
    # більше не можуть повернути Sens8 навіть один раз: CANONICAL fail-closed.
    if "crates/sens/src/eval/builtins.rs" not in CANONICAL:
        raise ValueError("migrated backend lost canonical-identity guard")
    for forbidden in ("use crate::Sens8;", "exact_args(crate::sens!(01010000), args, 1, span)?;"):
        if not inspect_code("crates/sens/src/eval/builtins.rs", forbidden):
            raise ValueError("canonical backend guard missed a legacy identity reintroduction")
    # Контроль колізій: числовий payload 1 НЕ визначає домен.
    same_payload = {(3, "001"), (4, "0001"), (5, "00001")}
    if len(same_payload) != 3 or {int(bits, 2) for _, bits in same_payload} != {1}:
        raise ValueError("D3/D4/D5 must never collapse by packed numeric payload")
    entries = [
        {"legacy_code": f"{i:08b}", "legacy_name": None,
         "classification": "UNNAMED-LEGACY-IDENTITY", "current_target": None}
        for i in range(256)
    ]
    for bits, (name, classification, target, _) in W8_COLLISION.items():
        entry = entries[int(bits, 2)]
        entry["legacy_name"] = name
        entry["classification"] = classification
        entry["current_target"] = target
    synthetic = {"status": "AUDIT-COMPLETE", "rows": entries}
    d8_sample = "\n".join(
        f"({bits} (en {label}) (sym ()))"
        for bits, (_, _, _, label) in W8_COLLISION.items()
    )
    inspect_w8_d8_collision(synthetic, d8_sample)
    # Кожен мутаційний негатив повинен впасти, а не «мігрувати» функцію.
    mutation_cases = [
        ({"status": "AUDIT-COMPLETE", "rows": entries[:-1]}, d8_sample),
        ({"status": "UNVERIFIED", "rows": entries}, d8_sample),
        (synthetic, d8_sample.replace("(en round)", "(en invoke)")),
        (synthetic, d8_sample.replace("(en 1/)", "(en read-file)")),
    ]
    for corrupted, table in mutation_cases:
        try:
            inspect_w8_d8_collision(corrupted, table)
        except ValueError:
            pass
        else:
            raise ValueError("W8/D8 collision mutation was incorrectly admitted")
    held = {"status": "AUDIT-COMPLETE", "rows": [dict(row) for row in entries]}
    held["rows"][int("10101000", 2)]["current_target"] = "D8:10101000"
    try:
        inspect_w8_d8_collision(held, d8_sample)
    except ValueError:
        pass
    else:
        raise ValueError("legacy INVOKE incorrectly admitted as D8 ROUND")
    print("DOMAIN-LADDER-IDENTITY: self-test PASS (Rust/Python/C/Lisp, D3/D4/D5, W8/D8 negative controls)")


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
