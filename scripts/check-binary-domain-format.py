#!/usr/bin/env python3
"""Check that the binary-domain format fields say something.

Slice 1 — DOMAIN (#2513): width/carrier or honest UNKNOWN.
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
    "DOMAIN": re.compile(r"^exact width/type/carrier\b", re.I),
    "RELATION": re.compile(
        r"^(?:Core-only\s*\|\s*Core-Math-only\s*\|\s*bridge-candidate\s*\|\s*"
        r"shared-proved-law)\b",
        re.I,
    ),
    "WITNESS": re.compile(
        r"^executable evidence\b|^executable/documentary evidence\b",
        re.I,
    ),
    "FALSIFIER": re.compile(
        r"^explicit counter-test\b|^observable failure condition\b",
        re.I,
    ),
    "STATUS": re.compile(
        r"^(?:hypothesis\s*\|\s*generated\s*\|\s*ratified\s*\|\s*falsified\s*\|\s*unknown)\b",
        re.I,
    ),
}

CONCRETE = re.compile(
    r"\b(?:W\d+|D\d+|Function\d+|Sound\d+)[A-Za-z]*\b|"
    r"\bexact-[A-Za-z0-9]+\b|\b\d+-bit\b|"
    r"\b(?:śloka|sūtra|pāṇini|fpga|binary source word)\b",
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
    if CONCRETE.search(value):
        return "ok"
    if CIRCULAR.search(value):
        return "circular"
    if HONEST_UNKNOWN.search(value):
        return "ok"
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
    if LEGEND_TEXT["STATUS"].search(value) or ("|" in norm and any(tok in norm for tok in STATUSES)):
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


def judge(issues, requested_fields=None):
    if requested_fields is None:
        requested_fields = tuple(k for k, _, _ in FIELDS)
    judged, skipped = [], 0
    for it in issues:
        body = it.get("body") or ""
        if str(it.get("state", "open")).lower() != "open":
            skipped += 1
            continue
        has_block = bool(BLOCK.search(body))
        if not has_block:
            skipped += 1
            continue
        entry = {
            "number": it.get("number"),
            "title": it.get("title", ""),
        }
        for key, label, rule in FIELDS:
            if key in requested_fields:
                _, val = field_value(body, label)
                entry[key] = rule(val, body) if key == "relation" else rule(val)
                entry[f"{key}_value"] = val
        judged.append(entry)
    return judged, skipped


VIOLATION_RULES = {
    "domain": {"circular", "empty", "vague", "missing", "legend"},
    "relation": {"prose", "empty", "missing", "legend", "unproved-shared-law"},
    "witness": {"prose", "empty", "missing", "legend", "aspirational"},
    "falsifier": {"vague", "empty", "missing", "legend", "aspirational"},
    "status": {"foreign", "empty", "missing", "legend"},
}


def self_test():
    cases = [
        # DOMAIN
        ("d-ok", "DOMAIN: D5", "domain", "ok"),
        ("d-unknown", "DOMAIN: UNKNOWN", "domain", "ok"),
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
        ("d-plural-heading", "## DOMAINS\nD5", "domain", "ok"),
        ("f-plural-heading", "## Falsifiers\nif the law fails", "falsifier", "ok"),
        ("f-legend-then-real", "FALSIFIER        explicit counter-test\nFALSIFIER: if the law fails",
         "falsifier", "ok"),
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

    # Scope guard: issues without BINARY-DOMAIN FORMAT are ignored
    scoped, skipped = judge([
        {"number": 90, "title": "legacy", "state": "open", "body": "## DOMAIN pass rule\nRELATION: prose only\n"},
        {"number": 91, "title": "closed", "state": "closed", "body": "BINARY-DOMAIN FORMAT\nDOMAIN: D5\n"},
    ])
    if scoped or skipped != 2:
        print(f"  [FAIL] scope guard: scoped={scoped}, skipped={skipped}")
        failures += 1

    if failures:
        print(f"binary-domain-selftest-failed ({failures})")
        return 1

    print(f"(binary-domain-selftest-ok ({len(cases) + 2} cases, 5 fields))")
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

    new_violations = {}
    for key in active_fields:
        known = set(baseline["violations"].get(key, []))
        new_violations[key] = [
            row for row in judged
            if row.get(key) in VIOLATION_RULES[key] and row["number"] not in known
        ]

    summary_parts = [f"(judged {len(judged)})"]
    for key in active_fields:
        summary_parts.append(f"(new-{key} {len(new_violations[key])})")
    summary_parts.append(f"(skipped {skipped})")

    print(f"(binary-domain-format {' '.join(summary_parts)})")

    has_new = False
    for key in active_fields:
        if new_violations[key]:
            has_new = True
            for row in new_violations[key]:
                print(f"  {key} {row[key]:12} #{row['number']}  {row.get(f'{key}_value')!r}")

    return 1 if has_new else 0


if __name__ == "__main__":
    raise SystemExit(main())
