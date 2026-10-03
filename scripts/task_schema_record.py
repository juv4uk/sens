#!/usr/bin/env python3
"""Shared parser for governed binary-domain task records.

This module owns structure only. Field-specific semantic judges must consume
this parser instead of scanning issue Markdown independently.

Canonical marker:
  ## BINARY-DOMAIN RECORD
or:
  ## BINARY-DOMAIN FORMAT

Structural law for the seven semantic fields:
  count(field) == 1

UNKNOWN is a value, not absence. Semantic quality is judged elsewhere.\nMarked-record scope is deliberate: unmarked legacy/examples are not governed records.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

FIELD_LABELS = (
    "DOMAIN",
    "BINARY OBJECT",
    "LAW",
    "WITNESS",
    "FALSIFIER",
    "STATUS",
    "RELATION",
)

_MARKER = re.compile(
    r"^(?P<hashes>#{1,6})[ \t]*"
    r"(?:BINARY[- ]DOMAIN[ \t]+(?:RECORD|FORMAT))"
    r"[ \t]*.*$",
    re.I | re.M,
)


@dataclass(frozen=True)
class Occurrence:
    label: str
    value: str
    line: int
    shape: str


@dataclass(frozen=True)
class ParsedRecord:
    marked: bool
    region: str
    occurrences: dict[str, tuple[Occurrence, ...]]

    def count(self, label: str) -> int:
        return len(self.occurrences.get(label, ()))

    def values(self, label: str) -> tuple[str, ...]:
        return tuple(x.value for x in self.occurrences.get(label, ()))


def _record_region(body: str) -> tuple[bool, str]:
    body = body or ""
    m = _MARKER.search(body)
    if not m:
        return False, body

    level = len(m.group("hashes"))
    tail = body[m.end():]
    ws = re.match(r"\s*", tail)
    pos = ws.end() if ws else 0

    if tail[pos:pos + 3] == "```":
        first_nl = tail.find("\n", pos)
        if first_nl < 0:
            return True, ""
        close = tail.find("```", first_nl + 1)
        if close < 0:
            return True, tail[first_nl + 1:]
        return True, tail[first_nl + 1:close]

    stop_rx = re.compile(rf"^#{{1,{level}}}[ \t]+\S", re.M)
    stop = stop_rx.search(tail)
    return True, tail[: stop.start() if stop else len(tail)]


def _matches_field_line(line: str, label: str) -> bool:
    esc = re.escape(label)
    return bool(
        re.match(rf"^\**{esc}\**\s*:", line, re.I)
        or re.match(rf"^\**{esc}\**\s{{2,}}\S", line, re.I)
        or re.match(rf"^#{{1,6}}\s*\**{esc}\**(?:\s*:.*|\s*)$", line, re.I)
    )


def _next_heading_value(lines: list[str], index: int) -> str:
    for line in lines[index + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue
        if stripped.startswith("#"):
            return ""
        if any(_matches_field_line(stripped, label) for label in FIELD_LABELS):
            return ""
        return stripped
    return ""


def _parse_occurrences(region: str) -> dict[str, tuple[Occurrence, ...]]:
    lines = region.splitlines()
    found: dict[str, list[Occurrence]] = {label: [] for label in FIELD_LABELS}

    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("```"):
            continue

        for label in FIELD_LABELS:
            esc = re.escape(label)

            heading = re.match(
                rf"^#{{1,6}}\s*\**{esc}\**\s*:?[ \t]*(.*)$",
                line,
                re.I,
            )
            if heading:
                rest = heading.group(1).strip()
                value = rest or _next_heading_value(lines, i)
                found[label].append(Occurrence(label, value, i + 1, "heading"))
                break

            inline = re.match(
                rf"^(?:[-*]\s*)?\**{esc}\**\s*:\s*(.*)$",
                line,
                re.I,
            )
            if inline:
                found[label].append(
                    Occurrence(label, inline.group(1).strip(), i + 1, "inline")
                )
                break

            twocol = re.match(
                rf"^\**{esc}\**\s{{2,}}(\S.*)$",
                line,
                re.I,
            )
            if twocol:
                found[label].append(
                    Occurrence(label, twocol.group(1).strip(), i + 1, "twocol")
                )
                break

    return {label: tuple(rows) for label, rows in found.items() if rows}


def parse_record(body: str) -> ParsedRecord:
    marked, region = _record_region(body or "")
    return ParsedRecord(marked, region, _parse_occurrences(region))


def field_occurrences(body: str, label: str) -> tuple[Occurrence, ...]:
    return parse_record(body).occurrences.get(label, ())


def first_field_value(body: str, label: str) -> tuple[str | None, str | None]:
    rows = field_occurrences(body, label)
    if not rows:
        return None, None
    row = rows[0]
    kind = "twocol" if row.shape == "twocol" else "value"
    return kind, row.value


def structural_verdict(record: ParsedRecord, label: str) -> str:
    rows = record.occurrences.get(label, ())
    if len(rows) == 0:
        return "MISSING-FIELD"
    if len(rows) > 1:
        return "DUPLICATE-FIELD"
    if not rows[0].value.strip():
        return "EMPTY-FIELD"
    return "OK"


def structural_rows(body: str) -> list[dict[str, object]]:
    record = parse_record(body)
    if not record.marked:
        return []
    rows = []
    for label in FIELD_LABELS:
        occ = record.occurrences.get(label, ())
        rows.append(
            {
                "field": label,
                "verdict": structural_verdict(record, label),
                "count": len(occ),
                "values": [x.value for x in occ],
                "lines": [x.line for x in occ],
            }
        )
    return rows


def self_test() -> int:
    good = """## BINARY-DOMAIN RECORD

