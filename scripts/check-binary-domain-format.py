#!/usr/bin/env python3
"""#2513 — the DOMAIN field must not be circular or empty.

The binary-domain reformat (#2490) requires every task body to say which exact
domain owns the binary number. In practice many *filled* DOMAIN values define
the domain by the domain itself:

    "Exact Core-Math domain selected by the admitted law"
    "One explicit Core-Math binary domain at a time"
    "Core-Math domain in which the admitted law operates"

None of those names a width or a carrier, so the field looks answered and is not.
This checker gives each DOMAIN a named verdict and fails closed on the ones that
say nothing.

Verdicts
--------
ok        names a concrete width/carrier (W8, D5, Function8, exact-Q, 8-bit, ...)
ok        says UNKNOWN, or states an explicit honest uncertainty
circular  defers to the law/domain itself ("selected by the admitted law")
empty     the field is present but blank
vague     neither concrete nor an honest unknown (e.g. a bare placeholder)
missing   the issue carries the reformat block but no DOMAIN field

Scope: only OPEN issues whose body carries the `BINARY-DOMAIN FORMAT` block.
Historical/closed bodies are left alone.

The checker never touches the network. CI supplies a snapshot, so the rule is
provable locally.

Usage
-----
    python3 scripts/check-binary-domain-format.py --issues snapshot.json
    python3 scripts/check-binary-domain-format.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys

BLOCK = re.compile(r"BINARY-DOMAIN\s+FORMAT", re.I)
DOMAIN_FIELD = re.compile(r"^[ \t]*(?:[-*][ \t]*)?\**DOMAIN\**[ \t]*:[ \t]*(.*)$", re.I | re.M)
# The real reformat uses a Markdown heading with the value on the next line:
#     ## DOMAIN
#     Exact Core-Math domain selected by the admitted law.
DOMAIN_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]*\**DOMAIN\**[ \t]*:?[ \t]*(.*)$", re.I | re.M)

# A concrete width or carrier: the thing the field is supposed to name.
CONCRETE = re.compile(
    r"\b(?:W\d+|D\d+|Function\d+|Sound\d+|exact-[A-Za-z0-9]+|\d+-bit|"
    r"śloka|sūtra|pāṇini|fpga|binary source word)\b", re.I)

# An explicit, honest uncertainty — allowed, because it is not disguised.
HONEST_UNKNOWN = re.compile(
    r"\b(?:unknown|not yet determined|not yet fixed|not yet known|"
    r"discovered per family|discovered per domain|no universal width|"
    r"not assumed|to be discovered|unfixed|pending proof)\b", re.I)

# Defining the domain by the law/domain itself.
CIRCULAR = re.compile(
    r"(selected by the (?:admitted )?law|chosen by the (?:admitted )?law|"
    r"in which the (?:admitted )?law operates|the law (?:selects|chooses)|"
    r"domain (?:selected|chosen) by|domain in which the law)", re.I)


def domain_value(body):
    """Return the DOMAIN value, or None when the body declares no DOMAIN at all."""
    body = body or ""
    m = DOMAIN_HEADING.search(body)
    if m:
        rest = m.group(1).strip()
        if rest:
            return rest
        for line in body[m.end():].splitlines():
            s = line.strip()
            if not s:
                continue
            # the next line being another heading/field means DOMAIN is blank
            if s.startswith("#") or re.match(r"^[A-Z][A-Z _/-]{2,}\s*:", s):
                return ""
            return s
        return ""
    m = DOMAIN_FIELD.search(body)
    return m.group(1).strip() if m else None


def domain_verdict(value):
    if value is None:
        return "missing"
    if not value:
        return "empty"
    if CONCRETE.search(value):
        return "ok"
    if CIRCULAR.search(value):
        return "circular"
    if HONEST_UNKNOWN.search(value):
        return "ok"
    return "vague"


def judge(issues):
    """Return (judged, skipped) where judged is [(number, title, verdict, value)].

    Scope: an OPEN body is judged when it declares a DOMAIN field at all, or when
    it carries the reformat block (so a block with no DOMAIN field is a finding).
    """
    judged, skipped = [], 0
    for it in issues:
        body = it.get("body") or ""
        if str(it.get("state", "open")).lower() != "open":
            skipped += 1
            continue
        value = domain_value(body)
        if value is None and not BLOCK.search(body):
            skipped += 1
            continue
        judged.append((it.get("number"), it.get("title", ""), domain_verdict(value), value))
    return judged, skipped


def run(path, baseline_path=None, emit=False):
    data = json.load(open(path, encoding="utf-8"))
    issues = data["issues"] if isinstance(data, dict) else data
    judged, skipped = judge(issues)
    bad = [j for j in judged if j[2] != "ok"]
    if emit:
        print(json.dumps({"violations": sorted(j[0] for j in bad)}, indent=2))
        return 0
    known = set()
    if baseline_path:
        known = set(json.load(open(baseline_path, encoding="utf-8")).get("violations", []))
    new = [j for j in bad if j[0] not in known]
    print(f"(binary-domain-format (judged {len(judged)}) (ok {len(judged) - len(bad)}) "
          f"(known-violations {len(bad) - len(new)}) (new {len(new)}) (skipped {skipped}))")
    for number, title, verdict, value in bad:
        mark = "NEW " if number not in known else "    "
        print(f"  {mark}{verdict:8} #{number}  {(value or '<blank>')[:80]}")
    if new:
        print("\nbinary-domain-violation: DOMAIN names no exact width/carrier.")
        print("  Name a width/carrier (W8, D5, Function8, exact-Q, ...) or say UNKNOWN,")
        print("  or add the issue to the baseline if it is pre-existing debt.")
        return 1
    print("(binary-domain-ok)")
    return 0


# --- self-test ---------------------------------------------------------------

BLOCK_TEXT = "## BINARY-DOMAIN FORMAT — 2026-10-03\n\nAuthority: #2490.\n"


def issue(number, value, state="open", with_block=True, title="t", form="inline"):
    field = f"## DOMAIN\n{value}\n" if form == "heading" else f"DOMAIN: {value}\n"
    body = (BLOCK_TEXT if with_block else "") + field + "LAW: something\n"
    return {"number": number, "title": title, "body": body, "state": state}


SELFTEST = [
    (issue(1, "W8"), "ok"),
    (issue(2, "exact-Q (rationals, zero excluded)"), "ok"),
    (issue(3, "D7 = Sound7 with local śloka ordinals"), "ok"),
    (issue(4, "UNKNOWN"), "ok"),
    (issue(5, "Core-Math binary domains. Exact widths/carriers are discovered per "
               "family; no universal width is assumed"), "ok"),
    (issue(6, "Exact Core-Math domain selected by the admitted law"), "circular"),
    (issue(7, "Core-Math domain in which the admitted law operates"), "circular"),
    (issue(8, "the law chooses the domain"), "circular"),
    (issue(9, "One explicit Core-Math binary domain at a time"), "vague"),
    (issue(10, "TBD"), "vague"),
    (issue(11, ""), "empty"),
    (issue(12, "", with_block=True, title="no domain line").__class__(
        **{**issue(12, "x"), "body": BLOCK_TEXT + "LAW: x\n"}), "missing"),
    (issue(13, "Exact Core-Math domain selected by the admitted law", state="closed"), None),
    (issue(14, "W8", with_block=False), "ok"),
    ({**issue(19, "x"), "body": "just prose, no fields at all\n"}, None),
    # the real shape: a Markdown heading, value on the next line
    (issue(15, "W8", form="heading"), "ok"),
    (issue(16, "Exact Core-Math domain selected by the admitted law.", form="heading"), "circular"),
    (issue(17, "Core-Math binary domains. Exact widths/carriers are discovered per "
                "family; no universal width is assumed.", form="heading"), "ok"),
    (issue(18, "", form="heading"), "empty"),
]


def self_test():
    failures = 0
    judged, skipped = judge([c[0] for c in SELFTEST])
    got = {number: verdict for number, _t, verdict, _v in judged}
    for it, expected in SELFTEST:
        n = it["number"]
        if expected is None:
            ok = n not in got
            shown = "ignored"
        else:
            ok = got.get(n) == expected
            shown = got.get(n)
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] #{n}: {shown} (expected {expected})")
    ok = skipped == 2
    failures += 0 if ok else 1
    print(f"  [{'ok' if ok else 'FAIL'}] skipped exactly the closed and un-reformatted bodies ({skipped})")
    ok = len(judged) == 17
    failures += 0 if ok else 1
    print(f"  [{'ok' if ok else 'FAIL'}] judged exactly the open reformatted bodies ({len(judged)})")
    if failures:
        print(f"binary-domain-selftest-failed ({failures})")
        return 1
    print("(binary-domain-selftest-ok (17 judged, 6 verdict classes, 2 ignored))")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", help="JSON snapshot: a list, or {\"issues\": [...]}")
    ap.add_argument("--baseline", help="JSON of pre-existing violations; fail only on new ones")
    ap.add_argument("--emit-baseline", action="store_true",
                    help="print the baseline JSON for the current snapshot")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.issues:
        ap.error("--issues is required (or use --self-test)")
    return run(args.issues, args.baseline, args.emit_baseline)


if __name__ == "__main__":
    sys.exit(main())
