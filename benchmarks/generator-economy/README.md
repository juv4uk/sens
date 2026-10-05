# Current selector closure curve (#1973)

This directory now also contains a **current Contract 11.5 closure/economics
harness**:

```sh
python3 benchmarks/generator-economy/current_closure.py \
  --out /tmp/sens-current-closure
```

It reads `knowledge/d1-d6-foundation.json` as authority, seeds only:

```text
D3:100 CAR
D3:011 CDR
```

and then derives selector children width by width. Every generated coordinate is
accepted into accounting only if the current foundation contains the exact
expected selector resident.

The mandatory current curve is:

```text
D3       2
D3..D4   6   (+4)
D3..D5  14   (+8)
D3..D6  30  (+16)
```

Outputs include:
- closure rows and marginal generated rows;
- fixed-point expansion rounds;
- deterministic seed/law/flat JSON bytes;
- representation-specific flat/model ratio;
- marginal generated rows per added law-description byte;
- coordinate payload bits;
- frontier selector vs non-selector row counts.

**Compression never ratifies a law.** The byte ratio is descriptive and
representation-specific. The semantic direction is always:

```text
current authority / proof -> admitted lift -> closure -> accounting
```

The rest of this README documents the older #2001 generic economy model.

---

# Generator economy benchmark (#2001)

Parent benchmark gate: **#1987**. Generator research: #1968. Residue: #1972.
Accounting: #1966 / #1973.

> **A semantic law earns a bit only when it explains enough to pay for itself.**

Benchmark-only research harness. It edits nothing in the runtime, contracts or
function table.

## The question

A local T0/T1 law (a generator) may be semantically valid and still be *worse*
than one explicit residue row. This lane measures only the economic side.

## Cost model (honest, deterministic, logical steps)

Per call, an explicit index lookup and a generator dispatch are modelled as the
**same** cost (1 step). So the entire difference is **one-time** cost:

```text
explicit  : materialise the whole family            = descendants rows
generator : rule_size + derive only the descendants
            the workload actually touches           = rule_size + used * depth
            used = ceil(descendants * utilisation)
```

Two consequences, stated plainly:

1. **N cancels.** In this model the decision does not depend on the number of
   calls — both routes pay the same per-call cost. The deciding variables are
   family size, utilisation and path depth. A crossover *in N* exists only when
   per-call costs are asymmetric (e.g. a runtime hash cache costing more per call
   than a table index) — that asymmetry is exactly what the pinned Cachegrind run
   must supply.
2. The bounded result is therefore a **utilisation threshold**:

```text
generator pays  <=>  utilisation < (descendants - rule_size) / (descendants * depth)
```

## Laws compared

| law | roots | descendants | semantics |
|---|---|---|---|
| `selector-carcdr-k10` (CAR/CDR family, depth 10) | 2 | 2046 | valid (positive control) |
| `selector-carcdr-k4` | 2 | 30 | valid |
| `atom-null-oneoff` | 1 | 1 | valid but a one-off |
| `eq-equal-typed-family` | 1 | 2 | valid but tiny |
| `cons-negative-evidence` | 1 | 0 | no claim (negative evidence) |
| `cond-andor-falsifier` | 1 | 1 | no claim (falsifier) |

## Falsifiers checked (all asserted in code)

- a one-off generator admitted merely because it is elegant → **rejected**;
- a law whose exceptions approach the original table size → threshold ≤ 0 → rejected;
- generator dispatch costlier with no compensating benefit → no accept verdict;
- path sharing miscounted as semantic quotient → `path_sharing_nodes` is reported
  as a **separate** count and asserted different from `semantic_nodes`.

## Run

```bash
python3 benchmarks/generator-economy/generator_economy.py \
    --tsv benchmarks/generator-economy/results/<date>/economy.tsv
```

## Output schema

Raw rows follow the shared #1987 schema verbatim (33 columns, blank when not
applicable) plus lane-specific columns appended at the end: `utilisation`,
`rows_avoided`, `semantic_nodes`, `path_sharing_nodes`, `rule_size`,
`special_cases`, `residue_required`, `semantics_valid`.

## What this harness does NOT claim

- **No instruction counts.** `i_refs`/`cpu`/`valgrind_version` are intentionally
  blank (no gcc/valgrind in this sandbox). Join them on `case_id` from the pinned
  environment; until then no per-call performance claim is made.
- No wall-time winner; the result is a step-model threshold plus a reject/accept
  verdict per law.
- No production carrier/reader/table edit, and no semantic validity inferred from
  the economy sweep (validity and economy stay separate gates).