```text
RELATION: Core-only
STATUS: hypothesis
FALSIFIER: remove edge -> law fails
WITNESS: PR #1
LAW: x -> y
BINARY OBJECT: 0011
DOMAIN: Core.D4 [carrier=W4]
```
"""
    rows = structural_rows(good)
    assert len(rows) == 7
    assert all(x["verdict"] == "OK" for x in rows)

    missing = good.replace("LAW: x -> y\n", "")
    verdicts = {x["field"]: x["verdict"] for x in structural_rows(missing)}
    assert verdicts["LAW"] == "MISSING-FIELD"

    duplicate = good.replace(
        "DOMAIN: Core.D4 [carrier=W4]\n",
        "DOMAIN: Core.D4 [carrier=W4]\nDOMAIN: Other\n",
    )
    verdicts = {x["field"]: x["verdict"] for x in structural_rows(duplicate)}
    assert verdicts["DOMAIN"] == "DUPLICATE-FIELD"

    empty = good.replace("STATUS: hypothesis", "STATUS:")
    verdicts = {x["field"]: x["verdict"] for x in structural_rows(empty)}
    assert verdicts["STATUS"] == "EMPTY-FIELD"

    unknown = good.replace(
        "DOMAIN: Core.D4 [carrier=W4]",
        "DOMAIN: UNKNOWN",
    )
    verdicts = {x["field"]: x["verdict"] for x in structural_rows(unknown)}
    assert verdicts["DOMAIN"] == "OK"

    reordered = """## BINARY-DOMAIN FORMAT
DOMAIN: Core.D4 [carrier=W4]
WITNESS: PR #1
RELATION: Core-only
BINARY OBJECT: 0011
FALSIFIER: remove edge -> law fails
STATUS: hypothesis
LAW: x -> y

## Notes
DOMAIN: example-outside-record
"""
    verdicts = {x["field"]: x["verdict"] for x in structural_rows(reordered)}
    assert all(v == "OK" for v in verdicts.values())

    legacy = "DOMAIN: D5\nRELATION: Core-only\n"
    assert parse_record(legacy).marked is False
    assert structural_rows(legacy) == []
    assert first_field_value(legacy, "DOMAIN") == ("value", "D5")

    print("TASK-SCHEMA-PARSER=PASS")
    print("FIELDS=7")
    print("MISSING-FIELD=PASS")
    print("DUPLICATE-FIELD=PASS")
    print("EMPTY-FIELD=PASS")
    print("UNKNOWN-IS-VALUE=PASS")
    print("REORDER-INVARIANCE=PASS")
    print("OUTSIDE-RECORD-EXAMPLE-IGNORED=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
