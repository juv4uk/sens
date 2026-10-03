#!/usr/bin/env python3
"""#2469 — derive requested Core-Math operations without eager closure enumeration.

Stacked on #2465/#2462.  The request file contains no NEG/SUB/DIV authority.
Operations are addressed only by replayable construction certificates.

Research only.
"""

from __future__ import annotations

import argparse
import copy
import csv
from dataclasses import dataclass
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUTO_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "run.py"
DONOR_PATH = ROOT / "scripts" / "research-2433-core-math-neutral-growth.py"
SPEC_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "spec.json"
REQUESTS_PATH = ROOT / "benchmarks" / "core-math-demand-derivation" / "requests.json"

LAWSET_VERSION = "exact-q-equivalence-set/v1"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def authority_payload(spec: dict[str, Any], request_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "carrier": spec["carrier"],
        "basis": sorted((x["id"], x["arity"], x["partiality"]) for x in spec["basis_operations"]),
        "constants": sorted((x["id"], x["value"]) for x in spec["constants"]),
        "schemas": sorted(x["id"] for x in spec["constructor_schemas"]),
        "normalization_laws": sorted(spec["normalization_laws"]),
        "lawset_version": request_doc["lawset_version"],
    }


def authority_digest(spec: dict[str, Any], request_doc: dict[str, Any]) -> str:
    return digest(authority_payload(spec, request_doc))


@dataclass
class Counters:
    basis_refs: int = 0
    constant_refs: int = 0
    ref_edges: int = 0
    constructor_apps: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    generated_materializations: int = 0


class DemandError(RuntimeError):
    pass


class Resolver:
    def __init__(
        self,
        auto,
        donor,
        spec: dict[str, Any],
        request_doc: dict[str, Any],
        *,
        memo: dict[str, Any] | None = None,
        persistent_rows: dict[str, dict[str, Any]] | None = None,
    ):
        self.auto = auto
        self.donor = donor
        self.spec = copy.deepcopy(spec)
        self.request_doc = copy.deepcopy(request_doc)
        self.requests = {
            x["id"]: x["certificate"]
            for x in self.request_doc["requests"]
        }
        self.memo = {} if memo is None else memo
        self.persistent_rows = {} if persistent_rows is None else persistent_rows
        self.counters = Counters()
        self.stack: list[str] = []
        self.laws = list(self.spec["normalization_laws"])
        self.schemas = {x["id"] for x in self.spec["constructor_schemas"]}
        self.constants = {x["id"]: x for x in self.spec["constants"]}
        self.basis_entries = {x["id"]: x for x in self.spec["basis_operations"]}
        self.basis_ops = {
            row.provenance[0]["id"]: row
            for row in self.auto.basis_operations(self.spec, self.laws)
        }
        for op in self.basis_ops.values():
            self.auto.attach_signature(self.donor, op, self.spec["constants"])
        self.auth_digest = authority_digest(self.spec, self.request_doc)

        if self.request_doc["lawset_version"] != LAWSET_VERSION:
            raise DemandError("request lawset version is not admitted")
        if sorted(self.laws) != sorted([
            "Q.add.commutative/v1",
            "Q.add.associative/v1",
            "Q.mul.commutative/v1",
            "Q.mul.associative/v1",
        ]):
            raise DemandError("active normalization law set is not the validated v1 bundle")

    def _operation_from_row(self, row: dict[str, Any]):
        op = self.auto.Operation(
            identity=row["identity"],
            arity=int(row["arity"]),
            depth=int(row["depth"]),
            expression=row["expression"],
            partiality=row["partiality"],
            provenance=row["provenance"],
            signature_sha256=row["signature_sha256"],
            undefined_cases=int(row["undefined_cases"]),
        )
        expected = self.auto.generated_identity(
            op.arity,
            op.expression,
            op.partiality,
            self.laws,
        )
        if expected != op.identity:
            raise DemandError("persistent cache identity failed recomputation")
        return op

    def _cache_row(self, op, cert_key: str) -> dict[str, Any]:
        return {
            "certificate_key": cert_key,
            "authority_digest": self.auth_digest,
            "identity": op.identity,
            "arity": op.arity,
            "depth": op.depth,
            "expression": op.expression,
            "partiality": op.partiality,
            "provenance": op.provenance,
            "signature_sha256": op.signature_sha256,
            "undefined_cases": op.undefined_cases,
        }

    def _validate_certificate_authority(self, cert: dict[str, Any]) -> None:
        if "basis" in cert:
            name = cert["basis"]
            if name not in self.basis_entries:
                raise DemandError(f"basis operation unavailable: {name}")
            return
        if "ref" in cert:
            if cert["ref"] not in self.requests:
                raise DemandError(f"unknown request reference: {cert['ref']}")
            return
        constructor = cert.get("constructor")
        if constructor not in self.schemas:
            raise DemandError(f"constructor unavailable: {constructor}")
        if constructor == "bind-left-constant":
            constant = cert.get("constant")
            if constant not in self.constants:
                raise DemandError(f"constant unavailable: {constant}")
            if "binary" not in cert:
                raise DemandError("bind-left certificate missing binary operand")
        elif constructor == "map-right":
            if "binary" not in cert or "unary" not in cert:
                raise DemandError("map-right certificate missing operand")
        else:
            raise DemandError(f"unknown constructor shape: {constructor}")

    def resolve_request(self, request_id: str):
        if request_id not in self.requests:
            raise DemandError(f"unknown request: {request_id}")
        if request_id in self.stack:
            raise DemandError(f"cyclic request reference: {request_id}")
        self.stack.append(request_id)
        try:
            return self.resolve_certificate(self.requests[request_id])
        finally:
            self.stack.pop()

    def resolve_certificate(self, cert: dict[str, Any]):
        self._validate_certificate_authority(cert)
        cert_key = digest({
            "schema": "core-math-demand-certificate-key/v1",
            "lawset_version": self.request_doc["lawset_version"],
            "certificate": cert,
        })

        if cert_key in self.memo:
            self.counters.cache_hits += 1
            return self.memo[cert_key]

        persistent = self.persistent_rows.get(cert_key)
        if persistent is not None:
            # Cache may only be used under the exact current authority digest.
            if persistent.get("authority_digest") == self.auth_digest:
                self.counters.cache_hits += 1
                op = self._operation_from_row(persistent)
                self.memo[cert_key] = op
                return op

        self.counters.cache_misses += 1

        if "basis" in cert:
            self.counters.basis_refs += 1
            op = self.basis_ops[cert["basis"]]
            self.memo[cert_key] = op
            return op

        if "ref" in cert:
            self.counters.ref_edges += 1
            op = self.resolve_request(cert["ref"])
            self.memo[cert_key] = op
            return op

        constructor = cert["constructor"]

        if constructor == "bind-left-constant":
            binary = self.resolve_certificate(cert["binary"])
            if binary.arity != 2:
                raise DemandError("bind-left requires a binary operation")
            self.counters.constant_refs += 1
            self.counters.constructor_apps += 1
            op = self.auto.bind_left(binary, cert["constant"], self.laws)

        elif constructor == "map-right":
            binary = self.resolve_certificate(cert["binary"])
            unary = self.resolve_certificate(cert["unary"])
            if binary.arity != 2 or unary.arity != 1:
                raise DemandError("map-right requires binary + unary operands")
            self.counters.constructor_apps += 1
            op = self.auto.map_right(binary, unary, self.laws)

        else:
            raise DemandError(f"unsupported constructor: {constructor}")

        self.auto.attach_signature(self.donor, op, self.spec["constants"])
        self.counters.generated_materializations += 1
        self.memo[cert_key] = op
        self.persistent_rows[cert_key] = self._cache_row(op, cert_key)
        return op


