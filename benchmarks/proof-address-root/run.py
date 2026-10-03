#!/usr/bin/env python3
"""#2669 — proof-addressed parentless-root identity attack.

Research-only. No coordinate, resident, domain, or execution width is assigned.

Question:
Can a normalized proof/certificate address itself satisfy the Core ontology
"binary number + exact domain + proved law" for a parentless semantic root?

Current bounded answer:
- proof normalization can stabilize a certificate presentation;
- raw hashes are presentation-dependent;
- digest/storage width remains an independent projection choice;
- selector certificates replay identities already fixed by domain+law;
- the non-local-exit root proof still lacks an exact semantic domain.

Therefore, under current evidence, proof addressing is CERTIFICATE-ONLY.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
D5_MAP = ROOT / "benchmarks" / "d5-closure-map" / "run.py"
ROOT_MIN = ROOT / "benchmarks" / "post-d4-root-min-closeout" / "run.py"


def digest_hex(payload: bytes, bits: int) -> str:
    if bits == 64:
        return hashlib.sha256(payload).digest()[:8].hex()
    if bits == 128:
        return hashlib.blake2b(payload, digest_size=16).hexdigest()
    if bits == 256:
        return hashlib.sha256(payload).hexdigest()
    raise ValueError(bits)


def selector_positive_control() -> dict[str, Any]:
    ns = runpy.run_path(str(D5_MAP))
    rows = ns["selector_rows"]()
    decode = ns["decode_certificate"]

    coordinate = "10100"
    row = rows[coordinate]
    cert = row["certificate"]

    # Same semantic certificate content, deliberately serialized differently.
    raw_a = json.dumps(cert, separators=(",", ":"), sort_keys=False).encode()
    raw_b = json.dumps(cert, indent=2, sort_keys=True).encode()
    assert raw_a != raw_b
    assert hashlib.sha256(raw_a).digest() != hashlib.sha256(raw_b).digest()

    # Yet replay is stable because semantic identity comes from the selector
    # domain/law, not from a hash of certificate bytes.
    replay_a = decode(cert)
    replay_b = decode(json.loads(raw_b))
    assert replay_a == coordinate
    assert replay_b == coordinate

    return {
        "domain": row["domain"],
        "coordinate": coordinate,
        "semantic_law": row["semantic_law"],
        "semantic_law_authority": row["semantic_law_authority"],
        "certificate_schema": cert["schema"],
        "presentation_hashes_differ": True,
        "replay_coordinate_a": replay_a,
        "replay_coordinate_b": replay_b,
        "identity_stable_under_certificate_presentation": True,
        "lesson": (
            "certificate proves/replays an identity already determined by "
            "domain + selector law; certificate bytes are not semantic authority"
        ),
        "evidence": ["#2323", "#2345", "#2505"],
    }


def root_control() -> dict[str, Any]:
    rows = runpy.run_path(str(ROOT_MIN))["ROWS"]
    matches = [row for row in rows if row["factor"] == "non-local-exit"]
    assert len(matches) == 1
    row = matches[0]
    assert row["root_status"] == "PROVEN-ROOT"
    assert row["width"] == "UNKNOWN"
    assert row["coordinate"] == "UNPLACED"
    return {
        "factor": row["factor"],
        "root_status": row["root_status"],
        "width": row["width"],
        "coordinate": row["coordinate"],
        "evidence": row["evidence"],
    }


def equivalent_proof_presentations() -> dict[str, Any]:
    # Same theorem facts, different harmless ordering/formatting.
    facts = [
        "factor=non-local-exit",
        "law=exit-to-nearest-active-prog",
        "outside-active-prog=fail-closed",
        "nested-prog=nearest-active-scope",
        "same-base-d1-d4-parent=none-proved",
        "root-status=PROVEN-ROOT",
    ]
    proof_a = {
        "theorem": "non-local-exit-root",
        "facts": facts,
        "evidence": ["#2488", "#2504"],
    }
    proof_b = {
        "evidence": ["#2488", "#2504"],
        "facts": list(reversed(facts)),
        "theorem": "non-local-exit-root",
    }

    raw_a = json.dumps(proof_a, separators=(",", ":"), sort_keys=False).encode()
    raw_b = json.dumps(proof_b, indent=2, sort_keys=False).encode()
    assert raw_a != raw_b

    raw_hash_a = hashlib.sha256(raw_a).hexdigest()
    raw_hash_b = hashlib.sha256(raw_b).hexdigest()
    assert raw_hash_a != raw_hash_b

    # A possible normalizer can erase ordering/whitespace differences.
    def normalize(proof: dict[str, Any]) -> bytes:
        normalized = {
            "theorem": proof["theorem"],
            "facts": sorted(proof["facts"]),
            "evidence": sorted(proof["evidence"]),
        }
        return json.dumps(
            normalized,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()

    norm_a = normalize(proof_a)
    norm_b = normalize(proof_b)
    assert norm_a == norm_b

    projections = {
        str(bits): digest_hex(norm_a, bits)
        for bits in (64, 128, 256)
    }
    assert len(projections["64"]) * 4 == 64
    assert len(projections["128"]) * 4 == 128
    assert len(projections["256"]) * 4 == 256

    return {
        "same_semantic_fact_set": True,
        "raw_presentation_bytes_equal": False,
        "raw_sha256_equal": False,
        "normalizer_used": "sort theorem fact/evidence sets + canonical JSON",
        "normalized_bytes_equal": True,
        "projection_choices": projections,
        "projection_widths": [64, 128, 256],
        "semantic_reason_to_choose_projection_width": "NONE-PROVED",
        "semantic_reason_to_choose_hash_algorithm": "NONE-PROVED",
        "normalizer_authority": "RESEARCH-CONSTRUCTION-NOT-RATIFIED-LAW",
    }


def build_result() -> dict[str, Any]:
    selector = selector_positive_control()
    root = root_control()
    proof = equivalent_proof_presentations()

    # Current ontology requires exact semantic domain, not merely stable bytes.
    assert root["width"] == "UNKNOWN"
    assert root["coordinate"] == "UNPLACED"
    assert proof["normalized_bytes_equal"] is True
    assert proof["semantic_reason_to_choose_projection_width"] == "NONE-PROVED"

    verdict = {
        "proof_address": "CERTIFICATE-ONLY",
        "normalization": "CAN-STABILIZE-PRESENTATION",
        "exact_semantic_domain": "UNRESOLVED",
        "root_identity_width": "UNKNOWN",
        "coordinate": "UNPLACED",
        "execution_storage_projection": "NON-AUTHORITATIVE",
        "new_residents": 0,
    }

    return {
        "schema": "proof-address-root/v1",
        "issue": "#2669",
        "phase": "SENS-DERIVATION",
        "authority": "research-only-no-placement",
        "ontology": "#2490",
        "selector_certificate_positive_control": selector,
        "parentless_root_control": root,
        "proof_presentation_attack": proof,
        "verdict": verdict,
        "why_not_semantic_domain": [
            (
                "raw proof hashes depend on harmless proof presentation, so raw "
                "certificate bytes cannot be semantic identity"
            ),
            (
                "a chosen normalizer can stabilize presentation, but current Core "
                "law does not ratify that normalizer as semantic authority"
            ),
            (
                "64/128/256-bit projections of the same normalized proof are all "
                "mechanically possible; proof semantics supplies no exact-width choice"
            ),
            (
                "a stable digest is a binary number in a digest/certificate space, "
                "not evidence that the semantic root belongs to Core D5, D6, or any "
                "other exact semantic domain"
            ),
            (
                "selector certificates are the positive control: replay succeeds "
                "because the domain+generator law already determines the coordinate"
            ),
        ],
        "falsifier_for_this_verdict": (
            "provide a ratified proof calculus + canonical normalization + exact "
            "semantic-domain law that maps equivalent proofs to one binary identity "
            "while making storage/hash width a non-authoritative projection"
        ),
        "guards": [
            "proof certificate != semantic domain",
            "stable digest != Core domain membership",
            "hash width != semantic width",
            "execution/storage width != semantic authority",
            "coordinate remains unplaced",
        ],
    }


def report(result: dict[str, Any]) -> str:
    s = result["selector_certificate_positive_control"]
    p = result["proof_presentation_attack"]
    v = result["verdict"]

    return "\n".join([
        "# Proof-addressed root identity — #2669",
        "",
        "Selector positive control:",
        f"- coordinate: {s['coordinate']} in {s['domain']}",
        "- two certificate serializations hash differently",
        "- both replay to the same semantic coordinate",
        "- identity therefore comes from domain + law, not certificate bytes",
        "",
        "Parentless non-local-exit proof attack:",
        "- two harmless proof presentations have different raw SHA-256 values",
        "- a research normalizer can make their canonical bytes equal",
        "- the same normalized proof can be projected to 64/128/256 bits",
        "- no current semantic theorem chooses one digest algorithm or width",
        "",
        "Verdict:",
        f"- PROOF-ADDRESS={v['proof_address']}",
        f"- NORMALIZATION={v['normalization']}",
        f"- EXACT-SEMANTIC-DOMAIN={v['exact_semantic_domain']}",
        f"- ROOT-IDENTITY-WIDTH={v['root_identity_width']}",
        f"- COORDINATE={v['coordinate']}",
        f"- EXECUTION/STORAGE={v['execution_storage_projection']}",
        f"- NEW-RESIDENTS={v['new_residents']}",
        "",
        "A proof address remains valuable provenance/self-description evidence.",
        "Under current ontology it does not itself choose an exact Core domain.",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    result = build_result()
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "report.md").write_text(report(result), encoding="utf-8")

    print("PROOF-ADDRESS-ROOT=PASS")
    print("PROOF-ADDRESS=CERTIFICATE-ONLY")
    print("NORMALIZATION=CAN-STABILIZE-PRESENTATION")
    print("EXACT-SEMANTIC-DOMAIN=UNRESOLVED")
    print("ROOT-IDENTITY-WIDTH=UNKNOWN")
    print("COORDINATE=UNPLACED")
    print("NEW-RESIDENTS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
