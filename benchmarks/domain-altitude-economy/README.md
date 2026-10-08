# Domain altitude economy — #4397 / #4398

Research-only consumer for the SENS authoring Pareto principle.

## Question

For two **already proven equivalent** programs, what trade-off exists between:

1. semantic altitude — the maximum exact domain width used by semantic residents;
2. exact dense bit cost.

There is no weighted score and no single global winner.

A variant is dominated only when another variant is no worse on both axes and
strictly better on at least one.

## Equivalence comes first

This stand does not decide that two programs mean the same thing.

Each JSONL row carries an `observable_digest` supplied by an oracle/evaluator
lane. Rows sharing a `case_id` are comparable only if every digest is identical.
Digest mismatch is a hard error.

## Input schema

Required fields:

```json
{
  "case_id": "member-small-01",
  "variant_id": "resident",
  "observable_digest": "sha256:...",
  "semantic_widths": [3, 8, 3],
  "exact_bits": 37
}
```

`semantic_widths` contains exact widths of semantic resident identities used
by the admitted program representation. D2 structural/framing words must not be
added merely because their visible token width is 2.

`exact_bits` must come from an admitted exact-width accounting path aligned
with the execution-ladder / #2833 discipline. This consumer does not reconstruct
semantic bit cost from human names or host objects.

Optional dynamic evidence:

```json
"i_refs": 12345
```

I-refs are reported unchanged. They never participate in Pareto dominance.

## Residency dividend

An explicit pair may add:

```json
"residency_pair_id": "D8:member/use-01",
"representation_role": "resident"
```

and a matching `expanded` row with the same case and observable digest.

The stand reports:

```text
bit_dividend = expanded_exact_bits - resident_exact_bits
```

This is economy evidence only. It cannot admit, remove, relocate, or make
callable any resident.

## Run

```sh
python3 benchmarks/domain-altitude-economy/run.py rows.jsonl \
  --out /tmp/domain-altitude.json

python3 -m unittest benchmarks/domain-altitude-economy/test_run.py
```

## Boundaries

- no scalar weighted optimum;
- no comparison across different observable digests;
- no inference from English/Ukrainian/Sanskrit/LISP names;
- no SID8/Sens8/u8 semantic identity;
- no runtime/contract/domain-table modification;
- no D8/D9 residency conclusion from dividend alone;
- no release authority: this lane is non-blocking for #4250.

Phase 1 uses `max domain width` as altitude. Derivation depth may become a
separate future axis only after an admitted derivation graph exists.
