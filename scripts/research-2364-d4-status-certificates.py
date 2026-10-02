#!/usr/bin/env python3
"""#2364 — D4 status-certificate bridge.

Translate the owner-ratified #2156 D4 classification into machine-readable
census evidence without deriving status from addresses or names.

Research only:
- 8 residents are generation candidates backed by Lisp-owned source + replay.
- LAMBDA/DEFINE are root candidates only in the bounded Core1 bootstrap scope.
- no production allocation/deletion follows from this file.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge" / "exact-width-admitted-corpus.json"
CORE1 = ROOT / "lib" / "core1.lisp"
PRELUDE = ROOT / "lib" / "core1-compiler-prelude.lisp"
CORE = ROOT / "lib" / "core.lisp"
CONTRACT = ROOT / "contracts" / "core1-bootstrap-contract.lisp"
CORE1_WORKFLOW = ROOT / ".github" / "workflows" / "core1-s0.yml"
CONFORMANCE = ROOT / "tests" / "fixtures" / "conformance.lisp"
MCCARTHY_TEST = ROOT / "crates" / "sens" / "tests" / "mccarthy.rs"

D4 = {
    "0000": "APPLY",
    "0001": "EVAL",
    "0010": "LAMBDA",
    "0011": "DEFINE",
    "0100": "NOT",
    "0110": "EVCON",
    "0111": "EVLIS",
    "1000": "LIST",
    "1110": "LOOKUP",
    "1111": "BIND",
}

GENERATED = {
    "APPLY": {
        "source": (CORE1, "(00001001 C1-APPLY\n"),
        "dependencies": ["COND", "LAMBDA", "DEFINE"],
        "certificate_kind": "core1-lisp-body+s0-replay",
    },
    "EVAL": {
        "source": (CORE1, "(00001001 C1-EVAL\n"),
        "dependencies": [
            "QUOTE", "ATOM", "EQ", "COND", "CAR", "CDR", "CONS",
            "LAMBDA", "DEFINE", "LOOKUP", "BIND", "EVLIS", "EVCON", "APPLY",
        ],
        "certificate_kind": "core1-lisp-body+s0-replay",
    },
    "NOT": {
        "source": (PRELUDE, "(00001011 not\n"),
        "dependencies": ["QUOTE", "COND", "LAMBDA", "DEFINE"],
        "certificate_kind": "pure-lisp-prelude+s0-replay",
    },
    "EVCON": {
        "source": (CORE1, "(00001001 C1-EVCON\n"),
        "dependencies": ["EQ", "COND", "CAR", "CDR", "EVAL", "DEFINE"],
        "certificate_kind": "core1-lisp-body+s0-replay",
    },
    "EVLIS": {
        "source": (CORE1, "(00001001 C1-EVLIS\n"),
        "dependencies": ["EQ", "COND", "CONS", "CAR", "CDR", "EVAL", "DEFINE"],
        "certificate_kind": "core1-lisp-body+s0-replay",
    },
    "LIST": {
        "source": (CORE, "(00001001 list "),
        "dependencies": ["LAMBDA", "DEFINE"],
        "certificate_kind": "pure-lisp-variadic-lambda+constitutive-runtime",
    },
    "LOOKUP": {
        "source": (CORE1, "(00001001 C1-LOOKUP\n"),
        "dependencies": ["EQ", "COND", "CAR", "CDR", "DEFINE"],
        "certificate_kind": "core1-lisp-body+s0-replay",
    },
    "BIND": {
        "source": (CORE1, "(00001001 C1-BIND\n"),
        "dependencies": ["EQ", "COND", "CONS", "CAR", "CDR", "DEFINE"],
        "certificate_kind": "core1-lisp-body+s0-replay",
    },
}

ROOT_CANDIDATES = {
    "LAMBDA": {
        "semantic_claim": "construct first-class lexical closure/application behavior",
        "remove_one_ref": ".github/workflows/d4-status-certificates.yml#remove-LAMBDA",
        "proof_scope": "bounded-current-Core1-bootstrap; not a global algebraic independence theorem",
    },
    "DEFINE": {
        "semantic_claim": "extend top-level global binding frame and enable recursive named definitions",
        "remove_one_ref": ".github/workflows/d4-status-certificates.yml#remove-DEFINE",
        "proof_scope": "bounded-current-Core1-bootstrap; not a global algebraic independence theorem",
    },
}

FORBIDDEN_HOST_MARKERS = (
    "process-run",
    "tcp-read",
    "tcp-write",
    "read-file",
    "write-file",
    "json-parse",
    "sha256-hex",
    "rust::",
    "extern ",
)

FIELDS = [
    "identity",
    "status_candidate",
    "semantic_claim",
    "dependencies",
    "certificate_kind",
    "certificate_ref",
    "remove_one_ref",
    "host_smuggling_check",
    "proof_bytes",
    "verify_i_refs",
    "fact_ledger_refs",
    "proof_scope",
]


def strip_comments(source: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in source.splitlines())


def extract_form(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing marker: {marker}")

    depth = 0
    in_string = False
    escaped = False
    seen = False
    for i in range(start, len(source)):
        ch = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "(":
            depth += 1
            seen = True
        elif ch == ")":
            depth -= 1
            if seen and depth == 0:
                return source[start : i + 1]
    raise AssertionError(f"unterminated form: {marker}")


def load_exact_width_d4() -> dict[str, dict[str, Any]]:
    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert data["meta"]["schema"] == "exact-width-admitted-corpus/v1"
    assert data["meta"]["authority"] == "projection-only"

    rows = {
        row["word"]: row
        for row in data["rows"]
        if row["width"] == 4 and row["status"] != "unallocated"
    }

    for identity, label in sorted(D4.items()):
        assert identity in rows, identity
        assert rows[identity]["human_label_optional"] == label
        assert rows[identity]["status"] == "admitted"
    return rows


def static_authority_checks() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    workflow = CORE1_WORKFLOW.read_text(encoding="utf-8")
    conformance = CONFORMANCE.read_text(encoding="utf-8")
    mccarthy = MCCARTHY_TEST.read_text(encoding="utf-8")

    assert "(derived-not-seed-primitives . (LIST NOT))" in contract
    for mechanism in (
        "lookup",
        "lexical-binding",
        "argument-evaluation",
        "application",
        "program-evaluation",
    ):
        assert mechanism in contract

    assert "Execute exact Core1 S1 source on S0" in workflow
    assert "Execute Core1 S3 compiler prelude through S0/Core1" in workflow
    assert "test \"$actual\" = '(T NIL)'" in workflow

    assert '((lambda args args) 1 2 3)' in conformance
    assert '(list 1 2 3)' in conformance
    assert "bare_symbol_lambda_list_binds_every_argument_as_one_list" in mccarthy
    assert "list_is_a_sens_function_in_core_my_not_a_rust_builtin" in mccarthy


def generated_row(identity: str, label: str) -> dict[str, Any]:
    spec = GENERATED[label]
    path, marker = spec["source"]
    source = strip_comments(path.read_text(encoding="utf-8"))
    form = extract_form(source, marker)

    lowered = form.lower()
    for forbidden in FORBIDDEN_HOST_MARKERS:
        assert forbidden not in lowered, (label, forbidden)

    if label == "LIST":
        compact = re.sub(r"\s+", " ", form).strip()
        assert "(00001000 args args)" in compact
    elif label == "NOT":
        assert "00000111" in form  # COND
        assert "00000001" in form  # QUOTE
        assert "00001000" in form  # LAMBDA
    else:
        assert "C1-" in form

    return {
        "identity": identity,
        "status_candidate": "generated",
        "semantic_claim": f"{label} behavior is reconstructed by admitted Lisp-owned program",
        "dependencies": spec["dependencies"],
        "certificate_kind": spec["certificate_kind"],
        "certificate_ref": ".github/workflows/d4-status-certificates.yml + tests/fixtures/d4-status-certificate-s0.lisp",
        "remove_one_ref": None,
        "host_smuggling_check": "PASS:no-host-capability-marker-in-proof-body; Lisp-owned execution evidence required",
        "proof_bytes": len(form.encode("utf-8")),
        "verify_i_refs": [
            "scripts/research-2364-d4-status-certificates.py",
            ".github/workflows/d4-status-certificates.yml",
        ],
        "fact_ledger_refs": ["#2156", "#2304", "#2351", "#2364"],
        "proof_scope": "current D4/Core1 bridge; residency does not imply primitiveness",
    }


def root_row(identity: str, label: str) -> dict[str, Any]:
    spec = ROOT_CANDIDATES[label]
    core1 = strip_comments(CORE1.read_text(encoding="utf-8"))

    eval_form = extract_form(core1, "(00001001 C1-EVAL\n")
    if label == "LAMBDA":
        assert "C1-LAMBDA-NAMEP" in eval_form
        assert "FUNCTION" in eval_form
        proof = extract_form(core1, "(00001001 C1-LAMBDA-NAMEP\n") + eval_form
    else:
        eval_program = extract_form(core1, "(00001001 C1-EVAL-PROGRAM\n")
        definitionp = extract_form(core1, "(00001001 C1-DEFINITIONP\n")
        assert "C1-DEFINITIONP" in eval_program
        assert "GLOBAL" in eval_program
        assert "C1-DEFINE-NAMEP" in definitionp
        proof = definitionp + eval_program

    return {
        "identity": identity,
        "status_candidate": "root",
        "semantic_claim": spec["semantic_claim"],
        "dependencies": ["D1-D3"],
        "certificate_kind": "bounded-remove-one-necessity",
        "certificate_ref": ".github/workflows/d4-status-certificates.yml",
        "remove_one_ref": spec["remove_one_ref"],
        "host_smuggling_check": "PASS:necessity attacked inside Lisp-owned Core1 evaluator; S0 is explicit mechanism provenance",
        "proof_bytes": len(proof.encode("utf-8")),
        "verify_i_refs": [
            "tests/fixtures/core1-s0-witness.lisp",
            "tests/fixtures/d4-status-certificate-s0.lisp",
        ],
        "fact_ledger_refs": ["#2156", "#2304", "#2351", "#2364"],
        "proof_scope": spec["proof_scope"],
    }


def build() -> dict[str, Any]:
    load_exact_width_d4()
    static_authority_checks()

    rows = []
    for identity, label in D4.items():
        if label in GENERATED:
            rows.append(generated_row(identity, label))
        elif label in ROOT_CANDIDATES:
            rows.append(root_row(identity, label))
        else:
            raise AssertionError(label)

    generated = sum(r["status_candidate"] == "generated" for r in rows)
    roots = sum(r["status_candidate"] == "root" for r in rows)
    assert generated == 8
    assert roots == 2
    assert len(rows) == 10

    return {
        "summary": {
            "schema": "d4-status-certificates/v1",
            "authority": "research-only-proof-bridge",
            "ratified_classification_ref": "#2156",
            "exact_width_membership_ref": "#2352/#2363",
            "generated_candidates": generated,
            "root_candidates": roots,
            "unknown_candidates": 0,
            "root_scope": "bounded Core1-bootstrap necessity only",
            "census_effect_if_accepted": {
                "generated": 20,
                "root": 2,
                "UNKNOWN": 8,
            },
            "non_conclusions": [
                "root candidate is not a global algebraic independence theorem",
                "generated resident need not lose its dedicated identity",
                "D4 address geometry is not evidence",
                "runtime/performance cost is outside this proof bridge",
            ],
        },
        "rows": rows,
    }


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def tsv_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, list):
        return ",".join(str(x) for x in value)
    return str(value).replace("\t", " ").replace("\n", " ")


def render_tsv(data: dict[str, Any]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in data["rows"]:
        writer.writerow({key: tsv_value(row.get(key)) for key in FIELDS})
    return out.getvalue()


def write_outputs(out_dir: Path) -> None:
    data = build()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "d4-status-certificates.json").write_text(
        render_json(data), encoding="utf-8"
    )
    (out_dir / "d4-status-certificates.tsv").write_text(
        render_tsv(data), encoding="utf-8"
    )
    (out_dir / "d4-status-certificates-summary.json").write_text(
        json.dumps(data["summary"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_outputs(target_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        write_outputs(tmp_dir)
        for name in ("d4-status-certificates.json", "d4-status-certificates.tsv"):
            expected = (tmp_dir / name).read_bytes()
            actual = target_dir / name
            if not actual.exists() or actual.read_bytes() != expected:
                raise SystemExit(
                    f"stale D4 status certificate projection: {actual}; "
                    "run with --write"
                )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--target-dir", type=Path, default=Path("knowledge"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.write:
        write_outputs(args.target_dir)
    else:
        check_outputs(args.target_dir)

    if args.out:
        write_outputs(args.out)

    print(json.dumps(build()["summary"], sort_keys=True))
    print("STATUS=PASS-D4-STATUS-CERTIFICATE-STATIC-BRIDGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
