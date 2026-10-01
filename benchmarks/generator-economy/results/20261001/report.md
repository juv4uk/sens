# #2001 generator economy — first result

Run: 2026-10-01, `benchmarks/generator-economy/generator_economy.py`.

## Headline

```text
law                       rows  utilisation threshold   verdict
selector-carcdr-k10       2046  0.1108                  ACCEPT if workload touches <11.1% of the family
selector-carcdr-k4          30  0.2755                  ACCEPT if workload touches <27.6% of the family
atom-null-oneoff             1  -3.0                    REJECTED (one-off never pays for its machinery)
eq-equal-typed-family        2  -2.0                    REJECTED (one-off never pays for its machinery)
cons-negative-evidence       0  n/a                     REJECTED (no semantic claim)
cond-andor-falsifier         1  -7.0                    REJECTED (no semantic claim)
```

**Bounded result:** on this step model the generator's advantage is a *one-time
cost* decision, not a call-count decision. The CAR/CDR family at depth 10 earns
its machinery only while the workload touches **less than ~11%** of the family;
the shallower depth-4 family is more forgiving (**<27.6%**), because its mean
path depth is lower. Every one-off / tiny / no-claim law is economically rejected
even though `atom-null` is semantically plausible.

**N-cancellation witness:** `explicit_once=2046` vs `generator_once(u=0.1)=1850`
— the verdict is decided before the first call and does not move with N, because
both routes pay the same per-call step. A crossover in N requires per-call cost
asymmetry, which only instruction counts can supply.

## Falsifiers from the issue — status

| falsifier | status |
|---|---|
| one-off generator admitted merely because it is elegant | rejected (`atom-null-oneoff`, threshold < 0) |
| exceptions approach the original table size | threshold ≤ 0 → rejected |
| generator dispatch costs more with no compensating benefit | no ACCEPT verdict without a positive threshold |
| path sharing miscounted as semantic quotient | `path_sharing_nodes` reported separately and asserted ≠ `semantic_nodes` |

## Acceptance checklist (#2001)

- [x] selector family positive economy control (amortises below a threshold);
- [x] at least one semantically plausible one-off remains economically rejected
      (`atom-null-oneoff`, `eq-equal-typed-family`);
- [x] rows avoided separate from semantic-node count;
- [x] compiled route included (`compiled-route` rows);
- [x] feeds #1972/#1973 (shared #1987 schema, residue fields present);
- [ ] instruction counts — **pending pinned environment** (`i_refs` blank).

## Provenance

```json
{"python": "3.12.13", "machine": "x86_64"}
```

Raw rows: `economy.tsv` (360 rows, shared #1987 schema).

## Honest limits

The model deliberately charges the same per-call cost to both routes, so it
cannot rank them by call count — and says so. It establishes a one-time-cost
threshold and a reject/accept verdict per law, not a performance ordering, and it
does not ratify any generator, carrier or domain model.
