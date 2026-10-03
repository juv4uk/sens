#!/usr/bin/env python3
"""#2460 — bounded autonomous Core-Math closure.

The input spec contains no per-result NEG/SUB/DIV generation rules.
Generic constructor schemas enumerate reusable operation objects mechanically.

Research only. Target labels are loaded only after generation as validation
projections; they do not participate in closure or identity construction.
"""

from __future__ import annotations

import argparse
import copy
import csv
from dataclasses import dataclass, field
from hashlib import sha256
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "spec.json"
DONOR_PATH = ROOT / "scripts" / "research-2433-core-math-neutral-growth.py"

CORPUS = ("-2/1", "-1/1", "-1/2", "0/1", "1/2", "1/1", "2/1")
LAWSET_VERSION = "exact-q-equivalence-set/v1"
AC_OPS = {"add", "mul"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def load_donor():
    spec = importlib.util.spec_from_file_location("core_math_growth_2433_auto", DONOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def arg(index: int) -> dict[str, Any]:
    return {"arg": index}


def const(name: str) -> dict[str, Any]:
    return {"const": name}


def call(op: str, *args: dict[str, Any]) -> dict[str, Any]:
    return {"call": op, "args": list(args)}


TRUE_COND = {"true": True}


def nonzero(expr: dict[str, Any]) -> dict[str, Any]:
    return {"nonzero": expr}


def substitute_expr(node: dict[str, Any], mapping: dict[int, dict[str, Any]]) -> dict[str, Any]:
    if "arg" in node:
        return copy.deepcopy(mapping[node["arg"]])
    if "const" in node:
        return copy.deepcopy(node)
    return {
        "call": node["call"],
        "args": [substitute_expr(x, mapping) for x in node["args"]],
    }


def substitute_cond(node: dict[str, Any], mapping: dict[int, dict[str, Any]]) -> dict[str, Any]:
    if "true" in node:
        return TRUE_COND
    if "nonzero" in node:
        return {"nonzero": substitute_expr(node["nonzero"], mapping)}
    if "and" in node:
        return {"and": [substitute_cond(x, mapping) for x in node["and"]]}
    raise ValueError(f"unknown partiality node: {node}")


def and_cond(*conds: dict[str, Any]) -> dict[str, Any]:
    flat: list[dict[str, Any]] = []
    for cond in conds:
        if "true" in cond:
            continue
        if "and" in cond:
            flat.extend(cond["and"])
        else:
            flat.append(cond)
    if not flat:
        return TRUE_COND
    uniq = {canonical_json(x): x for x in flat}
    values = [uniq[k] for k in sorted(uniq)]
    return values[0] if len(values) == 1 else {"and": values}


def normalize_expr(node: dict[str, Any]) -> dict[str, Any]:
    if "arg" in node or "const" in node:
        return copy.deepcopy(node)
    op = node["call"]
    args = [normalize_expr(x) for x in node["args"]]
    if op in AC_OPS:
        flat: list[dict[str, Any]] = []
        for item in args:
            if item.get("call") == op:
                flat.extend(item["args"])
            else:
                flat.append(item)
        args = sorted(flat, key=canonical_json)
    return {"call": op, "args": args}


def normalize_cond(node: dict[str, Any]) -> dict[str, Any]:
    if "true" in node:
        return TRUE_COND
    if "nonzero" in node:
        return {"nonzero": normalize_expr(node["nonzero"])}
    if "and" in node:
        return and_cond(*(normalize_cond(x) for x in node["and"]))
    raise ValueError(node)


@dataclass
class Operation:
    identity: str
    arity: int
    depth: int
    expression: dict[str, Any]
    partiality: dict[str, Any]
    provenance: list[dict[str, Any]] = field(default_factory=list)
    signature_sha256: str = ""
    undefined_cases: int = 0


def identity_payload(arity: int, expr: dict[str, Any], partiality: dict[str, Any], laws: list[str]) -> dict[str, Any]:
    return {
        "schema": "core-math-autonomous-op-identity/v1",
        "carrier": "Q",
        "arity": arity,
        "lawset_version": LAWSET_VERSION,
        "normalization_laws": sorted(laws),
        "expression": normalize_expr(expr),
        "partiality": normalize_cond(partiality),
    }


def generated_identity(arity: int, expr: dict[str, Any], partiality: dict[str, Any], laws: list[str]) -> str:
    return digest(identity_payload(arity, expr, partiality, laws))


def eval_expr(module, model, node: dict[str, Any], argv: tuple[Any, ...], constants: dict[str, Any]) -> Any:
    if "arg" in node:
        return argv[node["arg"]]
    if "const" in node:
        return constants[node["const"]]
    values = [eval_expr(module, model, x, argv, constants) for x in node["args"]]
    if any(x is module.UNDEFINED for x in values):
        return module.UNDEFINED
    fn = getattr(model, node["call"])
    return fn(*values)


def signature(module, model, operation: Operation, constants: dict[str, Any]) -> tuple[str, int, list[str]]:
    outputs: list[str] = []
    undefined = 0
    for combo in itertools.product(CORPUS, repeat=operation.arity):
        argv = tuple(model.parse(x) for x in combo)
        value = eval_expr(module, model, operation.expression, argv, constants)
        rendered = model.render(value)
        if rendered == "UNDEFINED":
            undefined += 1
        outputs.append(rendered)
    payload = {
        "arity": operation.arity,
        "inputs": [list(x) for x in itertools.product(CORPUS, repeat=operation.arity)],
        "outputs": outputs,
    }
    return digest(payload), undefined, outputs


def basis_operations(spec: dict[str, Any], laws: list[str]) -> list[Operation]:
    rows: list[Operation] = []
    for entry in spec["basis_operations"]:
        op = entry["id"]
        arity = int(entry["arity"])
        expr = call(op, *(arg(i) for i in range(arity)))
        partiality = TRUE_COND if entry["partiality"] == "total" else nonzero(arg(0))
        rows.append(
            Operation(
                identity=f"basis:{op}",
                arity=arity,
                depth=0,
                expression=expr,
                partiality=partiality,
                provenance=[{"kind": "basis", "id": op}],
            )
        )
    return rows


def bind_left(binary: Operation, constant_id: str, laws: list[str]) -> Operation:
    mapping = {0: const(constant_id), 1: arg(0)}
    expr = substitute_expr(binary.expression, mapping)
    part = substitute_cond(binary.partiality, mapping)
    ident = generated_identity(1, expr, part, laws)
    return Operation(
        identity=ident,
        arity=1,
        depth=binary.depth + 1,
        expression=expr,
        partiality=part,
        provenance=[{
            "constructor": "bind-left-constant",
            "dependencies": [binary.identity],
            "constant": constant_id,
        }],
    )


def map_right(binary: Operation, unary: Operation, laws: list[str]) -> Operation:
    unary_expr = substitute_expr(unary.expression, {0: arg(1)})
    unary_part = substitute_cond(unary.partiality, {0: arg(1)})
    mapping = {0: arg(0), 1: unary_expr}
    expr = substitute_expr(binary.expression, mapping)
    binary_part = substitute_cond(binary.partiality, mapping)
    part = and_cond(unary_part, binary_part)
    ident = generated_identity(2, expr, part, laws)
    return Operation(
        identity=ident,
        arity=2,
        depth=max(binary.depth, unary.depth) + 1,
        expression=expr,
        partiality=part,
        provenance=[{
            "constructor": "map-right",
            "dependencies": [binary.identity, unary.identity],
        }],
    )


def attach_signature(module, op: Operation, constants_spec: list[dict[str, Any]]) -> None:
    model_a = module.FractionModel()
    model_b = module.PairModel()
    const_a = {x["id"]: model_a.parse(x["value"]) for x in constants_spec}
    const_b = {x["id"]: model_b.parse(x["value"]) for x in constants_spec}
    sig_a, undef_a, out_a = signature(module, model_a, op, const_a)
    sig_b, undef_b, out_b = signature(module, model_b, op, const_b)
    assert out_a == out_b
    assert undef_a == undef_b
    assert sig_a == sig_b
    op.signature_sha256 = sig_a
    op.undefined_cases = undef_a


def run_closure(spec: dict[str, Any], module) -> tuple[list[Operation], list[dict[str, Any]]]:
    laws = list(spec["normalization_laws"])
    schemas = {x["id"] for x in spec["constructor_schemas"]}
    ops = basis_operations(spec, laws)
    for op in ops:
        attach_signature(module, op, spec["constants"])

    by_identity = {op.identity: op for op in ops}
    metrics: list[dict[str, Any]] = []

    for depth in range(1, int(spec["max_depth"]) + 1):
        snapshot = list(by_identity.values())
        raw = 0
        type_rejected = 0
        identity_dedup = 0
        new_count = 0

        if "bind-left-constant" in schemas:
            for dep in snapshot:
                if dep.depth + 1 != depth:
                    continue
                for constant in spec["constants"]:
                    raw += 1
                    if dep.arity != 2:
                        type_rejected += 1
                        continue
                    candidate = bind_left(dep, constant["id"], laws)
                    attach_signature(module, candidate, spec["constants"])
                    existing = by_identity.get(candidate.identity)
                    if existing is not None:
                        existing.provenance.extend(candidate.provenance)
                        identity_dedup += 1
                    else:
                        by_identity[candidate.identity] = candidate
                        new_count += 1

        snapshot = list(by_identity.values())
        if "map-right" in schemas:
            for left in snapshot:
                for right in snapshot:
                    if max(left.depth, right.depth) + 1 != depth:
                        continue
                    raw += 1
                    if left.arity != 2 or right.arity != 1:
                        type_rejected += 1
                        continue
                    candidate = map_right(left, right, laws)
                    attach_signature(module, candidate, spec["constants"])
                    existing = by_identity.get(candidate.identity)
                    if existing is not None:
                        existing.provenance.extend(candidate.provenance)
                        identity_dedup += 1
                    else:
                        by_identity[candidate.identity] = candidate
                        new_count += 1

        generated = [x for x in by_identity.values() if x.depth == depth]
        metrics.append({
            "depth": depth,
            "raw_candidates": raw,
            "type_rejected": type_rejected,
            "identity_dedup": identity_dedup,
            "new_unique_identities": new_count,
            "unique_at_depth": len(generated),
        })

    return list(by_identity.values()), metrics


def target_signatures(module) -> dict[str, str]:
    donor_spec = json.loads((ROOT / "docs" / "research" / "2433-core-math-neutral-v1.json").read_text(encoding="utf-8"))
    operations_a, _ = module.compile_spec(donor_spec, module.FractionModel())
    constants: list[dict[str, Any]] = donor_spec["constants"]
    result: dict[str, str] = {}
    arities = {"neg": 1, "sub": 2, "div": 2}
    for name, arity in arities.items():
        rule = next(x for x in donor_spec["generation_rules"] if x["id"] == name)
        expr = rule["expression"]
        # Expand the named donor rule through the donor compiler by evaluating its function.
        outputs: list[str] = []
        for combo in itertools.product(CORPUS, repeat=arity):
            argv = tuple(module.FractionModel().parse(x) for x in combo)
            value = operations_a[name](*argv)
            outputs.append(module.FractionModel().render(value))
        payload = {
            "arity": arity,
            "inputs": [list(x) for x in itertools.product(CORPUS, repeat=arity)],
            "outputs": outputs,
        }
        result[name] = digest(payload)
    return result


def find_matches(ops: list[Operation], targets: dict[str, str]) -> dict[str, list[Operation]]:
    return {
        name: [op for op in ops if op.depth > 0 and op.signature_sha256 == sig]
        for name, sig in targets.items()
    }


def variant(spec: dict[str, Any], *, remove_basis: str | None = None, remove_constant: str | None = None, disable_schema: str | None = None) -> dict[str, Any]:
    out = copy.deepcopy(spec)
    if remove_basis:
        out["basis_operations"] = [x for x in out["basis_operations"] if x["id"] != remove_basis]
    if remove_constant:
        out["constants"] = [x for x in out["constants"] if x["id"] != remove_constant]
    if disable_schema:
        out["constructor_schemas"] = [x for x in out["constructor_schemas"] if x["id"] != disable_schema]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert "generation_rules" not in spec
    assert {x["id"] for x in spec["basis_operations"]} == {"add", "mul", "recip"}
    assert {x["id"] for x in spec["constructor_schemas"]} == {"bind-left-constant", "map-right"}

    module = load_donor()
    targets = target_signatures(module)
    ops, metrics = run_closure(spec, module)
    matches = find_matches(ops, targets)

    assert matches["neg"], "NEG-like operation not discovered"
    assert matches["div"], "DIV-like operation not discovered"
    assert matches["sub"], "SUB-like operation not discovered"
    assert min(x.depth for x in matches["neg"]) == 1
    assert min(x.depth for x in matches["div"]) == 1
    assert min(x.depth for x in matches["sub"]) == 2

    neg_ids = {x.identity for x in matches["neg"]}
    sub_reuses_neg = False
    for sub_op in matches["sub"]:
        for proof in sub_op.provenance:
            if proof.get("constructor") == "map-right":
                if any(dep in neg_ids for dep in proof["dependencies"]):
                    sub_reuses_neg = True
    assert sub_reuses_neg, "SUB-like operation did not reuse generated NEG-like operand"

    # Observational duplicate accounting only; signatures never become identity authority.
    generated = [x for x in ops if x.depth > 0]
    signature_groups: dict[str, list[str]] = {}
    for op in generated:
        signature_groups.setdefault(op.signature_sha256, []).append(op.identity)
    observational_duplicates = sum(max(0, len(v) - 1) for v in signature_groups.values())

    controls = [
        ("remove-neg-one", variant(spec, remove_constant="neg_one"), {"neg", "sub"}),
        ("remove-mul", variant(spec, remove_basis="mul"), {"neg", "div"}),
        ("remove-add", variant(spec, remove_basis="add"), {"sub"}),
        ("remove-recip", variant(spec, remove_basis="recip"), {"div"}),
        ("disable-bind-left", variant(spec, disable_schema="bind-left-constant"), {"neg", "sub"}),
        ("disable-map-right", variant(spec, disable_schema="map-right"), {"sub", "div"}),
    ]
    control_rows = []
    for name, control_spec, must_disappear in controls:
        c_ops, _ = run_closure(control_spec, module)
        c_matches = find_matches(c_ops, targets)
        disappeared = {target for target in must_disappear if not c_matches[target]}
        assert disappeared == must_disappear, f"{name}: expected {must_disappear}, got {disappeared}"
        control_rows.append({
            "control": name,
            "required_disappear": "|".join(sorted(must_disappear)),
            "observed_disappear": "|".join(sorted(disappeared)),
            "pass": True,
        })

    rows = []
    target_by_sig = {sig: name for name, sig in targets.items()}
    for op in sorted(generated, key=lambda x: (x.depth, x.arity, x.identity)):
        rows.append({
            "identity": op.identity,
            "arity": op.arity,
            "depth": op.depth,
            "partiality": canonical_json(normalize_cond(op.partiality)),
            "semantic_signature_sha256": op.signature_sha256,
            "undefined_cases": op.undefined_cases,
            "validation_target": target_by_sig.get(op.signature_sha256, ""),
            "provenance_count": len(op.provenance),
            "expression": canonical_json(normalize_expr(op.expression)),
        })

    with (args.out / "generated-operations.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with (args.out / "depth-metrics.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(metrics[0].keys()), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(metrics)

    with (args.out / "negative-controls.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(control_rows[0].keys()), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(control_rows)

    artifact = {
        "schema": "core-math-autonomous-closure-result/v1",
        "authority": "research-only",
        "input_spec": "benchmarks/core-math-autonomous-closure/spec.json",
        "per_result_generation_rules": 0,
        "basis_count": len(spec["basis_operations"]),
        "constructor_schema_count": len(spec["constructor_schemas"]),
        "max_depth": spec["max_depth"],
        "generated_unique_identities": len(generated),
        "observational_signature_classes": len(signature_groups),
        "observational_duplicate_count": observational_duplicates,
        "targets": {
            name: [{
                "identity": op.identity,
                "depth": op.depth,
                "provenance": op.provenance,
            } for op in values]
            for name, values in matches.items()
        },
        "sub_reuses_generated_neg": sub_reuses_neg,
        "depth_metrics": metrics,
        "negative_controls": control_rows,
        "non_conclusions": [
            "target labels are validation projections only",
            "bounded semantic signatures are not identity authority",
            "constructor schemas are candidates, not final Core-Math laws",
            "unbounded closure finiteness/decidability is not proved",
            "no generated operation is admitted into Core",
        ],
    }
    (args.out / "closure.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    residue = len([x for x in generated if x.signature_sha256 not in target_by_sig])
    report = [
        "# Core-Math autonomous closure — #2460",
        "",
        f"Input per-result generation rules: **0**",
        f"Basis operations: **{len(spec['basis_operations'])}**",
        f"Generic constructor schemas: **{len(spec['constructor_schemas'])}**",
        f"Generated unique identities through depth {spec['max_depth']}: **{len(generated)}**",
        f"Bounded semantic-signature classes: **{len(signature_groups)}**",
        f"Generated objects not matching NEG/SUB/DIV validation targets: **{residue}**",
        "",
        "Positive controls:",
        f"- NEG-like discovered at depth {min(x.depth for x in matches['neg'])};",
        f"- DIV-like discovered at depth {min(x.depth for x in matches['div'])};",
        f"- SUB-like discovered at depth {min(x.depth for x in matches['sub'])};",
        f"- SUB-like provenance reuses generated NEG-like identity: **{sub_reuses_neg}**.",
        "",
        "| depth | raw candidates | type rejected | identity dedup | new identities |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in metrics:
        report.append(
            f"| {row['depth']} | {row['raw_candidates']} | {row['type_rejected']} | "
            f"{row['identity_dedup']} | {row['new_unique_identities']} |"
        )
    report += [
        "",
        "All dependency/schema removal controls PASS.",
        "",
        "Interpretation:",
        "generic admitted constructor schemas generated reusable executable operation objects",
        "that were not listed by result name in the input spec. This is a bounded",
        "autonomous-closure witness, not a claim that unbounded Core-Math growth is solved.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