def target_signatures(auto, donor):
    return auto.target_signatures(donor)


def build_eager(auto, donor, spec: dict[str, Any]):
    eager_spec = copy.deepcopy(spec)
    eager_spec["max_depth"] = 3
    ops, metrics = auto.run_closure(eager_spec, donor)
    by_identity = {op.identity: op for op in ops}
    return ops, by_identity, metrics


def run_order(auto, donor, spec, request_doc, order, persistent_rows=None):
    resolver = Resolver(
        auto, donor, spec, request_doc,
        persistent_rows={} if persistent_rows is None else copy.deepcopy(persistent_rows),
    )
    result = {}
    for request_id in order:
        op = resolver.resolve_request(request_id)
        result[request_id] = op
    return result, resolver


def ensure_matches_eager(results, eager_by_identity):
    for request_id, op in results.items():
        if op.identity not in eager_by_identity:
            raise AssertionError(f"{request_id}: demand identity absent from eager closure")
        eager = eager_by_identity[op.identity]
        assert eager.signature_sha256 == op.signature_sha256
        assert eager.undefined_cases == op.undefined_cases
        assert eager.arity == op.arity


def invalid_controls(auto, donor, spec, request_doc, persistent_rows):
    rows = []

    def expect_reject(name, mod_spec, mod_doc, request_id, expected_fragment):
        try:
            resolver = Resolver(
                auto, donor, mod_spec, mod_doc,
                persistent_rows=copy.deepcopy(persistent_rows),
            )
            resolver.resolve_request(request_id)
        except DemandError as exc:
            if expected_fragment not in str(exc):
                raise AssertionError(f"{name}: wrong rejection {exc!r}")
            rows.append({"control": name, "rejected": True, "reason": str(exc)})
            return
        raise AssertionError(f"{name}: expected rejection")

    no_mul = copy.deepcopy(spec)
    no_mul["basis_operations"] = [x for x in no_mul["basis_operations"] if x["id"] != "mul"]
    expect_reject("withdraw-mul", no_mul, request_doc, "r1", "basis operation unavailable")

    no_map = copy.deepcopy(spec)
    no_map["constructor_schemas"] = [
        x for x in no_map["constructor_schemas"] if x["id"] != "map-right"
    ]
    expect_reject("withdraw-map-right", no_map, request_doc, "r2", "constructor unavailable")

    wrong_law_doc = copy.deepcopy(request_doc)
    wrong_law_doc["lawset_version"] = "exact-q-equivalence-set/v2"
    expect_reject("withdraw-lawset-version", spec, wrong_law_doc, "r1", "lawset version")

    bad_ref = copy.deepcopy(request_doc)
    bad_ref["requests"].append({"id": "bad", "certificate": {"ref": "missing"}})
    expect_reject("unknown-ref", spec, bad_ref, "bad", "unknown request reference")

    bad_type = copy.deepcopy(request_doc)
    bad_type["requests"].append({
        "id": "bad-type",
        "certificate": {
            "constructor": "map-right",
            "binary": {"basis": "recip"},
            "unary": {"basis": "add"},
        },
    })
    expect_reject("type-invalid", spec, bad_type, "bad-type", "map-right requires binary + unary")

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    auto = load_module(AUTO_PATH, "core_math_auto_2469")
    donor = load_module(DONOR_PATH, "core_math_growth_2469")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    request_doc = json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))

    assert "generation_rules" not in spec
    assert {x["id"] for x in request_doc["requests"]} == {"r1", "r2", "r3"}

    eager_ops, eager_by_identity, eager_metrics = build_eager(auto, donor, spec)
    eager_generated = [op for op in eager_ops if op.depth > 0]
    assert len(eager_generated) == 76

    targets = target_signatures(auto, donor)
    signature_to_label = {v: k for k, v in targets.items()}

    # 1. No shared cache: each top-level request gets a fresh resolver.
    no_cache_results = {}
    no_cache_totals = Counters()
    for request_id in ["r1", "r2", "r3"]:
        result, resolver = run_order(auto, donor, spec, request_doc, [request_id])
        no_cache_results[request_id] = result[request_id]
        for field in Counters.__dataclass_fields__:
            setattr(
                no_cache_totals,
                field,
                getattr(no_cache_totals, field) + getattr(resolver.counters, field),
            )
    ensure_matches_eager(no_cache_results, eager_by_identity)

    # 2. Ephemeral memoization shared across request set.
    forward, ephemeral = run_order(
        auto, donor, spec, request_doc, ["r1", "r2", "r3"]
    )
    ensure_matches_eager(forward, eager_by_identity)

    # 3. Request-order independence.
    reverse, reverse_resolver = run_order(
        auto, donor, spec, request_doc, ["r3", "r2", "r1"]
    )
    ensure_matches_eager(reverse, eager_by_identity)
    assert {
        key: forward[key].identity for key in forward
    } == {
        key: reverse[key].identity for key in reverse
    }

    # 4. Cache-clear invariance.
    before_clear = {k: v.identity for k, v in forward.items()}
    ephemeral.memo.clear()
    after_clear = {
        request_id: ephemeral.resolve_request(request_id).identity
        for request_id in ["r1", "r2", "r3"]
    }
    assert before_clear == after_clear

    # 5. Persistent serialized memoization.
    persistent_path = args.out / "persistent-cache.json"
    persistent_payload = {
        "schema": "core-math-demand-cache/v1",
        "authority_digest": ephemeral.auth_digest,
        "rows": ephemeral.persistent_rows,
    }
    persistent_path.write_text(
        json.dumps(persistent_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    loaded = json.loads(persistent_path.read_text(encoding="utf-8"))
    assert loaded == persistent_payload

    persisted_results, persisted = run_order(
        auto,
        donor,
        spec,
        request_doc,
        ["r2", "r3", "r1"],
        persistent_rows=loaded["rows"],
    )
    ensure_matches_eager(persisted_results, eager_by_identity)
    assert {k: v.identity for k, v in persisted_results.items()} == before_clear

    # The demand request labels gain human interpretation only after derivation.
    observed_labels = {
        request_id: signature_to_label.get(op.signature_sha256, "")
        for request_id, op in forward.items()
    }
    assert observed_labels == {"r1": "neg", "r2": "sub", "r3": "div"}

    invalid_rows = invalid_controls(
        auto, donor, spec, request_doc, ephemeral.persistent_rows
    )

    rows = []
    for request_id in ["r1", "r2", "r3"]:
        op = forward[request_id]
        rows.append({
            "request_id": request_id,
            "posthoc_validation_label": observed_labels[request_id],
            "identity": op.identity,
            "depth": op.depth,
            "arity": op.arity,
            "signature_sha256": op.signature_sha256,
            "undefined_cases": op.undefined_cases,
            "eager_identity_match": op.identity in eager_by_identity,
            "certificate_bytes": len(
                canonical_json(
                    next(x["certificate"] for x in request_doc["requests"] if x["id"] == request_id)
                ).encode("utf-8")
            ),
        })

    with (args.out / "request-results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    mode_rows = [
        {
            "mode": "eager-depth3",
            "generated_materializations": len(eager_generated),
            "constructor_apps": sum(x["raw_candidates"] - x["type_rejected"] for x in eager_metrics),
            "cache_hits": 0,
            "cache_misses": 0,
            "semantic_result_set": "full-depth3",
        },
        {
            "mode": "demand-fresh-per-request",
            "generated_materializations": no_cache_totals.generated_materializations,
            "constructor_apps": no_cache_totals.constructor_apps,
            "cache_hits": no_cache_totals.cache_hits,
            "cache_misses": no_cache_totals.cache_misses,
            "semantic_result_set": "r1|r2|r3",
        },
        {
            "mode": "demand-ephemeral-shared",
            "generated_materializations": ephemeral.counters.generated_materializations,
            "constructor_apps": ephemeral.counters.constructor_apps,
            "cache_hits": ephemeral.counters.cache_hits,
            "cache_misses": ephemeral.counters.cache_misses,
            "semantic_result_set": "r1|r2|r3",
        },
        {
            "mode": "demand-persistent-replay",
            "generated_materializations": persisted.counters.generated_materializations,
            "constructor_apps": persisted.counters.constructor_apps,
            "cache_hits": persisted.counters.cache_hits,
            "cache_misses": persisted.counters.cache_misses,
            "semantic_result_set": "r1|r2|r3",
        },
    ]
    with (args.out / "mode-results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(mode_rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(mode_rows)

    with (args.out / "invalid-controls.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(invalid_rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(invalid_rows)

    # Materialization savings for the shared demand set.
    demand_unique_generated = len({
        op.identity for op in forward.values()
        if not op.identity.startswith("basis:")
    })
    # r2 depends on r1, so the unique generated set is r1/r2/r3 = 3.
    assert demand_unique_generated == 3
    assert len(eager_generated) == 76

    artifact = {
        "schema": "core-math-demand-derivation-result/v1",
        "authority": "research-only",
        "lawset_version": request_doc["lawset_version"],
        "requests": rows,
        "posthoc_validation_labels": observed_labels,
        "eager_generated_depth3": len(eager_generated),
        "demand_unique_generated_for_request_set": demand_unique_generated,
        "materialization_avoided": len(eager_generated) - demand_unique_generated,
        "request_order_independent": True,
        "cache_clear_changes_identity": False,
        "persistent_cache_replay_identity_match": True,
        "invalid_controls": invalid_rows,
        "non_conclusions": [
            "demand derivation is a mechanism for static closure, not a new semantic growth model",
            "posthoc NEG/SUB/DIV labels are validation only",
            "three request certificates do not solve general operation search",
            "persistent cache is non-authoritative and invalidated by authority digest change",
            "no Core/SENS coordinate is allocated",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core-Math demand derivation — #2469",
        "",
        f"Eager depth-3 generated identities: **{len(eager_generated)}**",
        f"Generated identities needed for request set r1/r2/r3: **{demand_unique_generated}**",
        f"Unrelated generated identities not materialized: **{len(eager_generated) - demand_unique_generated}**",
        "",
        "Post-hoc validation only:",
        f"- r1 -> {observed_labels['r1'].upper()}-like;",
        f"- r2 -> {observed_labels['r2'].upper()}-like;",
        f"- r3 -> {observed_labels['r3'].upper()}-like.",
        "",
        "All demand identities/signatures match the eager autonomous closure.",
        "Request order is identity-invariant.",
        "Clearing ephemeral cache does not change identity.",
        "Serialized cache replay preserves identity and remains bound to current authority digest.",
        "Withdrawal/malformed/type-invalid certificates fail closed.",
        "",
        "| mode | generated materializations | constructor apps | cache hits | cache misses |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in mode_rows:
        report.append(
            f"| {row['mode']} | {row['generated_materializations']} | "
            f"{row['constructor_apps']} | {row['cache_hits']} | {row['cache_misses']} |"
        )
    report += [
        "",
        "Interpretation:",
        "static mathematical closure does not require eager materialization.",
        "A requested operation can be replayed from a construction certificate,",
        "with cache remaining a removable mechanism layer.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
