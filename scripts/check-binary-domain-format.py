#!/usr/bin/env python3
"""Check binary-domain fields after explicit semantic/mechanism scope classification.

Slice 0 — SCHEMA-SCOPE (#2552): explicit SEMANTIC vs MECHANISM boundary.
Slice 1 — DOMAIN (#2513 + #2540): law-bearing semantic context or honest UNKNOWN.
Slice 2 — RELATION (#2514): exact enum token.
Slice 3 — WITNESS (#2561): verifiable evidence reference.
Slice 4 — FALSIFIER (#2574): concrete falsification condition.
Slice 5 — STATUS (#2575): exact enum token from declared set.

Usage:
    python3 scripts/check-binary-domain-format.py --self-test
    python3 scripts/check-binary-domain-format.py --issues snap.json \
        --baseline knowledge/binary-domain-format-baseline.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from task_schema_record import parse_record

BLOCK = re.compile(r"BINARY-DOMAIN\s+FORMAT", re.I)


def _heading_text(b, m):
    rest = (m.group(1) or "").strip()
    if rest:
        return rest
    for line in b[m.end() :].splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("```") or re.match(
            r"^[A-Z][A-Z _/-]{2,}\s*:", s
        ):
            return ""
        return s
    return ""


def field_value(body, label):
    """Return (kind, text) for the field, preferring a filled value over the legend.

    Three shapes occur in the wild, and a body may carry more than one. The label
    may carry a plural `s` (`## Falsifiers`) but must not be a prefix of a longer
    word, or the tail would be read as the value. A body that quotes the format
    preamble carries the legend first; the legend is a *description* of the field,
    not its value, so the first non-legend occurrence wins and the legend is only
    returned when nothing else is present.
    """
    b = body or ""
    pats = (
        (
            "value",
            re.compile(
                rf"^[ \t]*#{{1,6}}[ \t]*\**{label}s?(?![A-Za-z0-9_])(?:[ \t]*:[ \t]*(.*)|[ \t]*)$",
                re.I | re.M,
            ),
            True,
        ),
        (
            "value",
            re.compile(
                rf"^[ \t]*(?:[-*][ \t]*)?\**{label}s?(?![A-Za-z0-9_])[ \t]*:[ \t]*(.*)$",
                re.I | re.M,
            ),
            False,
        ),
        (
            "twocol",
            re.compile(
                rf"^[ \t]*\**{label}s?(?![A-Za-z0-9_])[ \t]{{2,}}(\S.*)$", re.I | re.M
            ),
            False,
        ),
    )
    cands = []
    for kind, rx, is_heading in pats:
        for m in rx.finditer(b):
            text = _heading_text(b, m) if is_heading else m.group(1).strip()
            cands.append((m.start(), kind, text))
    if not cands:
        return (None, None)
    cands.sort(key=lambda c: c[0])
    legend = LEGEND_TEXT.get(label)
    for _pos, kind, text in cands:
        if not (text and legend and legend.search(text)):
            return (kind, text)
    return (cands[0][1], cands[0][2])


LEGEND_TEXT = {
    "DOMAIN": re.compile(r"^(?:exact width/type/carrier|law-bearing semantic context)\b", re.I),
    "RELATION": re.compile(
        r"^(?:Core-only\s*\|\s*Core-Math-only\s*\|\s*bridge-candidate\s*\|\s*"
        r"shared-proved-law)\b",
        re.I,
    ),
    "WITNESS": re.compile(r"^executable\b[^\n]*\bevidence\b", re.I),
    "FALSIFIER": re.compile(
        r"^explicit counter-test\b|^observable failure condition\b",
        re.I,
    ),
    "STATUS": re.compile(
        r"^(?:hypothesis\s*\|\s*generated\s*\|\s*ratified\s*\|\s*falsified\s*\|\s*unknown)\b",
        re.I,
    ),
}

LAYER_MECHANISM = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?LAYER(?:\*\*)?\s*(?:=|:)\s*MECHANISM\s*$"
)
SEMANTIC_AUTHORITY_NONE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?SEMANTIC[ _-]+AUTHORITY(?:\*\*)?\s*(?:=|:)\s*NONE\s*$"
)

VIOLATION_SCOPE = {
    "mechanism-missing-nonauthority",
    "nonauthority-without-mechanism",
    "mechanism-semantic-conflict",
}


def _scope_metadata_text(body):
    """Return only task-level scope metadata, excluding nested examples/ledgers.

    Scope declarations are admitted from:
    - the preamble before the first level-2 section;
    - an explicit level-2 `## LAYER ...` section.

    A nested ledger row that happens to say `LAYER = MECHANISM` must not
    reclassify the whole issue.
    """
    b = body or ""
    chunks = []

    first_h2 = re.search(r"(?m)^##[ \t]+\S", b)
    chunks.append(b[: first_h2.start() if first_h2 else len(b)])

    layer_heading = re.compile(r"(?im)^##[ \t]+LAYER\b[^\n]*$")
    for match in layer_heading.finditer(b):
        start = match.end()
        next_section = re.search(r"(?m)^#{1,2}[ \t]+\S", b[start:])
        end = start + next_section.start() if next_section else len(b)
        chunks.append(b[start:end])

    return "\n".join(chunks)


def schema_scope(body):
    """Classify task scope from explicit task-level declarations only."""
    b = body or ""
    meta = _scope_metadata_text(b)
    mechanism = bool(LAYER_MECHANISM.search(meta))
    nonauthority = bool(SEMANTIC_AUTHORITY_NONE.search(meta))

    if mechanism and not nonauthority:
        return "mechanism-missing-nonauthority"
    if nonauthority and not mechanism:
        return "nonauthority-without-mechanism"
    if mechanism and nonauthority:
        if parse_record(b).marked:
            return "mechanism-semantic-conflict"
        return "mechanism"
    return "semantic"


SEMANTIC_DOMAIN = re.compile(
    r"\bD\d+(?:\.[A-Za-z][A-Za-z0-9._-]*)?\b|"
    r"\b(?:Core[.-]Number[.-]D\d+[A-Za-z0-9._-]*|"
    r"Core\.Number\.D\d+[A-Za-z0-9._-]*|"
    r"CoreMath\.[A-Za-z][A-Za-z0-9._-]*|"
    r"Core-Math[.-][A-Z][A-Za-z0-9._-]*)\b|"
    r"\b(?:Function\d+|Sound\d+)\b|"
    r"\bexact-Q\b",
    re.I,
)
CARRIER_ONLY = re.compile(
    r"^(?:W\d+|\d+-bit|binary source word)(?:\s|$|\[|\()",
    re.I,
)
MECHANISM_ONLY = re.compile(
    r"^(?:FPGA|CPU|GPU|CUDA|backend|Limb\d+|x86(?:-64)?|"
    r"runtime-[A-Za-z0-9-]+|historical-gc-donor)(?:\s|$|/|\[|\()",
    re.I,
)
HONEST_UNKNOWN = re.compile(
    r"\b(?:unknown|not yet determined|not yet fixed|not yet known|"
    r"discovered per family|discovered per domain|no universal width|"
    r"not assumed|to be discovered|unfixed|pending proof)\b",
    re.I,
)
CIRCULAR = re.compile(
    r"(selected by the (?:admitted )?law|chosen by the (?:admitted )?law|"
    r"in which the (?:admitted )?law operates|the law (?:selects|chooses)|"
    r"domain (?:selected|chosen) by|domain in which the law)",
    re.I,
)

RELATION_OK = re.compile(
    r"^(?:Core-only|Core-Math-only|bridge-candidate|shared-proved-law)\s*$",
    re.I,
)

ASPIRATIONAL = re.compile(
    r"\b(?:will be added|will be specified|TBD|planned|future|not yet added|to be added)\b",
    re.I,
)

WITNESS_EVIDENCE = re.compile(
    r"(?:#\d+|"
    r"(?:\.lisp|\.rs|\.py|\.yml|\.yaml|\.json|\.md|\.toml)\b|"
    r"(?:tests/|crates/|scripts/|benchmarks/|docs/|knowledge/)|"
    r"\b(?:cargo|python3|pytest|sens|gh|git)\b)",
    re.I,
)

FALSIFIER_CONDITION = re.compile(
    r"\b(?:if|when|unless|any|fails?|shows\s+that|refut(?:e|ed|es)|counter-?|"
    r"breaks?|violates?|contradicts?|disprov(?:e|ed|es)|diverges|overflows?|"
    r"mismatch|cannot|panics?|corrupts?)\b",
    re.I,
)

STATUSES = ("hypothesis", "generated", "ratified", "falsified", "unknown")


def domain_verdict(value):
    if value is None:
        return "missing"
    if not value:
        return "empty"
    if LEGEND_TEXT["DOMAIN"].search(value):
        return "legend"
    if CIRCULAR.search(value):
        return "circular"
    if HONEST_UNKNOWN.search(value):
        return "unknown"
    # A semantic context may carry width metadata, but the carrier does not
    # become the semantic identity.
    if SEMANTIC_DOMAIN.search(value):
        return "domain-ok"
    plain = value.strip(" `'\"")
    normalized = plain.lower()
    if CARRIER_ONLY.search(plain):
        return "carrier-only"
    if (
        MECHANISM_ONLY.search(plain)
        or "mechanism-only" in normalized
        or normalized.startswith("runtime-")
        or normalized.startswith("historical-gc-donor")
    ):
        return "mechanism-only"
    return "vague"


def relation_verdict(value, body=""):
    if value is None:
        return "missing"
    if not value:
        return "empty"
    if LEGEND_TEXT["RELATION"].search(value):
        return "legend"
    if RELATION_OK.match(value.strip()):
        if value.strip().lower() == "shared-proved-law":
            if not re.search(r"\b(?:witness|PR\s*#\d+|#\d+)\b", body or "", re.I):
                return "unproved-shared-law"
        return "ok"
    return "prose"


def witness_verdict(value, body=""):
    if value is None:
        return "missing"
    if not value:
        return "empty"
    if LEGEND_TEXT["WITNESS"].search(value):
        return "legend"
    if ASPIRATIONAL.search(value):
        return "aspirational"
    if WITNESS_EVIDENCE.search(value):
        return "ok"
    return "prose"


def falsifier_verdict(value, body=""):
    if value is None:
        return "missing"
    if not value:
        return "empty"
    if LEGEND_TEXT["FALSIFIER"].search(value):
        return "legend"
    if ASPIRATIONAL.search(value):
        return "aspirational"
    if FALSIFIER_CONDITION.search(value):
        return "ok"
    return "vague"


def status_verdict(value, body=""):
    if value is None:
        return "missing"
    if not value:
        return "empty"
    norm = re.sub(r"[`'\".,;]+", "", value).strip().lower()
    norm = re.sub(r"\s+", " ", norm)
    # the legend is the declared enum, not any private scale that happens to
    # contain one declared token behind a pipe (those are `foreign`, below)
    if LEGEND_TEXT["STATUS"].search(value) or all(tok in norm for tok in STATUSES):
        return "legend"
    if norm in STATUSES:
        return "ok"
    return "foreign"


FIELDS = (
    ("domain", "DOMAIN", domain_verdict),
    ("relation", "RELATION", relation_verdict),
    ("witness", "WITNESS", witness_verdict),
    ("falsifier", "FALSIFIER", falsifier_verdict),
    ("status", "STATUS", status_verdict),
)


def _declares_real_field(body, label):
    """True when an unscoped body already carries a non-empty, non-legend field value."""
    _, value = field_value(body, label)
    if value is None or not value:
        return False
    legend = LEGEND_TEXT.get(label)
    return not (legend and legend.search(value))


def scope_stats(issues):
    """Describe semantic/mechanism governance without inferring scope from names."""
    open_issues = [
        it for it in issues
        if str(it.get("state", "open")).lower() == "open"
    ]

    semantic_marked = []
    mechanism = []
    scope_errors = []
    unscoped_semantic = []

    for it in open_issues:
        body = it.get("body") or ""
        scope = schema_scope(body)
        if scope == "mechanism":
            mechanism.append(it)
        elif scope in VIOLATION_SCOPE:
            scope_errors.append(it)
        elif BLOCK.search(body):
            semantic_marked.append(it)
        else:
            unscoped_semantic.append(it)

    declarations = {}
    declared_issue_numbers = set()
    for _key, label, _rule in FIELDS:
        numbers = [
            it.get("number")
            for it in unscoped_semantic
            if _declares_real_field(it.get("body") or "", label)
        ]
        declarations[label.lower()] = len(numbers)
        declared_issue_numbers.update(number for number in numbers if number is not None)

    return {
        "scope": "semantic-format-or-explicit-mechanism",
        "open": len(open_issues),
        "judged": len(semantic_marked) + len(mechanism) + len(scope_errors),
        "semantic_marked": len(semantic_marked),
        "mechanism": len(mechanism),
        "scope_errors": len(scope_errors),
        "unscoped_open": len(unscoped_semantic),
        "unscoped_with_declared_fields": len(declared_issue_numbers),
        "outside_scope_declarations": declarations,
    }


def judge(issues, requested_fields=None):
    if requested_fields is None:
        requested_fields = tuple(k for k, _, _ in FIELDS)
    judged, skipped = [], 0

    for it in issues:
        body = it.get("body") or ""
        if str(it.get("state", "open")).lower() != "open":
            skipped += 1
            continue

        scope = schema_scope(body)

        if scope == "mechanism" or scope in VIOLATION_SCOPE:
            entry = {
                "number": it.get("number"),
                "title": it.get("title", ""),
                "scope": scope,
            }
            for key, _label, _rule in FIELDS:
                if key in requested_fields:
                    entry[key] = "not-applicable"
                    entry[f"{key}_value"] = None
            judged.append(entry)
            continue

        if not BLOCK.search(body):
            skipped += 1
            continue

        entry = {
            "number": it.get("number"),
            "title": it.get("title", ""),
            "scope": "semantic",
        }
        for key, label, rule in FIELDS:
            if key in requested_fields:
                _, val = field_value(body, label)
                entry[key] = rule(val, body) if key == "relation" else rule(val)
                entry[f"{key}_value"] = val
        judged.append(entry)

    return judged, skipped


VIOLATION_RULES = {
    "domain": {"carrier-only", "mechanism-only", "circular", "empty", "vague", "missing", "legend"},
    "relation": {"prose", "empty", "missing", "legend", "unproved-shared-law"},
    "witness": {"prose", "empty", "missing", "legend", "aspirational"},
    "falsifier": {"vague", "empty", "missing", "legend", "aspirational"},
    "status": {"foreign", "empty", "missing", "legend"},
}


def self_test():
    mechanism = """## LAYER

