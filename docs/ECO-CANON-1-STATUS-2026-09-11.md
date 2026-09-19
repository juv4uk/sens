# ECO-CANON-1 status — 2026-09-11 (updated 2026-09-12)

Issue: [my-lisp#75](https://github.com/juv4uk/my-lisp/issues/75)

## Principle (unchanged)

```text
CANON = immutable identity / meaning
display spelling ≠ identity
lib/surface/semantic-registry.lisp = sole surface↔ID authority
```

## What already existed

| Piece | Role |
|-------|------|
| `lib/surface/semantic-registry.lisp` | Numeric semantic IDs + en/uk/sa/sym surfaces |
| `scripts/check_semantic_registry.py` | Fail-closed schema checks |
| `scripts/generate-meta-semantic-registry.lisp` | Lisp-owned runtime projection for meta-eval |
| `crates/my-lisp/src/semantic_registry.rs` + `eval/canon.rs` | In-process resolvers |
| `docs/CANON-MIGRATION-PLAN-2026-09-11.md` | Consumer generator pattern |

## Deliverable status (honest, verified 2026-09-12)

1. **`scripts/generate-function-table.lisp`** — projects registry → function
   table (`ft/1`), written in my-lisp itself (2026-09-12), replacing the
   originally-committed Python version per issue #76
   (ECO-LISP-SCRIPTS-1: no new Python tooling; existing tooling migrates
   to my-lisp/wsm). Reads the registry as ordinary my-lisp data
   (`read-file`/`read-all`), not text/regex.
2. **`lib/generated/function-table.lisp`** — machine-readable table, **all
   161 identities actually generated and committed** (the prior version
   of this file was a 1-row placeholder despite this status doc's own
   earlier claim of "161 identities" — verified directly, not assumed,
   before writing this update).
3. **`docs/generated/function-table.md`** — human view, **all 161 rows**
   (the prior version had only a 10-row sample), column order:
   **Українська → Повна українська → English → Sanskrit**

### A real edge case the migration surfaced

Identity `0001`'s `sym` surface is the literal apostrophe character
(`'`). The ordinary my-lisp reader treats a bare `'` as its own
quote-shorthand macro (reads the *next* datum), not a plain 3-token
symbol — so `(sym ' stable)` in the registry source parses as
`(sym (quote stable))`, a 2-element list, not the intended 3-element
`(lang word status)` shape every other row has. The generator
reconstructs the intended shape on read, and emits the word as a
quoted string literal (`"'"`) in the generated `.lisp` output
specifically — a bare `'` there would hit the exact same collision for
the next reader. The generated `.md` table keeps it as a plain
character (prose has no such ambiguity).

### Column policy (honest, unchanged)

| Column | Source |
|--------|--------|
| `uk` | registry `uk` surface as-is |
| `full-uk` | **mirrors** stable/candidate `uk` until a separate ratification pass; **does not invent** names |
| `full-uk-status` | `stable` / `candidate` / `needs-review` / `missing` |
| `en` / `sa` / `sym` | registry |
| `authority` | always `my-lisp` for language identities |

At generation (2026-09-12, verified against the committed files, not
estimated): **161** identities projected.

### Not done yet (remaining #75)

- Formal semantic *action* prose per ID (still stub — `formal-stub`
  only names the identity/surface, not the behavior)
- Executable witness column per row
- CI job with a `--check` mode proving the committed projection is
  current (the retired Python script had one; the my-lisp replacement
  does not yet — regeneration is currently a manual step)
- Distinct ratification of «Повна українська» where it should differ
  from `uk` (currently 100% mirror, zero rows have an independently
  ratified full-word spelling yet)
- Consumer-repo projections (must not hand-copy)

## Commands

```bash
cargo run -p my-lisp-cli --bin my-lisp -- scripts/generate-function-table.lisp
python3 scripts/check_semantic_registry.py
```

## Consumer rule

Other repos **must not** hand-copy this table. Generate from
`semantic-registry.lisp` or pin a published projection; unknown ID →
fail-closed.

## Readiness verdict for other repos switching to Canon + this table

**Not yet.** The registry itself (`semantic-registry.lisp`) has been a
safe dependency for a while and several repos already generate their
own projections from it directly (`docs/CANON-MIGRATION-PLAN-2026-09-11.md`).
This specific function-table artifact is now real (161 rows, not a
stub) and its tooling no longer conflicts with issue #76, but it still
lacks the formal-action prose, executable witnesses, and a CI
freshness check the original issue asks for — a consumer depending on
it today would be depending on an artifact this repo cannot yet prove
stays in sync with its own source automatically.