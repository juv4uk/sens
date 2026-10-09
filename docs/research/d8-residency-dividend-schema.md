# d8-residency-dividend — measurement schema (draft)

Proposed column schema for the **#4394** residency-dividend experiment, so the first
run does not invent its own measurement. Grounded in the existing
`benchmarks/execution-ladder-objective/` methodology and the two axes of #4394.

## The quantity

```
dividend(r) = Σ over corpus programs ( D3-expansion bits(program, r) − resident bits(program, r) )
```

Positive → the resident earns its cell. Zero/negative → candidate for archaeology,
proven by benchmark, not by taste.

## Gate (must pass before any Pareto comparison)

```
digest(execute(program with r)) == digest(execute(program with D3 expansion of r))
```

Same result digest, or the comparison is not admitted. Source text, names, ASTs and
intended meaning never count as equivalence.

## Two axes (kept separate — #4394)

- **Axis A — semantic altitude:** `max_width_used` (directly measurable proxy;
  derivation depth is a later phase).
- **Axis B — bit economy:** canonical exact semantic source bits
  (measure owner: #4368/#4367 → #4372).

## Columns

| column | meaning | source |
|---|---|---|
| `resident_id` | D8/D9 resident under test | `lib/domains/d8.lisp` |
| `resident_bits` | exact semantic bits of the resident form in the program | bit measure |
| `expansion_bits` | exact semantic bits of its D3-word expansion in the same program | bit measure |
| `delta_bits` | `expansion_bits − resident_bits` | derived |
| `program_id` | corpus program | fixed corpus |
| `max_width_used` | altitude proxy for the program | static AST |
| `digest_before`, `digest_after` | execution digests for the gate | oracle |
| `gate_ok` | `digest_before == digest_after` | derived |
| `wire_bits` | framing / tail slack / container size — **separate** from semantic bits | bit measure |
| `machine_insts`, `code_bytes` | dynamic shape | dynamic run (Cachegrind) |

Aggregate per resident over the fixed corpus → `dividend(resident)`.

## Preconditions (blocking — see the #4394 verification note)

1. a D8→D3 **expansion law** must exist (and must not be invented by the optimizer);
2. a **corpus of real programs** that use residents (not the tiny `benchmarks/d8-*` semantic witnesses);
3. the **same** bit measure on both axes, or the axes are not commensurable.

## What this schema deliberately does NOT do

- it does not pick an "optimal" program — no scalar objective (#1987);
- it does not define an expansion — that is a law, upstream;
- it does not become language authority: it **measures**, it does not decide.
