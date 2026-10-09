# Strict-D1 COND migration — 2026-10-09

## Scope

This PR carries a source migration toward the current D3:110 contract: each executable COND clause is exactly `(test expression)`, and control values are exact D1 predicate results. This record is an engineering snapshot, not a language-law ratification.

Touched source areas:
- Core: `lib/core.lisp`, `lib/core4.lisp`
- Time source: `lib/time.lisp`
- Machine boundary: admission, encoding, operands, effects, semantic lowering, effects routing, and x86 projection under `lib/machine/`
- Adversarial range witness: `crates/sens/tests/machine_admission_adversarial.rs`
- D10 provenance: `knowledge/d10-time-law-review-v2.json` and `docs/research/D10-TIME-REVIEW.uk.md`

## Evidence collected

- Static S-expression parsing of the touched Lisp files found balanced parentheses.
- AST-aware control scan (which excludes quoted data) found no three-field clauses in the inspected live control forms across the migrated time, machine admission, encoder, lowering, effect, operand, and projection paths.
- The nine D10 review rows point to the exact `lib/time.lisp` blob and definition line numbers. These proposals remain research-only; behavior equivalence is unproven and no D10 identity was ratified.
- GitHub-hosted runs after the first machine migration passed the Vertical Day native pair witness and the machine-semantic-effect-lowering test, which exposed and helped locate an atom-only `EQ` applied to a list in `length-onto`. The core and Core4 sources now guard that equality with `ATOM` before calling `EQ`.

## Still required before merge

- Regenerate and commit `lib/core4.lisp.fasl` from the exact current PR merge candidate. The current-main CI previously checked freshness before generation, preventing artifact retrieval; PR #5232 reorders generation and enables artifact upload while retaining the tracked-file diff gate.
- Re-run the latest-head Hosted CI, Vertical Day, native machine-admission/effect tests, physical Core4/T5 witnesses, and D10 research gates.
- Investigate any remaining red checks from their logs. In particular, a stale source-route witness and the H-NIL/D8 historical contract gate must not be labeled as compiler errors or dismissed without evidence.

## Safety boundary

No direct write to `main` was performed by this language PR. Do not delete negative tests, widen host capabilities, or convert missing/failed checks to PASS. A structurally balanced source file is not by itself a proof of runtime equivalence.
