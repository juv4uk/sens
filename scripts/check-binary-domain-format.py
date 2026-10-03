#!/usr/bin/env python3
"""Check that the binary-domain format fields say something.

The binary-domain reformat (#2490) requires every task body to fill a small set
of fields. In practice the fields are often *present but empty of content*: the
preamble's legend (a two-column layout, `LABEL` + spaces + a description of what
the field should be) is mistaken for a filled value, and other values define the
thing by itself.

This checker gives each field a named verdict and fails closed on the ones that
say nothing.

Slice 1 — DOMAIN (#2513)
    ok        names a concrete width/carrier (W8, D5, Function8, exact-Q, 8-bit)
    ok        says UNKNOWN, or states an explicit honest uncertainty
    circular  defers to the law/domain itself ("selected by the admitted law")
    legend    only the format legend was copied, no value was filled
    empty     the field is present but blank
    vague     neither concrete nor an honest unknown
    missing   the body carries the reformat block but no DOMAIN field

Slice 2 — RELATION (#2539)
    ok                     exactly one of: Core-only | Core-Math-only |
                           bridge-candidate | shared-proved-law
    ok                     shared-proved-law WITH an executable witness
    unproved-shared-law    claims a proved shared law but cites no witness
    legend / empty / missing / prose
                           the enum was not filled (free prose is not a relation)

Slice 3 — WITNESS (#2561)
    ok             names checkable evidence: a PR/issue ref (#123), a witness
                   file path, or a runner (cargo, python3, pytest, sens, gh)
    legend         the copied legend ("executable evidence") — not a witness
    aspirational   promises evidence later ("will be added", TBD, planned);
                   a state without a witness belongs in STATUS, not here
    prose / empty / missing

Slice 4 — FALSIFIER (#2574)
    ok             names a condition under which the claim fails (if, when,
                   unless, fails, counter-, refutes, breaks, violates, disproves)
    legend         the copied legend ("explicit counter-test") — not a condition
    aspirational   promises a falsifier later (TBD, planned, will be added)
    vague / empty / missing

Slice 5 — STATUS (#2575)
    ok             exactly one state from: hypothesis | generated | ratified |
                   falsified | unknown
    foreign        a status value outside the declared enum (e.g. implementation-target)
    legend / empty / missing

Shape discrimination
--------------------
    ## DOMAIN            heading, value on the next non-empty line
    DOMAIN: W8           inline
    DOMAIN        exact width/type/carrier
                         legend (label + 2+ spaces) — NOT a value

Scope: only OPEN issues. A body is judged when it declares the field at all, or
when it carries the reformat block (so a block with no field is a finding).

The checker never touches the network. CI supplies a snapshot, so the rule is
provable locally.

Usage
-----
    python3 scripts/check-binary-domain-format.py --issues snapshot.json
    python3 scripts/check-binary-domain-format.py --issues snap.json \
        --baseline knowledge/binary-domain-format-baseline.json
    python3 scripts/check-binary-domain-format.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys

BLOCK = re.compile(r"BINARY-DOMAIN\s+FORMAT", re.I)

# --- shape extraction --------------------------------------------------------

def _heading_text(b, m):
    rest = m.group(1).strip()
    if rest:
        return rest
    for line in b[m.end():].splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("```") or re.match(r"^[A-Z][A-Z _/-]{2,}\s*:", s):
            return ""
        return s
    return ""


def field_value(body, label):
    """Return (kind, text) for the FIRST occurrence in document order.

    Three shapes occur in the wild, and a body may carry more than one, so the
    earliest one wins: heading (`## DOMAIN` + next line), inline (`DOMAIN: x`),
    two-column (`DOMAIN` + spaces + x — used for both the legend and real values).
    """
    b = body or ""
    pats = (
        ("value", re.compile(rf"^[ \t]*#{{1,6}}[ \t]*\**{label}\**[ \t]*:?[ \t]*(.*)$", re.I | re.M), True),
        ("value", re.compile(rf"^[ \t]*(?:[-*][ \t]*)?\**{label}\**[ \t]*:[ \t]*(.*)$", re.I | re.M), False),
        ("twocol", re.compile(rf"^[ \t]*\**{label}\**[ \t]{{2,}}(\S.*)$", re.I | re.M), False),
    )
    best = None
    for kind, rx, is_heading in pats:
        m = rx.search(b)
        if not m:
            continue
        text = _heading_text(b, m) if is_heading else m.group(1).strip()
        if best is None or m.start() < best[0]:
            best = (m.start(), kind, text)
    return (best[1], best[2]) if best else (None, None)


# The preamble's generic legend text. Only these exact descriptions are legends;
# the same two-column layout is used for real values, so content decides.
LEGEND_TEXT = {
    "DOMAIN": re.compile(r"^exact width/type/carrier\b", re.I),
    "RELATION": re.compile(
        r"^(?:Core-only\s*\|\s*Core-Math-only\s*\|\s*bridge-candidate\s*\|\s*"
        r"shared-proved-law)\b", re.I),
    "WITNESS": re.compile(r"^executable\b[^\n]*\bevidence\b", re.I),
    "FALSIFIER": re.compile(r"^explicit\s+counter-test\b", re.I),
    "STATUS": re.compile(
        r"^hypothesis\s*\|\s*generated\s*\|\s*ratified\s*\|\s*falsified\s*\|\s*unknown\b", re.I),
}


# --- DOMAIN ------------------------------------------------------------------

CONCRETE = re.compile(
    r"\b(?:W\d+|D\d+|Function\d+|Sound\d+)[A-Za-z]*\b|"
    r"\bexact-[A-Za-z0-9]+\b|\b\d+-bit\b|"
    r"\b(?:śloka|sūtra|pāṇini|fpga|binary source word)\b", re.I)
HONEST_UNKNOWN = re.compile(
    r"\b(?:unknown|not yet determined|not yet fixed|not yet known|"
    r"discovered per family|discovered per domain|no universal width|"
    r"not assumed|to be discovered|unfixed|pending proof)\b", re.I)
CIRCULAR = re.compile(
    r"(selected by the (?:admitted )?law|chosen by the (?:admitted )?law|"
    r"in which the (?:admitted )?law operates|the law (?:selects|chooses)|"
    r"domain (?:selected|chosen) by|domain in which the law)", re.I)


def domain_verdict(kind, text, body=""):
    if kind is None:
        return "missing"
    if text and LEGEND_TEXT["DOMAIN"].search(text):
        return "legend"
    if not text:
        return "empty"
    if CONCRETE.search(text):
        return "ok"
    if CIRCULAR.search(text):
        return "circular"
    if HONEST_UNKNOWN.search(text):
        return "ok"
    return "vague"


# --- RELATION ----------------------------------------------------------------

RELATIONS = ("core-only", "core-math-only", "bridge-candidate", "shared-proved-law")
# executable evidence: a PR/issue ref, a file path, or a known runner
EVIDENCE = re.compile(
    r"(#\d+|[\w./-]+\.(?:lisp|rs|py|json|tsv|yml)|\b(?:cargo|python3|pytest|sens|gh)\b|tests/)", re.I)


def relation_verdict(kind, text, body=""):
    if kind is None:
        return "missing"
    if text and LEGEND_TEXT["RELATION"].search(text):
        return "legend"
    if not text:
        return "empty"
    norm = re.sub(r"[`'\".,;]+", "", text).strip().lower()
    norm = re.sub(r"\s+", " ", norm)
    if norm in RELATIONS:
        if norm == "shared-proved-law":
            wkind, wtext = field_value(body, "WITNESS")
            if wkind != "value" or not wtext or not EVIDENCE.search(wtext):
                return "unproved-shared-law"
        return "ok"
    # the legend string copied verbatim as a value
    if "|" in norm and all(tok in norm for tok in RELATIONS):
        return "legend"
    return "prose"


# --- WITNESS -----------------------------------------------------------------

# promising evidence later is not evidence
ASPIRATIONAL = re.compile(
    r"\b(?:will be added|to be added|to be written|to be provided|TBD|planned|not yet|pending|coming soon)\b",
    re.I)


def witness_verdict(kind, text, body=""):
    if kind is None:
        return "missing"
    if text and LEGEND_TEXT["WITNESS"].search(text):
        return "legend"
    if not text:
        return "empty"
    if ASPIRATIONAL.search(text):
        return "aspirational"
    if EVIDENCE.search(text):
        return "ok"
    return "prose"


# --- FALSIFIER ---------------------------------------------------------------

FALSIFIER_CONDITION = re.compile(
    r"\b(?:if|when|unless|any|fails?|shows\s+that|refut(?:e|ed|es)|counter-?|breaks?|violates?|contradicts?|disprov(?:e|ed|es))\b",
    re.I)


def falsifier_verdict(kind, text, body=""):
    if kind is None:
        return "missing"
    if text and LEGEND_TEXT["FALSIFIER"].search(text):
        return "legend"
    if not text:
        return "empty"
    if ASPIRATIONAL.search(text):
        return "aspirational"
    if FALSIFIER_CONDITION.search(text):
        return "ok"
    return "vague"


# --- STATUS ------------------------------------------------------------------

STATUSES = ("hypothesis", "generated", "ratified", "falsified", "unknown")


def status_verdict(kind, text, body=""):
    if kind is None:
        return "missing"
    if text and LEGEND_TEXT["STATUS"].search(text):
        return "legend"
    if not text:
        return "empty"
    norm = re.sub(r"[`'\".,;]+", "", text).strip().lower()
    norm = re.sub(r"\s+", " ", norm)
    if norm in STATUSES:
        return "ok"
    if "|" in norm and all(tok in norm for tok in STATUSES):
        return "legend"
    return "foreign"


# --- judging -----------------------------------------------------------------

FIELDS = (("domain", "DOMAIN", domain_verdict), ("relation", "RELATION", relation_verdict),
          ("witness", "WITNESS", witness_verdict), ("falsifier", "FALSIFIER", falsifier_verdict),
          ("status", "STATUS", status_verdict))


def judge(issues, fields=("domain", "relation", "witness", "falsifier", "status")):
    """Return (judged, skipped); judged is [(field, number, title, verdict, text)]."""
    judged, skipped = [], 0
    for it in issues:
        body = it.get("body") or ""
        if str(it.get("state", "open")).lower() != "open":
            skipped += 1
            continue
        rows = []
        for key, label, rule in FIELDS:
            if key not in fields:
                continue
            kind, text = field_value(body, label)
            if kind is None and not BLOCK.search(body):
                continue
            verdict = rule(kind, text, body)
            rows.append((key, it.get("number"), it.get("title", ""), verdict, text))
        if not rows:
            skipped += 1
            continue
        judged.extend(rows)
    return judged, skipped


def run(path, baseline_path=None, emit=False, fields=("domain", "relation", "witness", "falsifier", "status")):
    data = json.load(open(path, encoding="utf-8"))
    issues = data["issues"] if isinstance(data, dict) else data
    judged, skipped = judge(issues, fields)
    bad = [j for j in judged if j[3] != "ok"]
    if emit:
        out = {}
        for key in fields:
            out[key] = sorted(j[1] for j in bad if j[0] == key)
        print(json.dumps({"violations": out}, indent=2))
        return 0
    known = {key: set() for key in fields}
    if baseline_path:
        raw = json.load(open(baseline_path, encoding="utf-8")).get("violations", {})
        if isinstance(raw, list):          # tolerate the flat slice-1 shape
            known["domain"] = set(raw)
        else:
            for key in fields:
                known[key] = set(raw.get(key, []))
    new = [j for j in bad if j[1] not in known.get(j[0], set())]
    for key, label, _rule in FIELDS:
        if key not in fields:
            continue
        rows = [j for j in judged if j[0] == key]
        rows_bad = [j for j in rows if j[3] != "ok"]
        rows_new = [j for j in rows_bad if j[1] not in known.get(key, set())]
        print(f"(binary-domain-format (field {key}) (judged {len(rows)}) "
              f"(ok {len(rows) - len(rows_bad)}) (known {len(rows_bad) - len(rows_new)}) "
              f"(new {len(rows_new)}))")
    print(f"(binary-domain-format (judged {len(judged)}) (skipped {skipped}))")
    for key, number, _t, verdict, text in bad:
        mark = "NEW " if number not in known.get(key, set()) else "    "
        print(f"  {mark}{key:8} {verdict:20} #{number}  {(text or '<blank>')[:64]}")
    if new:
        print("\nbinary-domain-violation: a format field names no value.")
        print("  DOMAIN: name a width/carrier (W8, D5, exact-Q, ...) or say UNKNOWN.")
        print("  RELATION: one of Core-only | Core-Math-only | bridge-candidate |")
        print("  shared-proved-law — free prose is not a relation.")
        return 1
    print("(binary-domain-ok)")
    return 0


# --- self-test ---------------------------------------------------------------

BLOCK_TEXT = "## BINARY-DOMAIN FORMAT — 2026-10-03\n\nAuthority: #2490.\n"


def issue(number, domain=None, relation=None, witness=None, falsifier=None, status=None,
          state="open", with_block=True, form="inline"):
    body = BLOCK_TEXT if with_block else ""
    if domain is not None:
        body += f"## DOMAIN\n{domain}\n" if form == "heading" else f"DOMAIN: {domain}\n"
    if relation is not None:
        body += f"RELATION: {relation}\n"
    if witness is not None:
        body += f"WITNESS: {witness}\n"
    if falsifier is not None:
        body += f"FALSIFIER: {falsifier}\n"
    if status is not None:
        body += f"STATUS: {status}\n"
    body += "LAW: something\n"
    return {"number": number, "title": "t", "body": body, "state": state}


SELFTEST = [
    # DOMAIN
    (issue(1, domain="W8"), "domain", "ok"),
    (issue(2, domain="exact-Q (rationals, zero excluded)"), "domain", "ok"),
    (issue(3, domain="UNKNOWN"), "domain", "ok"),
    (issue(4, domain="Core-Math binary domains. Exact widths/carriers are discovered per "
                      "family; no universal width is assumed"), "domain", "ok"),
    (issue(5, domain="Exact Core-Math domain selected by the admitted law"), "domain", "circular"),
    (issue(6, domain="Core-Math domain in which the admitted law operates"), "domain", "circular"),
    (issue(7, domain="One explicit Core-Math binary domain at a time"), "domain", "vague"),
    (issue(8, domain=""), "domain", "empty"),
    (issue(9, domain="W8", form="heading"), "domain", "ok"),
    (issue(10, domain="Exact Core-Math domain selected by the admitted law.", form="heading"),
     "domain", "circular"),
    ({"number": 11, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "LAW: x\n"}, "domain", "missing"),
    ({"number": 12, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "DOMAIN        exact width/type/carrier\n"}, "domain", "legend"),
    ({"number": 13, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "DOMAIN      D5 or D6 candidate/exact domain\n"}, "domain", "ok"),
    ({"number": 14, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "DOMAIN: Core-Number-D24Z and Core-Number-D48Z candidate carriers\n"},
     "domain", "ok"),
    # RELATION
    (issue(20, relation="Core-only"), "relation", "ok"),
    (issue(21, relation="bridge-candidate"), "relation", "ok"),
    (issue(22, relation="Core-only | Core-Math-only | bridge-candidate | shared-proved-law"),
     "relation", "legend"),
    ({"number": 23, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "RELATION      Core-only | Core-Math-only | bridge-candidate | "
                            "shared-proved-law\n"}, "relation", "legend"),
    (issue(24, relation="Shared governance method; no Core/Core-Math semantic bridge implied."),
     "relation", "prose"),
    (issue(25, relation="transport/mechanics only; domain meaning remains external."),
     "relation", "prose"),
    (issue(26, relation="shared-proved-law"), "relation", "unproved-shared-law"),
    (issue(27, relation=""), "relation", "empty"),
    ({"number": 28, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "LAW: x\n"}, "relation", "missing"),
    ({"number": 30, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "RELATION      Core-only\n"}, "relation", "ok"),
    # WITNESS
    ({"number": 40, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: tests/fixtures/exact-q-commutes.lisp\n"}, "witness", "ok"),
    ({"number": 41, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: PR #2529 dedicated gate = GREEN\n"}, "witness", "ok"),
    ({"number": 42, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: cargo test -p sens --test exact_q\n"}, "witness", "ok"),
    ({"number": 43, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS      executable evidence\n"}, "witness", "legend"),
    ({"number": 44, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: executable evidence in a bounded scope\n"},
     "witness", "legend"),
    ({"number": 49, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: executable/documentary evidence\n"}, "witness", "legend"),
    ({"number": 45, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: Positive controls:\n"}, "witness", "prose"),
    ({"number": 46, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: will be added once the D5 map lands\n"},
     "witness", "aspirational"),
    ({"number": 47, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "WITNESS: \n"}, "witness", "empty"),
    ({"number": 48, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "LAW: x\n"}, "witness", "missing"),
    # FALSIFIER (#2574)
    (issue(60, falsifier="fails if child bits do not match"), "falsifier", "ok"),
    (issue(61, falsifier="when domain width differs"), "falsifier", "ok"),
    (issue(62, falsifier="counter-example shows law breaks"), "falsifier", "ok"),
    (issue(63, falsifier="explicit counter-test"), "falsifier", "legend"),
    (issue(64, falsifier="will be added once the D5 map lands"), "falsifier", "aspirational"),
    (issue(65, falsifier="Positive controls:"), "falsifier", "vague"),
    (issue(66, falsifier=""), "falsifier", "empty"),
    ({"number": 67, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "LAW: x\n"}, "falsifier", "missing"),
    # STATUS (#2575)
    (issue(70, status="hypothesis"), "status", "ok"),
    (issue(71, status="ratified"), "status", "ok"),
    (issue(72, status="unknown"), "status", "ok"),
    (issue(73, status="hypothesis | generated | ratified | falsified | unknown"), "status", "legend"),
    (issue(74, status="READY-FOR-OWNER"), "status", "foreign"),
    (issue(75, status="implementation-target"), "status", "foreign"),
    (issue(76, status=""), "status", "empty"),
    ({"number": 77, "title": "t", "state": "open",
      "body": BLOCK_TEXT + "LAW: x\n"}, "status", "missing"),
]


def selftest_shared_proved_law():
    body = (BLOCK_TEXT + "RELATION: shared-proved-law\n"
            "WITNESS: tests/fixtures/exact-q-commutes.lisp\nLAW: x\n")
    return {"number": 29, "title": "t", "state": "open", "body": body}


def self_test():
    cases = list(SELFTEST) + [(selftest_shared_proved_law(), "relation", "ok")]
    failures = 0
    judged, _skipped = judge([c[0] for c in cases])
    got = {(j[0], j[1]): j[3] for j in judged}
    for it, field, expected in cases:
        ok = got.get((field, it["number"])) == expected
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] {field:10} #{it['number']}: "
              f"{got.get((field, it['number']))} (expected {expected})")
    # a closed body and an un-stamped, field-less body are ignored
    ignored, skipped = judge([
        {"number": 90, "title": "t", "state": "closed", "body": BLOCK_TEXT + "DOMAIN: W8\n"},
        {"number": 91, "title": "t", "state": "open", "body": "just prose\n"},
    ])
    ok = skipped == 2 and not ignored
    failures += 0 if ok else 1
    print(f"  [{'ok' if ok else 'FAIL'}] closed and field-less bodies are ignored ({skipped})")
    if failures:
        print(f"binary-domain-selftest-failed ({failures})")
        return 1
    print(f"(binary-domain-selftest-ok ({len(cases)} cases, 5 fields, 2 ignored))")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", help="JSON snapshot: a list, or {\"issues\": [...]}")
    ap.add_argument("--baseline", help="JSON of pre-existing violations; fail only on new ones")
    ap.add_argument("--emit-baseline", action="store_true",
                    help="print the baseline JSON for the current snapshot")
    ap.add_argument("--fields", default="domain,relation,witness,falsifier,status",
                    help="comma-separated subset of: domain,relation,witness,falsifier,status")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.issues:
        ap.error("--issues is required (or use --self-test)")
    fields = tuple(f.strip() for f in args.fields.split(",") if f.strip())
    return run(args.issues, args.baseline, args.emit_baseline, fields)


if __name__ == "__main__":
    sys.exit(main())
