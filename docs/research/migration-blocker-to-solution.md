# Migration blocker → solution (design note)

## The blocker (precise)

The exact-domain migration of `lib/compiler-nucleus.lisp` by the canonical
converter `sens-to-sens` is **not identity-preserving**. After the rewrite:

- `crates/sens/tests/compiler_l1_l5_role.rs` (which does
  `include_str!("../../../lib/compiler-nucleus.lisp")`) fails:
  `sens_l1_l5_derivation_matches_rust_oracle_for_all_d3_identities`
  → `car expects a non-empty list` at D3:000, span `3641..3656`.
- The completion gate `active_authored_lib_has_no_parser_convertible_surface_heads`
  still requires this file at `convertible=0`.

So the two requirements collide: the gate wants the file migrated; the canonical
migration of it breaks a consumer.

## Root cause (localized)

The converter rewrites **Ukrainian surface aliases** of core operations into D8
SIDs:

| surface (uk) | rewritten to |
|---|---|
| `визначити` | `00001001` (DEFINE) |
| `функція` | `00001000` (LAMBDA) |
| `за-умовою` | `00000111` (COND) |
| `атом?` | `00000010` |
| `тотожне?` | `00000011` |
| `перше` / `решта` | `00000101` / `00000110` |
| `сполучити` | `00000100` |

Behaviour changes for D3:000 (empty seed) inside `compiler-xor-bits` /
`compiler-bit-xor`, so **at least one alias resolves to a SID that is not the
intended operation in that context**. The bug is therefore in the
**alias → admitted-surface resolution**, not in the lexical walk (quote/data
positions are handled correctly — the repo's own
`tests/test_audit_lisp_migration_edits.py` passes on the rewrite).

## Solution — three levels

### 1. Tactical — a self-verifying migration driver

A migration is a rewrite **plus its consumer closure**, not a bare rewrite.
Built: `scripts/migrate-active-lib-exact.sh` v2. After `--apply` it runs the
consumers (generated reports, encoder-coverage input, the `include_str!`-based
tests) and **holds (reverts) any file whose rewrite breaks a consumer**. So a
non-identity-preserving rewrite can never land; `compiler-nucleus.lisp` is held
automatically with a reason instead of by hand.

### 2. Structural — migrate over the dependency closure

A migrated source has derived consumers that must be migrated/regenerated with
it: `include_str!` embeds, generated reports (`public-api-discovery.md`),
generated registries. The driver now checks all of them. Without this, the
gate can be "green" while a consumer is red.

### 3. Strategic — remove the class of problem

Stop *migrating* files and make **exactness the default at the source of truth**:

- generators emit exact SIDs (one generator already fixed:
  `generate-encoder-coverage-input.py`);
- the surface (Ukrainian/English names) becomes a **rendered view/lens**, not a
  separate stored state;
- the gate then becomes trivial — there is nothing "convertible" because sources
  are born exact.

This turns the recurring blocker into a non-event.

## Concrete next steps

1. **Fix the alias table** so Ukrainian aliases resolve to the same admitted
   surfaces the English ones do (or reject ambiguous aliases). Until then,
   `compiler-nucleus.lisp` is held.
2. **Add a differential identity check** to the converter: for each rewritten
   head, evaluate a witness on the original and migrated forms and assert equal
   results — a generic guard, not per-file consumer tests.
3. **Regenerate derived artifacts** as part of every migration (the driver does
   this now).

## What is built and landed

- `scripts/migrate-active-lib-exact.sh` v2 — self-verifying driver (hold-on-break).
- Generator fix for `pair` head → exact SID; regenerated index verified
  byte-identical to the canonical artifact.
- `native-first.lisp`, `admitted-iclass-index.lisp` migrated;
  `compiler-nucleus.lisp` **held** pending the alias fix.
- PR #4505 (`agent/vivaka-hub/4380-migrate-code-subset`).

## Boundary

No cargo/Lisp in the sandbox, so identity is validated by CI (the canonical
tool + the repo's tests), not by hand. I do not invent identities, and I do not
hand-edit generated files — fixes go into the generator.
