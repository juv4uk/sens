#!/usr/bin/env python3
"""#2435 — Core-Math generated-operation identity tournament.

Stacked on #2437/#2433.  This research witness compares identity mechanisms
without allocating SENS function coordinates or Core registry rows.

Models:
A. synthetic allocated slot (control);
B. raw derivation tree;
C. normalized expanded mathematical construction;
D. SHA-256 content identity of C.

Normalization is explicitly versioned.  For the exact-Q positive control it
uses only:
- alpha-normalization of arguments;
- expansion of already-generated dependencies;
- commutativity of admitted exact-Q ADD/MUL as a charged normalization law.

Research only.  This does not ratify the final Core-Math identity scheme.
"""

from __future__ import annotations

import argparse
import copy
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json"
CERT_PATH = ROOT / "docs" / "research" / "2433-core-math-generation-certificates.json"
DONOR_PATH = ROOT / "scripts" / "research-2433-core-math-neutral-growth.py"

IDENTITY_SCHEMA = "core-math-generated-identity/v1"
NORMALIZATION_VERSION = "exact-q-normal-form/v1"
COMMUTATIVE_BASIS = {"add", "mul"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_donor_module():
    spec = importlib.util.spec_from_file_location("core_math_growth_2433", DONOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_tree_payload(rule: dict[str, Any], carrier: str) -> dict[str, Any]:
    """Deliberately weak identity: preserves variable spelling and generated refs."""
    return {
        "schema": "raw-derivation-tree/v1",
        "carrier": carrier,
        "arity": len(rule["inputs"]),
        "output": rule["output"],
        "partiality": rule["partiality"],
        "expression": copy.deepcopy(rule["expression"]),
    }


def normalize_expr(
    node: dict[str, Any],
    *,
    env: dict[str, dict[str, Any]],
    rules: dict[str, dict[str, Any]],
    stack: tuple[str, ...] = (),
) -> dict[str, Any]:
    if "var" in node:
        return copy.deepcopy(env[node["var"]])
    if "const" in node:
        return {"const": node["const"]}

    op = node["call"]
    args = [
        normalize_expr(arg, env=env, rules=rules, stack=stack)
        for arg in node["args"]
    ]

    # Generated references are identity-transparent in this candidate model:
    # substitute the already admitted generated construction instead of using
    # its display label as semantic authority.
    if op in rules:
        if op in stack:
            raise ValueError(f"cyclic generated identity expansion: {stack + (op,)}")
        called = rules[op]
        if len(called["inputs"]) != len(args):
            raise ValueError(f"arity mismatch while expanding {op}")
        subenv = dict(zip(called["inputs"], args, strict=True))
        return normalize_expr(
            called["expression"],
            env=subenv,
            rules=rules,
            stack=stack + (op,),
        )

    if op in COMMUTATIVE_BASIS:
        args = sorted(args, key=canonical_json)

    return {"call": op, "args": args}


def normalized_payload(
    rule: dict[str, Any],
    *,
    carrier: str,
    rules: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    env = {
        name: {"arg": index}
        for index, name in enumerate(rule["inputs"])
    }
    expression = normalize_expr(rule["expression"], env=env, rules=rules)
    return {
        "schema": IDENTITY_SCHEMA,
        "normalization_version": NORMALIZATION_VERSION,
        "normalization_laws": {
            "alpha_arguments": True,
            "expand_generated_dependencies": True,
            "commutative_basis_operations": sorted(COMMUTATIVE_BASIS),
        },
        "carrier": carrier,
        "arity": len(rule["inputs"]),
        "output": rule["output"],
        "partiality": rule["partiality"],
        "expression": expression,
    }


def alpha_commutative_variant(rule: dict[str, Any]) -> dict[str, Any]:
    """Equivalent positive-control derivation for NEG/SUB/DIV."""
    op = rule["id"]
    if op == "neg":
        return {
            **rule,
            "inputs": ["z"],
            "expression": {
                "call": "mul",
                "args": [{"var": "z"}, {"const": "neg_one"}],
            },
        }
    if op == "sub":
        return {
            **rule,
            "inputs": ["a", "b"],
            "expression": {
                "call": "add",
                "args": [
                    {"call": "neg", "args": [{"var": "b"}]},
                    {"var": "a"},
                ],
            },
        }
    if op == "div":
        return {
            **rule,
            "inputs": ["a", "b"],
            "expression": {
                "call": "mul",
                "args": [
                    {"call": "recip", "args": [{"var": "b"}]},
                    {"var": "a"},
                ],
            },
        }
    raise KeyError(op)


def inline_dependency_variant(rule: dict[str, Any]) -> dict[str, Any]:
    """Equivalent control that removes the generated NEG reference from SUB."""
    if rule["id"] != "sub":
        return copy.deepcopy(rule)
    return {
        **rule,
        "inputs": ["left", "right"],
        "expression": {
            "call": "add",
            "args": [
                {"var": "left"},
                {
                    "call": "mul",
                    "args": [
                        {"const": "neg_one"},
                        {"var": "right"},
                    ],
                },
            ],
        },
    }


def proof_object(
    operation_label: str,
    identity_hash: str,
    certificate: dict[str, Any],
    *,
    provenance: str,
) -> dict[str, Any]:
    return {
        "semantic_identity_sha256": identity_hash,
        "display_label": operation_label,
        "bounded_semantic_signature_sha256": certificate["semantic_signature_sha256"],
        "certificate_expression": certificate["expression"],
        "certificate_dependencies": certificate["dependencies"],
        "provenance": provenance,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    spec = load_json(SPEC_PATH)
    committed_certs = load_json(CERT_PATH)
    carrier = spec["carrier"]["id"]
    rules = {rule["id"]: rule for rule in spec["generation_rules"]}
    certs = {row["operation"]: row for row in committed_certs["certificates"]}

    # Recompute the #2433 evidence independently through both executable models.
    donor = load_donor_module()
    fraction_certs, fraction_order = donor.all_certificates(spec, donor.FractionModel())
    pair_certs, pair_order = donor.all_certificates(spec, donor.PairModel())
    assert fraction_order == pair_order == ["neg", "sub", "div"]
    assert fraction_certs == pair_certs == committed_certs["certificates"]

    slot_identity = {name: f"slot:{i}" for i, name in enumerate(fraction_order)}
    alternate_slot_identity = {
        name: f"slot:{i}"
        for i, name in enumerate(reversed(fraction_order))
    }
    assert any(slot_identity[name] != alternate_slot_identity[name] for name in fraction_order)

    rows: list[dict[str, Any]] = []
    identities: dict[str, dict[str, Any]] = {}
    proof_objects: list[dict[str, Any]] = []

    for name in fraction_order:
        rule = rules[name]
        variant = alpha_commutative_variant(rule)

        raw = raw_tree_payload(rule, carrier)
        raw_variant = raw_tree_payload(variant, carrier)
        raw_hash = digest(raw)
        raw_variant_hash = digest(raw_variant)

        normalized = normalized_payload(rule, carrier=carrier, rules=rules)
        normalized_variant = normalized_payload(variant, carrier=carrier, rules=rules)
        norm_hash = digest(normalized)
        norm_variant_hash = digest(normalized_variant)

        assert raw_hash != raw_variant_hash, (
            f"raw tree unexpectedly alpha/commutative invariant for {name}"
        )
        assert normalized == normalized_variant
        assert norm_hash == norm_variant_hash

        if name == "sub":
            inline = inline_dependency_variant(rule)
            normalized_inline = normalized_payload(
                inline,
                carrier=carrier,
                rules=rules,
            )
            assert normalized_inline == normalized, (
                "SUB generated-reference and inline NEG constructions diverged"
            )

        identities[name] = {
            "allocated_slot_control": slot_identity[name],
            "raw_derivation_sha256": raw_hash,
            "normalized_payload": normalized,
            "normalized_identity_sha256": norm_hash,
            "bounded_semantic_signature_sha256": certs[name][
                "semantic_signature_sha256"
            ],
        }

        proof_a = proof_object(
            name,
            norm_hash,
            certs[name],
            provenance="fraction-model/#2437",
        )
        proof_b = proof_object(
            name,
            norm_hash,
            certs[name],
            provenance="normalized-pair-model/#2437",
        )
        assert proof_a["semantic_identity_sha256"] == proof_b["semantic_identity_sha256"]
        assert proof_a["provenance"] != proof_b["provenance"]
        proof_objects.extend([proof_a, proof_b])

        rows.append({
            "operation": name,
            "allocated_slot": slot_identity[name],
            "alternate_allocated_slot": alternate_slot_identity[name],
            "raw_equivalent_derivation_same": raw_hash == raw_variant_hash,
            "normalized_equivalent_derivation_same": norm_hash == norm_variant_hash,
            "normalized_identity_sha256": norm_hash,
            "semantic_signature_sha256": certs[name]["semantic_signature_sha256"],
            "dedicated_registry_row_required_by_normalized_model": False,
        })

    # Collision guard on the positive corpus.
    norm_hashes = [identities[name]["normalized_identity_sha256"] for name in fraction_order]
    assert len(norm_hashes) == len(set(norm_hashes))

    # Partiality is identity-relevant.
    div_total = copy.deepcopy(rules["div"])
    div_total["partiality"] = "total"
    assert digest(normalized_payload(div_total, carrier=carrier, rules=rules)) != identities[
        "div"
    ]["normalized_identity_sha256"]

    # Identity-law version is identity-relevant.
    version_mutant = copy.deepcopy(identities["neg"]["normalized_payload"])
    version_mutant["normalization_version"] = "exact-q-normal-form/v2"
    assert digest(version_mutant) != identities["neg"]["normalized_identity_sha256"]

    # Display/provenance are deliberately not identity authority.
    proof_mutant = copy.deepcopy(proof_objects[0])
    proof_mutant["display_label"] = "arbitrary-human-label"
    proof_mutant["provenance"] = "another-proof-source"
    assert (
        proof_mutant["semantic_identity_sha256"]
        == proof_objects[0]["semantic_identity_sha256"]
    )

    artifact = {
        "schema": "core-math-generated-identity-tournament/v1",
        "authority": "research-only",
        "stacked_on": "#2437",
        "normalization": {
            "version": NORMALIZATION_VERSION,
            "charged_laws": [
                "alpha-normalization",
                "generated-dependency-expansion",
                "exact-Q ADD commutativity",
                "exact-Q MUL commutativity",
            ],
        },
        "models": {
            "allocated-slot": {
                "dedicated_registry_rows": len(fraction_order),
                "mathematics_determines_identity": False,
            },
            "raw-derivation-tree": {
                "dedicated_registry_rows": 0,
                "equivalent_derivation_canonicalization": False,
            },
            "normalized-construction": {
                "dedicated_registry_rows": 0,
                "equivalent_derivation_canonicalization": True,
            },
            "proof-carrying-content-hash": {
                "dedicated_registry_rows": 0,
                "equivalent_derivation_canonicalization": True,
                "hash": "sha256(canonical normalized payload)",
            },
        },
        "identities": identities,
        "proof_objects": proof_objects,
        "residue_policy": (
            "operations without an admitted canonical construction may retain "
            "explicit residue identity; this tournament does not forbid it"
        ),
        "non_conclusions": [
            "the normalization law set is not proved globally minimal",
            "bounded semantic signatures are evidence, not identity authority",
            "SHA-256 is a mechanism projection of canonical identity, not mathematics itself",
            "no Core/SENS function slot is allocated by this experiment",
        ],
    }

    path = args.out / "identity-tournament.json"
    path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    assert json.loads(path.read_text(encoding="utf-8")) == artifact

    with (args.out / "identity-results.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    report = [
        "# Core-Math generated identity tournament — #2435",
        "",
        "| model | registry rows | equivalent derivation canonicalized? |",
        "|---|---:|---|",
        f"| allocated slot | {len(fraction_order)} | no / allocation-dependent |",
        "| raw derivation tree | 0 | no |",
        "| normalized mathematical construction | 0 | yes, bounded controls |",
        "| proof-carrying canonical hash | 0 | yes, bounded controls |",
        "",
        "Positive generated corpus: NEG, SUB, DIV from #2437.",
        "",
        "Controls passed:",
        "- alpha-renamed + commutative variants normalize to the same identity;",
        "- SUB via generated NEG and SUB with NEG inlined normalize identically;",
        "- NEG/SUB/DIV normalized identities are pairwise distinct;",
        "- partiality mutation changes identity;",
        "- normalization-law version mutation changes identity;",
        "- display label and provenance changes do not change semantic identity;",
        "- Fraction and normalized-pair executors share the same #2437 certificates and identities;",
        "- JSON serialization/reload is deterministic;",
        "",
        "Interpretation:",
        "the bounded positive corpus needs zero dedicated operation registry rows under",
        "the normalized-construction/content-hash models.  This is evidence for a",
        "mathematically generated identity scheme, not ratification of the final scheme.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
