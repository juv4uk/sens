# #2003 whole-program domains — first result

Run: 2026-10-01, `benchmarks/whole-program-domains/whole_program.py`.

## Headline

Oracle parity holds on all six workloads across all four variants (asserted).

Cold (`r1`) total logical steps:

```text
workload             flat   root-suffix   hybrid   compiled
selector-heavy        885      894          886       897
append-list          1120     1363         1147      1131
member-equal          895      949          901       906
assoc-pairlis         977     1085          989       988
eval-apply-lisp15     997     1042         1002      1009
mixed-residue         884      929          889       895
```

**Composition finding:** in whole programs the resolution phase is a **minority
of total work** — its share runs from 0.1% (`selector-heavy`) to 17.8%
(`append-list`, `root-suffix`). Consequences:

1. A resolution-layer micro-win is **diluted or erased** by framing, carrier and
   execution. Here `flat` wins every workload cold, even though `root-suffix`
   has the cheaper *preparation*: its per-call path walk dominates once
   execution is counted.
2. `root-suffix` is the **worst** in composition and diverges with repetition
   (e.g. `append-list` 1363 → 52645 across r1→r100), because it pays the walk on
   every call and amortises nothing.
3. `compiled` does **not** overtake `flat` even hot (`selector-heavy` 5043 vs
   5055 at r100): per-call cost is equal and its one-time lowering is larger, so
   the amortisation never closes the gap in bounded programs.

Amortisation (total steps r1/r10/r100, `flat`): `selector-heavy` 885/1263/5043 —
i.e. the one-time table is real but small next to per-call execution.

## Acceptance checklist (#2003)

- [x] same programs across legal candidates (one evaluator, four resolution
      strategies);
- [x] oracle parity first (asserted before any metric);
- [x] per-phase differential accounting (nine `phase_*` counters);
- [x] >= 1 Lisp I and >= 1 Lisp 1.5 evaluator-related workload
      (`eval-apply-lisp15` runs the meta-circular `eval`);
- [x] mixed generated/residue workload (`mixed-residue`);
- [x] repeated hot program vs cold (`r1`/`r10`/`r100`);
- [ ] instruction counts — **pending pinned environment** (`i_refs` blank);
- [x] feeds #1973 (shared #1987 schema).

## Provenance

```json
{"python": "3.12.13", "machine": "x86_64"}
```

Raw rows: `whole_program.tsv` (72 rows = 6 workloads × 4 variants × 3 repetitions).

## Honest limits

The counters are model-specific logical steps, not instructions, and the
absolute values must not be compared with a C/Cachegrind lane. The result is a
*composition* statement — resolution is a small share and local wins do not
survive — not a performance ordering, and it ratifies no carrier, framing or
compiler design.
