#!/usr/bin/env python3
"""#2326 — bounded Möbius semantic-fact accounting.

Research-only. Uses the merged #2304 semantic-fact ledger validator and the
merged #2324 generic coordinate adapter.

Three models cover the same bounded corpus of 224 projective Möbius functions:

A. flat opaque function rows;
B. canonical projective matrix coordinate IS the function identity;
C. opaque function identity plus a per-function map to the matrix coordinate.

The key falsifier is C: an algebra hidden behind old opaque IDs must pay for
the mapping rows and may lose semantic-fact compression.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_LEDGER = ROOT / "benchmarks/generator-economy/semantic-fact-ledger.json"
BASE_VALIDATOR = ROOT / "scripts/research-2304-semantic-fact-ledger.py"
COORDINATE_CHECKER = ROOT / "scripts/research-2324-coordinate-monoid-checker.py"

MODEL_FLAT = "mobius-flat224"
MODEL_DIRECT = "mobius-coordinate-direct224"
MODEL_OPAQUE_MAP = "mobius-coordinate-opaque-map224"
MODELS = (MODEL_FLAT, MODEL_DIRECT, MODEL_OPAQUE_MAP)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"MOBIUS-SEMANTIC-ACCOUNTING=FAIL\n{message}")


def load_coordinate_module():
    spec = importlib.util.spec_from_file_location("sens_coordinate_checker", COORDINATE_CHECKER)
    require(spec is not None and spec.loader is not None, "cannot load coordinate checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bounded_coordinates(coord) -> list[tuple[Fraction, Fraction, Fraction, Fraction]]:
    coeffs = tuple(Fraction(n) for n in range(-2, 3))
    unique: dict[tuple[Fraction, ...], tuple[Fraction, Fraction, Fraction, Fraction]] = {}
    for values in product(coeffs, repeat=4):
        matrix = tuple(values)
        if all(value == 0 for value in matrix):
            continue
        if coord.mdet(matrix) == 0:
            continue
        key = coord.canonical_projective(matrix)
        unique.setdefault(key, matrix)
    result = list(unique.values())
    require(len(result) == 224, f"expected 224 projective classes, got {len(result)}")
    return result


def bounded_p1_inputs(coord) -> tuple[Fraction | str, ...]:
    q = tuple(
        sorted(
            {
                Fraction(n, d)
                for n in range(-3, 4)
                for d in range(1, 4)
            }
        )
    )
    require(len(q) == 15, f"expected 15 finite rational samples, got {len(q)}")
    return q + (coord.INF,)


def signature(coord, matrix, samples) -> tuple[str, ...]:
    values = tuple(coord.mobius_apply(matrix, x) for x in samples)
    return tuple(str(value) for value in values)


def semantic_fact(
    *,
    fact_id: str,
    kind: str,
    claim: str,
    domain: str,
    applies_to: list[str],
    dependencies: list[str],
    witness: str,
    status: str,
    provenance: str,
    counterexample_class: str,
    independence_evidence: str,
    accounting_class: str = "semantic",
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "kind": kind,
        "accounting_class": accounting_class,
        "claim": claim,
        "domain": domain,
        "applies_to": applies_to,
        "dependencies": dependencies,
        "witness": witness,
        "status": status,
        "provenance": provenance,
        "counterexample_class": counterexample_class,
        "independence_evidence": independence_evidence,
    }


def add_model_to_fact(facts: list[dict[str, Any]], fact_id: str, model_ids: tuple[str, ...]) -> None:
    for fact in facts:
        if fact["id"] == fact_id:
            for model_id in model_ids:
                if model_id not in fact["applies_to"]:
                    fact["applies_to"].append(model_id)
            return
    raise AssertionError(f"missing base fact {fact_id}")


def build_extended_ledger(coord) -> tuple[dict[str, Any], dict[str, Any]]:
    base = json.loads(BASE_LEDGER.read_text(encoding="utf-8"))
    facts: list[dict[str, Any]] = base["facts"]
    models: list[dict[str, Any]] = base["models"]

    add_model_to_fact(facts, "q.carrier.exact-rational", MODELS)

    coordinates = bounded_coordinates(coord)
    samples = bounded_p1_inputs(coord)

    signatures = [signature(coord, matrix, samples) for matrix in coordinates]
    require(
        len(set(signatures)) == len(signatures) == 224,
        "bounded P1 sample does not distinguish all 224 projective classes",
    )

    common_models = [MODEL_FLAT, MODEL_DIRECT, MODEL_OPAQUE_MAP]

    facts.extend(
        [
            semantic_fact(
                fact_id="mob.carrier.p1q",
                kind="carrier-premise",
                claim="Möbius semantic inputs/outputs live on P1(Q)=Q union infinity",
                domain="P1(Q)",
                applies_to=common_models,
                dependencies=["q.carrier.exact-rational"],
                witness="#2290: finite-Q intermediate poles can recover through infinity; #2324 generic adapter",
                status="bounded-confirmed",
                provenance="#2290 #2324",
                counterexample_class="finite-Q partial semantics loses compositions recovered through infinity",
                independence_evidence="#2290 observed 4096 bounded cases where an intermediate finite-Q pole is recovered through infinity",
            ),
            semantic_fact(
                fact_id="mob.carrier.matrix2q-invertible",
                kind="carrier-premise",
                claim="function coordinates are invertible 2x2 exact-Q matrices modulo projective scale",
                domain="GL(2,Q) projectivized",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["q.carrier.exact-rational"],
                witness="#2324 MOBIUS valid_coord + bounded 224-class corpus",
                status="bounded-confirmed",
                provenance="#2290 #2324 #2326",
                counterexample_class="zero/singular matrix admitted as an ordinary PGL coordinate",
                independence_evidence="remove the matrix carrier and none of the 224 canonical coordinate values can be represented",
            ),
            semantic_fact(
                fact_id="mob.partial.det-nonzero",
                kind="partiality",
                claim="Möbius coordinate family admits only determinant-nonzero matrices",
                domain="2x2 exact-Q matrices",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.carrier.matrix2q-invertible"],
                witness="#2324 valid_coord and #2290 inverse witness",
                status="bounded-confirmed",
                provenance="#2290 #2324",
                counterexample_class="singular coordinate reaches PGL composition/inverse path",
                independence_evidence="bounded corpus excludes every singular matrix and inverse witness requires det != 0",
            ),
            semantic_fact(
                fact_id="mob.law.interpret-finite",
                kind="law",
                claim="for finite x, T_M(x)=(a*x+b)/(c*x+d), with zero denominator mapped to infinity",
                domain="PGL(2,Q) x Q -> P1(Q)",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=[
                    "mob.carrier.p1q",
                    "mob.carrier.matrix2q-invertible",
                    "mob.partial.det-nonzero",
                ],
                witness="#2290 and merged #2324 coordinate adapter",
                status="bounded-confirmed",
                provenance="#2290 #2324",
                counterexample_class="finite sample where coordinate interpretation differs",
                independence_evidence="remove this interpretation rule and finite inputs of all 224 coordinate functions are uncovered",
            ),
            semantic_fact(
                fact_id="mob.law.interpret-infinity",
                kind="law",
                claim="T_M(infinity)=infinity when c=0, otherwise a/c",
                domain="PGL(2,Q) x {infinity} -> P1(Q)",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=[
                    "mob.carrier.p1q",
                    "mob.carrier.matrix2q-invertible",
                    "mob.partial.det-nonzero",
                ],
                witness="#2324 MOBIUS adapter",
                status="bounded-confirmed",
                provenance="#2324 #2326",
                counterexample_class="infinity input interpreted as finite-Q terminal failure",
                independence_evidence="remove this rule and the infinity sample of all 224 functions is uncovered",
            ),
            semantic_fact(
                fact_id="mob.equiv.projective-scale",
                kind="equivalence",
                claim="nonzero scalar multiples kM and M denote the same Möbius function",
                domain="nonzero exact-Q scalar x GL(2,Q)",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.carrier.matrix2q-invertible"],
                witness="#2290 projective-equivalence cases; #2324 coord_equal",
                status="bounded-confirmed",
                provenance="#2290 #2324",
                counterexample_class="scalar-equivalent matrices treated as different semantic functions",
                independence_evidence="#2290 verifies 13440 bounded scalar-equivalence evaluations; without equivalence the same function has duplicate coordinates",
            ),
            semantic_fact(
                fact_id="mob.law.coordinate-is-identity",
                kind="law",
                claim="canonical projective matrix coordinate is itself the bounded function identity; no external function-to-coordinate map is required",
                domain="224 canonical bounded projective classes",
                applies_to=[MODEL_DIRECT],
                dependencies=[
                    "mob.equiv.projective-scale",
                    "mob.law.interpret-finite",
                    "mob.law.interpret-infinity",
                ],
                witness="#2326: 224 canonical coordinates produce 224 distinct signatures on 16 P1(Q) samples",
                status="bounded-confirmed",
                provenance="#2326",
                counterexample_class="two canonical coordinates collapse to one bounded semantic signature or require an opaque ID map",
                independence_evidence="bounded injectivity is executable; removing direct coordinate identity forces per-function instance maps",
            ),
            semantic_fact(
                fact_id="mob.norm.canonical-projective",
                kind="normalization",
                claim="choose one deterministic representative per projective matrix class",
                domain="projective 2x2 exact-Q coordinates",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.equiv.projective-scale"],
                witness="#2290 primitive-integer normalization; #2324 first-nonzero normalization",
                status="bounded-confirmed",
                provenance="#2290 #2324",
                counterexample_class="equivalent matrices serialize as unrelated canonical identities",
                independence_evidence="normalization is charged as mechanism, not semantic compression",
                accounting_class="mechanism",
            ),
            semantic_fact(
                fact_id="mob.cert.finite-q-nonclosure",
                kind="certificate",
                claim="ordinary finite-Q partial semantics is not closed under Möbius composition",
                domain="bounded exact-Q Möbius corpus",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.carrier.p1q"],
                witness="#2290: 4096 pole-recovered-via-infinity cases",
                status="bounded-confirmed",
                provenance="#2290",
                counterexample_class="no intermediate-pole recovery case exists",
                independence_evidence="certificate only; not counted as semantic fact",
                accounting_class="proof",
            ),
            semantic_fact(
                fact_id="mob.cert.composition-homomorphism",
                kind="certificate",
                claim="T_A(T_B(x)) = T_(A*B)(x) on P1(Q)",
                domain="sampled PGL(2,Q) x PGL(2,Q) x P1(Q)",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=[
                    "mob.law.interpret-finite",
                    "mob.law.interpret-infinity",
                    "mob.equiv.projective-scale",
                ],
                witness="#2290 102400 P1 composition cases; #2324 generic checker",
                status="bounded-confirmed",
                provenance="#2290 #2324",
                counterexample_class="composition mismatch under exact projective semantics",
                independence_evidence="derived theorem/certificate; not counted as an independent semantic fact",
                accounting_class="proof",
            ),
            semantic_fact(
                fact_id="mob.cert.identity",
                kind="certificate",
                claim="identity matrix interprets as identity map on P1(Q)",
                domain="P1(Q)",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.law.interpret-finite", "mob.law.interpret-infinity"],
                witness="#2324 common identity checker",
                status="bounded-confirmed",
                provenance="#2324",
                counterexample_class="identity coordinate changes a bounded P1 input",
                independence_evidence="derived theorem/certificate; not counted as an independent semantic fact",
                accounting_class="proof",
            ),
            semantic_fact(
                fact_id="mob.cert.inverse-adjugate",
                kind="certificate",
                claim="for det(M)!=0 the adjugate gives the inverse projective transform",
                domain="PGL(2,Q)",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.partial.det-nonzero", "mob.equiv.projective-scale"],
                witness="#2290 inverse exact cases",
                status="bounded-confirmed",
                provenance="#2290",
                counterexample_class="invertible coordinate whose adjugate fails round-trip",
                independence_evidence="derived theorem/certificate; not counted as an independent semantic fact",
                accounting_class="proof",
            ),
            semantic_fact(
                fact_id="mob.cert.generator-decomposition",
                kind="certificate",
                claim="bounded Möbius coordinates decompose through translation, scaling and reciprocal generators",
                domain="bounded PGL(2,Q) corpus",
                applies_to=[MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["mob.carrier.matrix2q-invertible", "mob.equiv.projective-scale"],
                witness="#2290 224 matrix decompositions / 3360 value cases",
                status="bounded-confirmed",
                provenance="#2290",
                counterexample_class="bounded invertible matrix with no admitted decomposition",
                independence_evidence="generative sufficiency certificate; not counted as an independent semantic fact",
                accounting_class="proof",
            ),
        ]
    )

    generic_direct = [
        "q.carrier.exact-rational",
        "mob.carrier.p1q",
        "mob.carrier.matrix2q-invertible",
        "mob.partial.det-nonzero",
        "mob.law.interpret-finite",
        "mob.law.interpret-infinity",
        "mob.equiv.projective-scale",
        "mob.law.coordinate-is-identity",
    ]
    generic_mapped = generic_direct[:-1]

    flat_rows: list[str] = []
    map_rows: list[str] = []
    direct_derived: list[dict[str, Any]] = []
    mapped_derived: list[dict[str, Any]] = []

    for index, (matrix, sig) in enumerate(zip(coordinates, signatures, strict=True)):
        row_id = f"mob.flat.row.{index:03d}"
        map_id = f"mob.map.row.{index:03d}"
        flat_rows.append(row_id)
        map_rows.append(map_id)

        digest = hashlib.sha256(repr(sig).encode("utf-8")).hexdigest()[:16]
        facts.append(
            semantic_fact(
                fact_id=row_id,
                kind="operation",
                claim=f"opaque bounded Möbius function row {index} over the fixed 16-input P1(Q) corpus",
                domain="bounded P1(Q) -> P1(Q)",
                applies_to=[MODEL_FLAT, MODEL_DIRECT, MODEL_OPAQUE_MAP],
                dependencies=["q.carrier.exact-rational", "mob.carrier.p1q"],
                witness=f"#2326 bounded signature sha256:{digest}",
                status="bounded-confirmed",
                provenance="#2326 generated flat control",
                counterexample_class="remove this opaque row and its unique bounded signature is uncovered",
                independence_evidence="flat control admits no cross-row generating law; 224 bounded signatures are unique",
            )
        )
        facts.append(
            semantic_fact(
                fact_id=map_id,
                kind="instance-map",
                claim=f"opaque function row {index} maps to canonical projective coordinate {coord.canonical_projective(matrix)}",
                domain="opaque function identity -> PGL(2,Q) coordinate",
                applies_to=[MODEL_OPAQUE_MAP],
                dependencies=["mob.carrier.matrix2q-invertible", "mob.equiv.projective-scale"],
                witness="#2326 generated mapping control",
                status="unknown",
                provenance="#2326",
                counterexample_class="mapping is derivable from the opaque ID without storing a row",
                independence_evidence="UNKNOWN: if old opaque IDs are retained, each map must be paid unless a derivation is found",
            )
        )

        direct_derived.append({"target": row_id, "via": generic_direct})
        mapped_derived.append({"target": row_id, "via": generic_mapped + [map_id]})

    models.extend(
        [
            {
                "id": MODEL_FLAT,
                "corpus": "224 opaque Möbius function rows over the same 16-input bounded P1(Q) corpus",
                "binary_participation": "B0",
                "binary_participation_note": "opaque flat function identities; binary representation carries no admitted coordinate law",
                "independent_facts": [
                    "q.carrier.exact-rational",
                    "mob.carrier.p1q",
                    *flat_rows,
                ],
                "unknown_facts": [],
                "derived_facts": [],
                "covers": flat_rows,
                "expected_semantic_fact_interval": [226, 226],
            },
            {
                "id": MODEL_DIRECT,
                "corpus": "same 224 functions; canonical projective matrix coordinate is the function identity",
                "binary_participation": "B1",
                "binary_participation_note": "exact algebraic coordinate; no per-bit semantic action claimed",
                "independent_facts": generic_direct,
                "unknown_facts": [],
                "derived_facts": direct_derived,
                "covers": flat_rows,
                "expected_semantic_fact_interval": [8, 8],
            },
            {
                "id": MODEL_OPAQUE_MAP,
                "corpus": "same 224 functions; old opaque identity retained with a per-function map to projective coordinate",
                "binary_participation": "B0",
                "binary_participation_note": "coordinate algebra is hidden behind opaque function IDs and therefore requires instance maps",
                "independent_facts": generic_mapped,
                "unknown_facts": map_rows,
                "derived_facts": mapped_derived,
                "covers": flat_rows,
                "expected_semantic_fact_interval": [7, 231],
            },
        ]
    )

    metadata = {
        "projective_classes": len(coordinates),
        "p1_samples": len(samples),
        "unique_bounded_signatures": len(set(signatures)),
        "flat_rows": len(flat_rows),
        "opaque_instance_maps": len(map_rows),
        "new_semantic_facts": len(
            [
                fact
                for fact in facts
                if fact["id"].startswith("mob.") and fact["accounting_class"] == "semantic"
            ]
        ),
        "new_proof_facts": len(
            [
                fact
                for fact in facts
                if fact["id"].startswith("mob.") and fact["accounting_class"] == "proof"
            ]
        ),
        "new_mechanism_facts": len(
            [
                fact
                for fact in facts
                if fact["id"].startswith("mob.") and fact["accounting_class"] == "mechanism"
            ]
        ),
    }
    return base, metadata


def run_validator(ledger: dict[str, Any], summary_path: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="sens-mobius-ledger-") as temp_dir:
        ledger_path = Path(temp_dir) / "extended-ledger.json"
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(BASE_VALIDATOR),
                str(ledger_path),
                "--summary-json",
                str(summary_path),
            ],
            check=True,
        )
    return json.loads(summary_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-json", default="mobius-semantic-accounting-summary.json")
    args = parser.parse_args()

    coord = load_coordinate_module()
    ledger, metadata = build_extended_ledger(coord)

    summary_path = Path(args.summary_json)
    summary = run_validator(ledger, summary_path)
    rows = {row["id"]: row for row in summary["models"]}

    flat = rows[MODEL_FLAT]
    direct = rows[MODEL_DIRECT]
    mapped = rows[MODEL_OPAQUE_MAP]

    require(flat["semantic_fact_lower_bound"] == 226, "flat total drift")
    require(direct["semantic_fact_upper_bound"] == 8, "direct coordinate total drift")
    require(mapped["semantic_fact_upper_bound"] == 231, "opaque-map upper bound drift")

    result = {
        "metadata": metadata,
        "models": {
            MODEL_FLAT: flat,
            MODEL_DIRECT: direct,
            MODEL_OPAQUE_MAP: mapped,
        },
        "direct_semantic_fact_reduction_vs_flat": 226 - 8,
        "opaque_map_upper_delta_vs_flat": 231 - 226,
        "proof_fact_count_total": summary["proof_fact_count"],
        "mechanism_fact_count_total": summary["mechanism_fact_count"],
        "conclusion": (
            "bounded coordinate compression appears only when the canonical projective "
            "coordinate is itself the function identity; retaining opaque IDs and adding "
            "per-function maps removes the gain"
        ),
    }
    summary_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("MOBIUS-SEMANTIC-ACCOUNTING=PASS")
    print(f"PROJECTIVE-CLASSES={metadata['projective_classes']}")
    print(f"P1-SAMPLES={metadata['p1_samples']}")
    print(f"UNIQUE-BOUNDED-SIGNATURES={metadata['unique_bounded_signatures']}")
    print("MODEL\tBINARY\tLOWER\tUNKNOWN\tUPPER")
    for row in (flat, direct, mapped):
        print(
            f"{row['id']}\t{row['binary_participation']}\t"
            f"{row['semantic_fact_lower_bound']}\t"
            f"{row['unknown_semantic_facts']}\t"
            f"{row['semantic_fact_upper_bound']}"
        )
    print("DIRECT-SEMANTIC-FACT-REDUCTION-VS-FLAT=218")
    print("OPAQUE-MAP-UPPER-DELTA-VS-FLAT=+5")
    print("MOBIUS-BINARY-CLASS=B1-WHEN-COORDINATE-IS-IDENTITY")
    print("THEOREMS=PROOF-FACTS-NOT-AUTOMATIC-SEMANTIC-ROOTS")
    print("NORMALIZATION=MECHANISM-FACT-NOT-FREE")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