LAYER = MECHANISM
SEMANTIC AUTHORITY = NONE
"""
    assert schema_scope(mechanism) == "mechanism"
    assert schema_scope("LAYER = MECHANISM\n") == "mechanism-missing-nonauthority"
    assert schema_scope("SEMANTIC AUTHORITY = NONE\n") == "nonauthority-without-mechanism"
    assert schema_scope("codec GC FPGA runtime\n") == "semantic"
    assert schema_scope(
        "## Ledger\n\n```text\nLAYER = MECHANISM\n```\n"
    ) == "semantic"
    assert schema_scope(
        "## LAYER\n\n```text\nLAYER = MECHANISM\nSEMANTIC AUTHORITY = NONE\n```\n"
    ) == "mechanism"
    assert schema_scope(
        mechanism
        + "\n## BINARY-DOMAIN RECORD\n"
        + "DOMAIN: D5\nBINARY OBJECT: 00101\nLAW: x\n"
        + "WITNESS: #1\nFALSIFIER: if x fails\nSTATUS: hypothesis\n"
        + "RELATION: Core-only\n"
    ) == "mechanism-semantic-conflict"

    mechanism_rows, mechanism_skipped = judge([
        {"number": 80, "state": "open", "body": mechanism},
        {"number": 81, "state": "open", "body": "LAYER: MECHANISM\n"},
        {"number": 82, "state": "open", "body": "SEMANTIC AUTHORITY: NONE\n"},
    ])
    assert mechanism_skipped == 0
    assert [row["scope"] for row in mechanism_rows] == [
        "mechanism",
        "mechanism-missing-nonauthority",
        "nonauthority-without-mechanism",
    ]
    assert mechanism_rows[0]["domain"] == "not-applicable"
    assert mechanism_rows[0]["relation"] == "not-applicable"

    cases = [
        # DOMAIN
        ("d-ok", "DOMAIN: D5", "domain", "domain-ok"),
        ("d-role", "DOMAIN: D7.SoundCell [carrier=W7]", "domain", "domain-ok"),
        ("d-local-ordinal", "DOMAIN: D7.LocalOrdinal [carrier=W7]", "domain", "domain-ok"),
        ("d-number", "DOMAIN: Core.Number.D24Z-candidate [carrier=W24]", "domain", "domain-ok"),
        ("d-exact-q", "DOMAIN: CoreMath.ExactQ [carrier=variable]", "domain", "domain-ok"),
        ("d-unknown", "DOMAIN: UNKNOWN", "domain", "unknown"),
        ("d-carrier-w", "DOMAIN: W7", "domain", "carrier-only"),
        ("d-carrier-bit", "DOMAIN: 7-bit", "domain", "carrier-only"),
        ("d-carrier-source", "DOMAIN: binary source word", "domain", "carrier-only"),
        ("d-mechanism-fpga", "DOMAIN: FPGA", "domain", "mechanism-only"),
        ("d-mechanism-limb", "DOMAIN: Limb24", "domain", "mechanism-only"),
        ("d-circular", "DOMAIN: Exact Core-Math domain selected by the admitted law.", "domain", "circular"),
        ("d-vague", "DOMAIN: One explicit Core-Math binary domain at a time.", "domain", "vague"),
        ("d-empty", "## DOMAIN\n\n## LAW\nx", "domain", "empty"),
        ("d-legend", "DOMAIN        exact width/type/carrier", "domain", "legend"),
        # RELATION
        ("r-ok", "RELATION: Core-only", "relation", "ok"),
        ("r-bridge", "RELATION: bridge-candidate", "relation", "ok"),
        ("r-shared-witness", "RELATION: shared-proved-law\nWITNESS: #2522", "relation", "ok"),
        ("r-shared-nowitness", "RELATION: shared-proved-law\n", "relation", "unproved-shared-law"),
        ("r-prose", "RELATION: transport only", "relation", "prose"),
        ("r-legend", "RELATION: Core-only | Core-Math-only | bridge-candidate | shared-proved-law", "relation", "legend"),
        # WITNESS
        ("w-ok-issue", "WITNESS: PR #2592", "witness", "ok"),
        ("w-ok-file", "WITNESS: crates/sens/tests/exact_q.rs", "witness", "ok"),
        ("w-ok-runner", "WITNESS: cargo test -p sens", "witness", "ok"),
        ("w-legend", "WITNESS: executable evidence", "witness", "legend"),
        ("w-aspirational", "WITNESS: will be added after D5", "witness", "aspirational"),
        ("w-prose", "WITNESS: Positive controls and manual observation", "witness", "prose"),
        ("w-empty", "WITNESS:\n", "witness", "empty"),
        # FALSIFIER
        ("f-ok-if", "FALSIFIER: if any test fails or diverges", "falsifier", "ok"),
        ("f-ok-when", "FALSIFIER: when stack overflow occurs", "falsifier", "ok"),
        ("f-legend", "FALSIFIER: explicit counter-test", "falsifier", "legend"),
        ("f-aspirational", "FALSIFIER: will be specified later", "falsifier", "aspirational"),
        ("f-vague", "FALSIFIER: none", "falsifier", "vague"),
        ("f-empty", "FALSIFIER:\n", "falsifier", "empty"),
        # STATUS
        ("s-ok-hypo", "STATUS: hypothesis", "status", "ok"),
        ("s-ok-ratified", "STATUS: ratified", "status", "ok"),
        ("s-ok-unknown", "STATUS: unknown", "status", "ok"),
        ("s-foreign", "STATUS: READY-FOR-OWNER", "status", "foreign"),
        ("s-foreign-target", "STATUS: implementation-target", "status", "foreign"),
        ("s-legend", "STATUS: hypothesis | generated | ratified | falsified | unknown", "status", "legend"),
        ("s-empty", "STATUS:\n", "status", "empty"),
        # extraction: a plural section heading must not be read as a value,
        # and the preamble legend must not hide a filled value below it
        ("d-plural-heading", "## DOMAINS\nD5", "domain", "domain-ok"),
        ("f-plural-heading", "## Falsifiers\nif the law fails", "falsifier", "ok"),
        ("f-legend-then-real", "FALSIFIER        explicit counter-test\nFALSIFIER: if the law fails",
         "falsifier", "ok"),
        # rule quality: the WITNESS legend has variants, and a private status scale
        # is `foreign`, not `legend`, even when it contains a declared token
        ("w-legend-variant", "WITNESS: executable or source-grounded evidence", "witness", "legend"),
        ("s-private-enum", "STATUS: confirmed | partial | hypothesis", "status", "foreign"),
    ]

    field_map = {k: rule for k, _, rule in FIELDS}
    failures = 0
    for name, text, f_key, expected in cases:
        body = f"BINARY-DOMAIN FORMAT\n{text}\n"
        _, v = field_value(body, f_key.upper())
        got = relation_verdict(v, body) if f_key == "relation" else field_map[f_key](v)
        if got != expected:
            print(f"  [FAIL] {name}: got {got!r}, expected {expected!r}")
            failures += 1

    # Scope guard: unmarked semantic legacy prose stays outside the ratchet,
    # while explicit mechanism declarations are governed without fake DOMAIN.
    scope_fixture = [
        {"number": 90, "title": "legacy", "state": "open", "body": "## DOMAIN\nD5\nRELATION: prose only\n"},
        {"number": 91, "title": "closed", "state": "closed", "body": "BINARY-DOMAIN FORMAT\nDOMAIN: D5\n"},
        {"number": 92, "title": "semantic", "state": "open", "body": "BINARY-DOMAIN FORMAT\nDOMAIN: D5\n"},
        {"number": 93, "title": "mechanism", "state": "open", "body": mechanism},
        {"number": 94, "title": "bad mechanism", "state": "open", "body": "LAYER: MECHANISM\n"},
    ]
    scoped, skipped = judge(scope_fixture)
    stats = scope_stats(scope_fixture)
    if len(scoped) != 3 or skipped != 2:
        print(f"  [FAIL] scope guard: scoped={scoped}, skipped={skipped}")
        failures += 1
    if stats != {
        "scope": "semantic-format-or-explicit-mechanism",
        "open": 4,
        "judged": 3,
        "semantic_marked": 1,
        "mechanism": 1,
        "scope_errors": 1,
        "unscoped_open": 1,
        "unscoped_with_declared_fields": 1,
        "outside_scope_declarations": {
            "domain": 1,
            "relation": 1,
            "witness": 0,
            "falsifier": 0,
            "status": 0,
        },
    }:
        print(f"  [FAIL] scope diagnostics: {stats}")
        failures += 1


    if failures:
        print(f"binary-domain-selftest-failed ({failures})")
        return 1

    print("SCHEMA-SCOPE-MECHANISM=PASS")
    print("SCHEMA-SCOPE-INCOMPLETE-FAIL-CLOSED=PASS")
    print("SCHEMA-SCOPE-NO-NAME-GUESSING=PASS")
    print("SCHEMA-SCOPE-CONFLICT=PASS")
    print(f"(binary-domain-selftest-ok ({len(cases) + 7} cases, 5 fields + scope))")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issues", type=str, help="JSON snapshot of issues")
    ap.add_argument("--baseline", type=str, help="baseline violations JSON")
    ap.add_argument("--emit-baseline", action="store_true", help="emit baseline JSON for current snapshot")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.issues:
        print("need --issues or --self-test", file=sys.stderr)
        return 2

    data = json.load(open(args.issues, encoding="utf-8"))
    issues = data["issues"] if isinstance(data, dict) else data

    if args.emit_baseline:
        judged, _ = judge(issues)
        baseline = {"violations": {}}
        baseline["violations"]["scope"] = sorted({
            row["number"]
            for row in judged
            if row.get("scope") in VIOLATION_SCOPE
        })
        for key in ("domain", "relation", "witness", "falsifier", "status"):
            bad = sorted({
                row["number"]
                for row in judged
                if row.get(key) in VIOLATION_RULES[key]
            })
            baseline["violations"][key] = bad
        print(json.dumps(baseline, indent=2))
        return 0


    baseline = {"violations": {}}
    if args.baseline:
        b = json.load(open(args.baseline, encoding="utf-8"))
        baseline["violations"] = b.get("violations", b)

    active_fields = tuple(k for k in ("domain", "relation", "witness", "falsifier", "status") if k in baseline["violations"])
    judged, skipped = judge(issues, requested_fields=active_fields)
    scope = scope_stats(issues)

    known_scope = set(baseline["violations"].get("scope", []))
    new_scope = [
        row for row in judged
        if row.get("scope") in VIOLATION_SCOPE and row["number"] not in known_scope
    ]

    def known_violation(key, row, known):
        if row["number"] in known:
            return True
        # #2555 is the classifier cutover. Carrier/mechanism DOMAIN debt from
        # older semantic tasks remains visible but does not become a retroactive
        # blanket failure; new tasks must use semantic DOMAIN or explicit
        # mechanism scope.
        return (
            key == "domain"
            and row.get("domain") in {"carrier-only", "mechanism-only"}
            and isinstance(row.get("number"), int)
            and row["number"] < 2556
        )

    new_violations = {}
    for key in active_fields:
        known = set(baseline["violations"].get(key, []))
        new_violations[key] = [
            row for row in judged
            if row.get(key) in VIOLATION_RULES[key] and not known_violation(key, row, known)
        ]

    summary_parts = [
        f"(scope {scope['scope']})",
        f"(open {scope['open']})",
        f"(judged {len(judged)})",
        f"(semantic-marked {scope['semantic_marked']})",
        f"(mechanism {scope['mechanism']})",
        f"(scope-errors {scope['scope_errors']})",
        f"(new-scope {len(new_scope)})",
    ]
    for key in active_fields:
        summary_parts.append(f"(new-{key} {len(new_violations[key])})")
    summary_parts.extend([
        f"(skipped {skipped})",
        f"(unscoped-open {scope['unscoped_open']})",
        f"(unscoped-with-declared-fields {scope['unscoped_with_declared_fields']})",
    ])

    print(f"(binary-domain-format {' '.join(summary_parts)})")
    outside = scope["outside_scope_declarations"]
    print(
        "(binary-domain-format-outside-scope "
        + " ".join(
            f"({key}-declared {outside[key]})"
            for key in ("domain", "relation", "witness", "falsifier", "status")
        )
        + ")"
    )

    has_new = bool(new_scope)
    for row in new_scope:
        print(f"  scope {row['scope']:32} #{row['number']}")

    for key in active_fields:
        if new_violations[key]:
            has_new = True
            for row in new_violations[key]:
                print(f"  {key} {row[key]:12} #{row['number']}  {row.get(f'{key}_value')!r}")

    return 1 if has_new else 0


if __name__ == "__main__":
    raise SystemExit(main())
