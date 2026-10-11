# ADR: first-class reasoning outcomes as Lisp data

Status: **IMPLEMENTED AS AN OPT-IN LIBRARY CONVENTION, 2026-09-07.**
Originally proposed 2026-08-18 as `MYLISP-UNKNOWN-RESULT-SEMANTICS-DESIGN`.
This remains a library/API decision, not a language-contract change: there is
still no new evaluator exception mechanism and no new Rust `Value` variant.

The original design named `unknown / partial / blocked / disputed`. The Advice
Taker B1 implementation completed the algebra with the success and malformed-
input observations it also needed: `proved` and `invalid`. **Current authority
has since narrowed when `unknown` may be asserted.** Under
`contracts/reasoning-honesty-contract.lisp`, absence of proof by itself does
not justify `unknown`: neither-side-proved remains unspecialized as `()`
unless a named completeness/search contract warrants a stronger conclusion.
A missing named module is `blocked`, not `unknown`. Existing `reason` and
`reason-in` remain backward-compatible; callers opt into structured outcomes
through `reason-observe` / `reason-in-observe`.

## The problem

Historically `lib/reason.lisp` returns a proof-result list on success and `()` on
failure. That compatibility API is useful, but `()` by itself cannot state why
there is no ordinary proof result. Several materially different situations
must not be reported as the same claim:

1. **Unknown** — a named completeness/search contract positively establishes
   that the relevant search space has been exhausted without proof. Mere
   absence of proof is not sufficient.
2. **Partial** — a bounded search produced only a bounded result; this is not a
   proof that no answer exists outside the bound.
3. **Blocked** — evaluation deliberately did not proceed because an operational
   precondition was unmet.
4. **Disputed** — mutually exclusive sides are both backed by live reasoning
   evidence.
5. **Invalid** — the requested reasoning/input shape is malformed; this is an
   input-validation observation, not logical `unknown`.
6. **Proved** — one or more proof results exist and must remain available rather
   than being collapsed to a boolean.

These states must not be conflated with each other or with false. At the same
time, the current honesty contract deliberately leaves **mere absence of
evidence** unspecialized as `()`: it is not silently promoted to `unknown`.
Thus `()` here means "no stronger justified reasoning outcome was established",
not FALSE.

## Decision: one tagged-result algebra, no parallel vocabulary

The canonical data-only shapes in `lib/result-status.lisp` are:

```lisp
(proved statement results)
(unknown subject)
(partial value bound)
(blocked reason)
(disputed evidence)
(invalid reason payload)
```

They are ordinary Lisp lists. No host exception type or evaluator primitive is
introduced.

`proved` stores **all** successful `reason` results, not only the first one.
That matters because backward reasoning may legitimately have several
substitutions/proof paths.

`disputed` similarly keeps evidence for both sides. It is not another spelling
for `unknown`: it positively states that incompatible sides are each supported.

## Compatibility boundary

The historical APIs are intentionally unchanged:

```text
reason / reason-in
    -> historical proof-list-or-() result

reason-observe / reason-in-observe
    -> canonical structured outcome
```

This lets existing callers migrate deliberately rather than changing every
reasoning consumer in one semantic flag day.

The adapters currently observe explicit positive/opposite proofs as follows:

```text
positive only   -> (proved positive-goal all-positive-results)
opposite only   -> (proved opposite-goal all-opposite-results)
both            -> (disputed ((proved ...) (proved ...)))
neither         -> ()
                    unless a named completeness/search contract justifies unknown
malformed goal  -> (invalid invalid-goal payload)
missing module  -> (blocked (module-not-found name))
```

The opposite check uses explicit knowledge, not negation-as-failure: absence of
a positive proof never manufactures a negative fact. Likewise, absence of both
positive and opposite proof does not manufacture `unknown`; that stronger
status requires its own completeness/search evidence.

## Presentation boundary

`lib/narrate.lisp` may present these observations to a human, but presentation is
not the semantic authority. `narrate-outcome` keeps the outcome class visible
so `unknown`, `partial`, `blocked`, `disputed`, and `invalid` cannot silently
collapse back into one "cannot prove" phrase.

A caller may still legitimately pass an explicitly established `(unknown subject)`
value to the presenter. That presentation law is independent of the stricter rule
about when a reasoner may create `unknown` in the first place.

## Executable evidence

`crates/my-lisp/tests/result_status.rs` covers:

- all six constructors/tags;
- positive proof observation;
- explicit negative/opposite proof;
- disputed two-sided evidence;
- preservation of multiple successful alternatives;
- malformed goal as `invalid`;
- unspecialized `()` when neither side is proved and no completeness/search
  contract is available;
- missing module as `blocked (module-not-found name)`.

`crates/my-lisp/tests/narrate_outcomes.rs` covers the presentation boundary for
proved, unknown, disputed, partial, blocked, invalid, and malformed outcome
shapes. Those paths are historical pre-rename test references; the current
Lisp-owned semantic authority is:
- `contracts/reasoning-honesty-contract.lisp`, which states
  `no-proof-is-not-negation`, `no-evidence-is-not-unknown`, and
  `missing-module-is-blocked`;
- `tests/fixtures/reason-observe-honesty-v1.lisp`, which executes the
  no-evidence case and requires Canon 0 `()`;
- `lib/result-status.lisp`, which implements the same specialization boundary
  for `reason-observe` and `reason-in-observe`.

Rust tests may observe mechanism and integration, but the expected epistemic
classification is Lisp-owned. Historical host-side tests that encode the older
`neither -> unknown` rule are stale duplicates and should be retired only after
any unique presentation law they carry is preserved in Lisp.

## Non-goals

- No evaluator change.
- No new Rust `Value` variant.
- No automatic replacement of `reason`/`reason-in` return values.
- No claim that a bounded `partial` result is currently emitted by the ordinary
  unbounded reasoner; the tag exists for bounded callers that genuinely have
  that observation.
- No silent conversion of operational faults into `unknown`.

This ADR records the implemented library convention, as superseded where
necessary by the current Lisp-owned reasoning-honesty contract (#219/#244).
Any future change that makes these outcomes part of Level 1/2 language
conformance would require its own deliberate contract process.
