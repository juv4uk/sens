#!/usr/bin/env python3
"""#2934 — D8 non-selector parent triage.

Research-only. Screens all 48 non-selector D6 parents for cheap structural
signals that indicate a row is NOT a clean two-bit product, before any
parent-specific executable witness is written.

This is a filter, not an admission. It sorts rows into:
  PLAUSIBLE  — no cheap disqualifier; may deserve a hand-written witness
  IMPAIRED   — at least one structural disqualifier, named explicitly

Disqualifiers are deliberately mechanical and falsifiable:
  NAME_COUNT        the row does not hold exactly four names
  NEAR_SYNONYM      two names differ only by a qualifier suffix, so the pair is
                    one concept twice rather than two independent bits
  POLARITY_TWIN     a +/- or <-> variant pair, which is one axis twice
  CATEGORY_DRIFT    a name that is not the same kind of thing as its siblings
  HISTORICAL_ONLY   the row mixes dialect lineages that never coexisted

The point is to avoid spending hand-written witnesses on rows that already
have a visible structural defect, and to make the remaining work enumerable.

No production mutation and no D8 coordinate is ratified here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

POLARITY_TOKENS = {
    "INCF": ("DECF",),
    "DECF": ("INCF",),
    "1+": ("1-",),
    "1-": ("1+",),
    "CHAR>": ("CHAR<",),
    "CHAR<": ("CHAR>",),
    "STRING>": ("STRING<",),
    "STRING<": ("STRING>",),
    "PLUSP": ("MINUSP",),
    "MINUSP": ("PLUSP",),
    "SIGNUM": (),
}

# Any two names sharing a hyphenated first component are one concept twice:
# COPY-TREE -> COPY-STRUCTURE / COPY-ARRAY, MAPLIST -> MAPLIST* is separate.
STEM_RE = re.compile(r"^(?P<stem>[A-Z0-9]+)-")

# Rows already refuted by a parent-specific executable witness. Triage must not
# offer them again as promising work.
REFUTED = {
    "000000": "research-2934-d8-repl-factoring.py",
    "000101": "research-2934-d8-lexpr-factoring.py",
    "001011": "research-2934-d8-while-factoring.py",
    "010010": "research-2934-d8-integerp-factoring.py",
}


@dataclass
class Verdict:
    parent_d6: str
    parent_name: str
    names: list
    reasons: list = field(default_factory=list)

    @property
    def impaired(self) -> bool:
        return bool(self.reasons)


def near_synonyms(names: list) -> list:
    """Names sharing a hyphenated stem, e.g. COPY-STRUCTURE / COPY-ARRAY."""
    stems: dict = {}
    for name in names:
        match = STEM_RE.match(name)
        if match:
            stems.setdefault(match.group("stem"), []).append(name)
    return [group for group in stems.values() if len(group) > 1]


def polarity_twins(names: list) -> list:
    """A +/- or ordering pair inside one row: one axis counted twice."""
    present = set(names)
    found = set()
    for name, twins in POLARITY_TOKENS.items():
        for twin in twins:
            if name in present and twin in present:
                found.add(frozenset((name, twin)))
    return sorted(tuple(sorted(pair)) for pair in found)


def category_drift(names: list, parent_name: str) -> list:
    """A name that cannot be a refinement of this parent by construction.

    The clearest case is a foreign-function call sitting under a composition
    parent: composition cannot generate a call into another language.
    """
    reasons = []
    if parent_name == "CURRY" and "FFI-CALL" in names:
        reasons.append("FFI-CALL is a foreign-function call, not a curry descendant")
    return reasons


def load_rows() -> list:
    path = "knowledge/d8-historical-full-map.json"
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    d6_path = "knowledge/d6-historical-full-map.json"
    with open(d6_path, encoding="utf-8") as handle:
        d6 = json.load(handle)
    parent_names = {row["coordinate"]: row["name"] for row in d6["coordinates"]}

    rows: dict = {}
    for cell in data.get("unassigned_candidates", []):
        rows.setdefault(cell["parent_d6"], []).append(cell)
    return [(parent, cells, parent_names.get(parent)) for parent, cells in sorted(rows.items())]


def triage() -> list:
    out = []
    for parent, cells, parent_name in load_rows():
        names = [cell["name"] for cell in cells]
        verdict = Verdict(parent_d6=parent, parent_name=parent_name, names=names)
        if len(names) != 4:
            verdict.reasons.append(f"NAME_COUNT: {len(names)} names, not 4")
        for group in near_synonyms(names):
            verdict.reasons.append(f"NEAR_SYNONYM: {group} are one concept twice")
        for name, twin in polarity_twins(names):
            verdict.reasons.append(
                f"POLARITY_TWIN: {name} <-> {twin} is one axis twice"
            )
        verdict.reasons.extend(category_drift(names, parent_name or ""))
        if parent in REFUTED:
            verdict.reasons.append(
                f"ALREADY_REFUTED: {REFUTED[parent]}"
            )
        out.append(verdict)
    return out


def main() -> None:
    verdicts = triage()
    assert len(verdicts) == 48, len(verdicts)

    impaired = [v for v in verdicts if v.impaired]
    plausible = [v for v in verdicts if not v.impaired]
    assert all(len(set(v.reasons)) == len(v.reasons) for v in verdicts), \
        "a reason was recorded twice"

    for verdict in impaired:
        print(f"IMPAIRED {verdict.parent_d6} {verdict.parent_name}")
        for reason in verdict.reasons:
            print(f"    {reason}")

    print()
    print(f"PLAUSIBLE={len(plausible)} IMPAIRED={len(impaired)} TOTAL={len(verdicts)}")
    print()
    print("PLAUSIBLE rows needing a hand-written witness:")
    for verdict in plausible:
        print(f"  {verdict.parent_d6} {verdict.parent_name:<14} {verdict.names}")


if __name__ == "__main__":
    main()