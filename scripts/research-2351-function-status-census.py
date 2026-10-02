#!/usr/bin/env python3
"""#2351 conservative function-status census.

Reads the live semantic registry and assigns exactly one epistemic status:
  root | generated | residue | UNKNOWN

This first slice is intentionally conservative:
- only current selector descendants with merged executable certificate evidence
  are promoted to generated;
- local grammar roots are NOT automatically global semantic roots;
- draft/bounded synthesis evidence may annotate UNKNOWN rows but cannot promote
  them before its evidence gate is admitted.

Research only. No production allocation or deletion.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
OUT_TSV = ROOT / "docs" / "research" / "2351-function-status-census.tsv"
OUT_JSON = ROOT / "docs" / "research" / "2351-function-status-census.json"

ROW_RE = re.compile(r"^\s*\(([01]{8})\s+(.*)\)\s*$")
EN_RE = re.compile(r"\(en\s+([^\s()]+|\(\))\)")

STATUSES = {"root", "generated", "residue", "UNKNOWN"}

# Current fixed-8 identities remain the authority keys in this census.
# These mappings are semantic evidence, not a proposal to preserve fixed-8
# identity as the future ontology.
CONFIRMED_GENERATED = {
    "00110011": {
        "law_path": "CAR>CAR",
        "root_basis": "00000101,00000110",
        "certificate_ref": "#2345 merged; #2329 merged",
        "search_grammar": "selector-composition",
        "search_bound": "merged-executable-certificate",
        "semantic_fact_refs": "#1962,#2054,#2329,#2345",
    },
    "00110100": {
        "law_path": "CDR>CAR",
        "root_basis": "00000101,00000110",
        "certificate_ref": "#2345 merged; #2329 merged",
        "search_grammar": "selector-composition",
        "search_bound": "merged-executable-certificate",
        "semantic_fact_refs": "#1962,#2054,#2329,#2345",
    },
    "00110101": {
        "law_path": "CDR>CDR",
        "root_basis": "00000101,00000110",
        "certificate_ref": "#2345 merged; #2329 merged",
        "search_grammar": "selector-composition",
        "search_bound": "merged-executable-certificate",
        "semantic_fact_refs": "#1962,#2054,#2329,#2345",
    },
    "00110110": {
        "law_path": "CDR>CDR>CDR>CAR",
        "root_basis": "00000101,00000110",
        "certificate_ref": "#2345 merged; #2329 merged",
        "search_grammar": "selector-composition",
        "search_bound": "merged-executable-certificate",
        "semantic_fact_refs": "#1962,#2054,#2329,#2345",
    },
}

# Evidence exists, but the PR is still draft/open. These remain UNKNOWN.
DRAFT_CANDIDATES = {
    "00011011": {
        "law_path": "SWAP>LT",
        "certificate_ref": "#2335 draft",
        "search_grammar": "typed-composition-BFS",
        "search_bound": "depth<=3,bounded-Q-corpus",
        "semantic_fact_refs": "#2254,#2321,#2335",
        "note": "candidate GT derivation; evidence gate not merged",
    },
    "00011101": {
        "law_path": "SWAP>LT>NOT",
        "certificate_ref": "#2335 draft",
        "search_grammar": "typed-composition-BFS",
        "search_bound": "depth<=3,bounded-Q-corpus",
        "semantic_fact_refs": "#2254,#2321,#2335",
        "note": "candidate LE derivation; evidence gate not merged",
    },
    "00011110": {
        "law_path": "LT>NOT",
        "certificate_ref": "#2335 draft",
        "search_grammar": "typed-composition-BFS",
        "search_bound": "depth<=3,bounded-Q-corpus",
        "semantic_fact_refs": "#2254,#2321,#2335",
        "note": "candidate GE derivation; evidence gate not merged",
    },
    "00011100": {
        "law_path": "",
        "certificate_ref": "#2335 draft",
        "search_grammar": "typed-composition-BFS",
        "search_bound": "depth<=4,bounded-Q-corpus",
        "semantic_fact_refs": "#2321,#2335",
        "note": "EQ unresolved in bounded pure-composition search; not independence",
    },
}

LOCAL_BASIS_ROLES = {
    "00000101": "selector-root-candidate",
    "00000110": "selector-root-candidate",
}


def parse_registry() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        identity, rest = match.groups()
        en_match = EN_RE.search(rest)
        en_surface = ""
        if en_match and en_match.group(1) != "()":
            en_surface = en_match.group(1)
        any_surface = not (
            "(en ())" in rest
            and "(ук ())" in rest
            and "(укр ())" in rest
            and "(sa ())" in rest
            and "(sym ())" in rest
        )
        rows.append(
            {
                "function_identity": identity,
                "width": len(identity),
                "human_surface_optional": en_surface,
                "surface_exposed": bool(any_surface),
            }
        )

    assert len(rows) == 256, len(rows)
    assert len({r["function_identity"] for r in rows}) == 256
    return rows


def classify(base: dict[str, object]) -> dict[str, object]:
    identity = str(base["function_identity"])
    row = dict(base)
    row.update(
        {
            "status": "UNKNOWN",
            "basis_role": LOCAL_BASIS_ROLES.get(identity, ""),
            "root_basis": "",
            "law_path": "",
            "certificate_ref": "",
            "search_grammar": "not-run",
            "search_bound": "none",
            "counterexample": "",
            "independence_status": "unknown",
            "semantic_fact_refs": "",
            "note": "",
        }
    )

    if identity in CONFIRMED_GENERATED:
        evidence = CONFIRMED_GENERATED[identity]
        row.update(evidence)
        row["status"] = "generated"
        row["independence_status"] = "derived"
        row["note"] = "current identity retained; behavior reconstructible from merged selector law"
    elif identity in DRAFT_CANDIDATES:
        row.update(DRAFT_CANDIDATES[identity])
        row["status"] = "UNKNOWN"
        row["independence_status"] = "bounded-candidate-not-admitted"

    assert row["status"] in STATUSES
    return row


def census() -> dict[str, object]:
    rows = [classify(r) for r in parse_registry()]
    counts = {status: sum(r["status"] == status for r in rows) for status in STATUSES}
    surface_exposed = sum(bool(r["surface_exposed"]) for r in rows)

    summary = {
        "admitted_total": len(rows),
        "surface_exposed": surface_exposed,
        "surface_empty": len(rows) - surface_exposed,
        "roots": counts["root"],
        "generated": counts["generated"],
        "bounded_residue": counts["residue"],
        "unknown": counts["UNKNOWN"],
        "generated_fraction": counts["generated"] / len(rows),
        "independent_fact_upper_bound": len(rows) - counts["generated"],
        "registry_rows_potentially_derivable": counts["generated"],
        "epistemic_rule": "failed-search-is-not-independence",
        "authority": "research-only",
    }

    # This first slice is deliberately conservative.
    assert summary["admitted_total"] == 256
    assert summary["surface_exposed"] == 182
    assert summary["surface_empty"] == 74
    assert summary["roots"] == 0
    assert summary["generated"] == 4
    assert summary["bounded_residue"] == 0
    assert summary["unknown"] == 252

    return {"summary": summary, "rows": rows}


FIELDS = [
    "function_identity",
    "width",
    "status",
    "basis_role",
    "root_basis",
    "law_path",
    "certificate_ref",
    "search_grammar",
    "search_bound",
    "counterexample",
    "independence_status",
    "semantic_fact_refs",
    "surface_exposed",
    "human_surface_optional",
    "note",
]


def render_json(data: dict[str, object]) -> str:
    # Preserve deterministic construction order used by the committed artifact.
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def render_tsv(data: dict[str, object]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in data["rows"]:
        rendered = {}
        for field in FIELDS:
            value = row.get(field, "")
            if isinstance(value, bool):
                value = "true" if value else "false"
            rendered[field] = value
        writer.writerow(rendered)
    return out.getvalue()


def write_outputs(data: dict[str, object]) -> None:
    OUT_JSON.write_text(render_json(data), encoding="utf-8")
    OUT_TSV.write_text(render_tsv(data), encoding="utf-8")


def check_outputs(data: dict[str, object]) -> None:
    expected = {
        OUT_JSON: render_json(data),
        OUT_TSV: render_tsv(data),
    }
    stale = []
    for path, content in expected.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(str(path.relative_to(ROOT)))
    if stale:
        raise SystemExit("STALE-CENSUS=" + ",".join(stale))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    data = census()
    if args.write:
        write_outputs(data)
    if args.check:
        check_outputs(data)

    summary = data["summary"]
    for key, value in summary.items():
        print(f"{key.upper().replace('-', '_')}={value}")
    print("STATUS=PASS-CONSERVATIVE-FUNCTION-STATUS-CENSUS")


if __name__ == "__main__":
    main()
