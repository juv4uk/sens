# ECO-CANON-1 status — 2026-09-11 (updated 2026-09-20)

Issue: [my-lisp#75](https://github.com/juv4uk/my-lisp/issues/75)  
Projection-input retirement: [my-lisp#1004](https://github.com/juv4uk/my-lisp/issues/1004)

## Principle

```text
Canon / function-table identity lives in lib/surface/semantic-registry.lisp
display spelling ≠ identity
generated function-table = reproducible projection, not semantic input authority
```

## Current authority and projections

| Piece | Role |
|---|---|
| `lib/surface/semantic-registry.lisp` | Sole numeric identity + peer-surface authority |
| `scripts/generate-function-table.lisp` | Lisp-owned projection generator; reads the registry directly |
| `lib/generated/function-table.lisp` | Machine-readable review/output projection (`ft/2`) |
| `docs/generated/function-table.md` | Human review projection, optionally joined with machine realization metadata |
| `lib/machine/intel-core-i5-6400.lisp` | Physical execution/mechanism projection only; cannot mint meaning |

The live registry currently contains **170 identities total**:

- `00000000` — structural `()`;
- **169 callable/form identities** projected by the generated function table.

The generated table schema is:

```text
ft/2:
(sid-bitstring formal (uk ...) (ukr ...) (en ...) (sa ...) (sym ...) authority)
```

`ukr` is the full Ukrainian peer surface of the same SID. There is no independent
`full-uk` identity namespace.

## Direction of authority

```text
lib/surface/semantic-registry.lisp
        ↓
one Canon/function-table SID
        ↓
generated/review projections
        ├─ lib/generated/function-table.lisp
        └─ docs/generated/function-table.md
        ↓
inspection / tooling that explicitly treats them as projections
```

The reverse direction is forbidden for semantic ownership:

```text
generated projection
        ✗
reconstruct / redefine SID meaning
```

Under #1004, active UK generators and coverage checks are being moved off
`lib/generated/function-table.lisp` as an input API and onto
`lib/surface/semantic-registry.lisp` directly.

## Ukrainian surface columns

| Column | Source |
|---|---|
| `uk` | registry `uk` surface |
| `ukr` | registry `ukr` peer surface |
| `en` | registry `en` surface |
| `sa` | registry `sa` surface |
| `sym` | registry `sym` surface |
| `authority` | `my-lisp` in the generated review projection |

The generator does not invent a missing peer spelling and does not derive one
surface namespace from another.

## Reader-sensitive apostrophe case

The quote identity's symbolic surface is stored in the registry as a string:

```lisp
(sym "'")
```

This keeps the registry ordinary re-readable Lisp data without colliding with
reader quote shorthand. Generated projections preserve that representation
mechanically; no special semantic reconstruction is required.

## What generated-table consumers may do

Allowed:

- inspect the generated artifact as an output under test;
- compare formatting/schema of that projection;
- verify that machine-specific realization metadata has not contaminated it;
- publish or pin it explicitly as a derived artifact.

Not allowed:

- derive semantic identity coverage from it when the registry is available;
- treat a generated row as an independent SID→meaning authority;
- use it to reconstruct meaning missing from Canon/function-table authority;
- create a hand-maintained replacement table.

## Commands

```bash
cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp
python3 scripts/check_semantic_registry.py
```

## Remaining work

- #1046 owns convergence of meaning/domain/law + admitted mechanisms onto the
  existing Canon/function-table identity row.
- #1049 owns the general structural guard against host/island SID→meaning
  authority outside Canon.
- #1004 retires the generated function-table specifically as an active input API
  while preserving it as a reproducible output/review projection.

## Readiness rule for other repositories

Prefer the authoritative registry when semantic identity or peer-surface data is
required. A consumer may use a published generated function-table only as an
explicitly pinned **derived projection**; it must never become an independent
source of Lisp meaning.
