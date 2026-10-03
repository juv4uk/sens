#!/usr/bin/env python3
"""Check that the binary-domain format fields say something.

Slice 1 — DOMAIN (#2513): width/carrier or honest UNKNOWN.
Slice 2 — RELATION (#2514): exact enum token.

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
    b = body or ""
    pats = (
        (
            "value",
            re.compile(
                rf"^[ \t]*#{{1,6}}[ \t]*\**{label}\**(?:[ \t]*:[ \t]*(.*)|[ \t]*)$",
                re.I | re.M,
            ),
            True,
        ),
        (
            "value",
            re.compile(
                rf"^[ \t]*(?:[-*][ \t]*)?\**{label}\**[ \t]*:[ \t]*(.*)$",
                re.I | re.M,
            ),
            False,
        ),
        (
            "twocol",
            re.compile(
                rf"^[ \t]*\**{label}\**[ \t]{{2,}}(\S.*)$", re.I | re.M
            ),
            False,
        ),
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


LEGEND_TEXT = {
    "DOMAIN": re.compile(r"^exact width/type/carrier\b", re.I),
    "RELATION": re.compile(
        r"^(?:Core-only\s*\|\s*Core-Math-only\s*\|\s*bridge-candidate\s*\|\s*"
        r"shared-proved-law)\b",
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


def judge(issues):
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
        d_kind, d_val = field_value(body, "DOMAIN")
        r_kind, r_val = field_value(body, "RELATION")
        judged.append(
            {
                "number": it.get("number"),
                "title": it.get("title", ""),
                "domain": domain_verdict(d_val if d_kind else None),
                "domain_value": d_val,
                "relation": relation_verdict(r_val if r_kind else None, body),
                "relation_value": r_val,
            }
        )
    return judged, skipped


VIOLATION_DOMAIN = {"circular", "empty", "vague", "missing", "legend"}
VIOLATION_RELATION = {
    "prose",
    "empty",
    "missing",
    "legend",
    "unproved-shared-law",
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issues", type=str, help="JSON snapshot of issues")
    ap.add_argument("--baseline", type=str, help="baseline violations JSON")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        cases = [
            ("ok", "## DOMAIN\nD5", "ok"),
            ("ok-unknown", "DOMAIN: UNKNOWN", "ok"),
            ("circular", "DOMAIN: Exact Core-Math domain selected by the admitted law.", "circular"),
            ("vague", "DOMAIN: One explicit Core-Math binary domain at a time.", "vague"),
            ("empty", "## DOMAIN\n\n## LAW\nx", "empty"),
            ("legend", "DOMAIN        exact width/type/carrier", "legend"),
            ("rel-ok", "RELATION: Core-only", "ok"),
            ("rel-prose", "RELATION: transport only", "prose"),
        ]
        ok = 0
        for name, body, expected in cases:
            if "RELATION" in body:
                _, v = field_value(body, "RELATION")
                got = relation_verdict(v, body)
            else:
                _, v = field_value(body, "DOMAIN")
                got = domain_verdict(v)
            assert got == expected, (name, got, expected)
            ok += 1
        print(f"(binary-domain-selftest-ok ({ok} cases))")
        return 0

    if not args.issues:
        print("need --issues or --self-test", file=sys.stderr)
        return 2

    data = json.load(open(args.issues, encoding="utf-8"))
    issues = data["issues"] if isinstance(data, dict) else data
    judged, skipped = judge(issues)

    baseline = {"domain": set(), "relation": set()}
    if args.baseline:
        b = json.load(open(args.baseline, encoding="utf-8"))
        v = b.get("violations", b)
        baseline["domain"] = set(v.get("domain", []))
        baseline["relation"] = set(v.get("relation", []))

    new_d, new_r = [], []
    for row in judged:
        n = row["number"]
        if row["domain"] in VIOLATION_DOMAIN and n not in baseline["domain"]:
            new_d.append(row)
        if row["relation"] in VIOLATION_RELATION and n not in baseline["relation"]:
            new_r.append(row)

    print(
        f"(binary-domain-format (judged {len(judged)}) "
        f"(new-domain {len(new_d)}) (new-relation {len(new_r)}) "
        f"(skipped {skipped}))"
    )
    for row in new_d:
        print(f"  domain {row['domain']:12} #{row['number']}  {row['domain_value']!r}")
    for row in new_r:
        print(f"  relation {row['relation']:12} #{row['number']}  {row['relation_value']!r}")

    return 1 if new_d or new_r else 0


if __name__ == "__main__":
    raise SystemExit(main())
