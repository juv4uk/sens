# ADR: first-class reasoning outcomes as Lisp data

Status: **IMPLEMENTED AS AN OPT-IN LIBRARY CONVENTION; HONESTY BOUNDARY UPDATED 2026-09-17.**
Originally proposed 2026-08-18 as `MYLISP-UNKNOWN-RESULT-SEMANTICS-DESIGN`.
This remains a library/API decision, not a language-contract change: there is
still no new evaluator exception mechanism and no new Rust `Value` variant.

The original design named `unknown / partial / blocked / disputed`. The Advice
Taker B1 implementation completed the algebra with the success and malformed-
input observations it also needed: `proved` and `invalid`. Existing `reason`
and `reason-in` remain backward-compatible; callers opt into the observation
layer through `reason-observe` / `reason-in-observe`.

The later #219/#244 reasoning-honesty contract narrows when those richer tags
may be produced. A tag is a positive epistemic claim, not a replacement spelling
for every empty search result. In particular, absence of proof by itself does
not establish `unknown`.

## The problem

Historically `lib/reason.lisp` returns a proof-result list on success and `()` on
failure. That compatibility API is useful, but `()` by itself does not state why
there is no ordinary proof result. Richer observations are useful only when the
reasoner has evidence for the distinction it names:

1. **Unknown** — a separately named completeness/search contract positively
   establishes that the subject was not proved under its declared scope. Mere
   absence of positive and opposite proof is not enough.
2. **Partial** — a bounded search produced only a bounded result; this is not a
   proof that no answer exists outside the bound.
3. **Blocked** — evaluation deliberately did not proceed because an operational
   precondition was unmet. A known missing module is in this class.
4. **Disputed** — mutually exclusive sides are both backed by live reasoning
   evidence.
5. **Invalid** — the requested reasoning/input shape is malformed; this is an
   input-validation observation, not logical `unknown`.
6. **Proved** — one or more proof results exist and must remain available rather
   than being collapsed to a boolean.

The honesty rule is asymmetric on purpose: a richer classification requires
positive justification. When neither side is proved and no named contract
establishes more, the unspecialized result remains Canon 0 `()` rather than an
invented `unknown` or false claim.

## Decision: one tagged-result algebra, no parallel vocabulary

The data-only shapes available in `lib/result-status.lisp` are:

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

The existence of a constructor does not authorize every caller to manufacture
that status. `contracts/reasoning-honesty-contract.lisp` owns the current
specialization boundary: `unknown` needs a named completeness/search contract;
a completely scanned missing knowledge module is `blocked`; and an ordinary
neither-side-proved observation remains `()`.

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
    -> structured observation when justified, otherwise unspecialized ()
```

This lets existing callers migrate deliberately rather than changing every
reasoning consumer in one semantic flag day.

The adapters currently observe explicit positive/opposite proofs as follows:

```text
positive only   -> (proved positive-goal all-positive-results)
opposite only   -> (proved opposite-goal all-opposite-results)
both            -> (disputed ((proved ...) (proved ...)))
neither         -> () unless a separate named contract establishes more
malformed goal  -> (invalid invalid-goal payload)
missing module  -> (blocked (module-not-found name))
```

The opposite check uses explicit knowledge, not negation-as-failure: absence of
a positive proof never manufactures a negative fact. The same evidence rule now
also applies to `unknown`: absence of both proofs never manufactures an
`unknown` classification without a separate contract that warrants it.

## Presentation boundary

`lib/narrate.lisp` may present tagged observations to a human, but presentation
is not the semantic authority. `narrate-outcome` keeps an already-established
outcome class visible so `unknown`, `partial`, `blocked`, `disputed`, and
`invalid` cannot silently collapse into one phrase.

A caller may still legitimately pass an explicitly established `(unknown
subject)` value to the presenter. That presentation law is independent from the
reasoner's stricter rule about when it may create `unknown` in the first place.

## Executable evidence

The current semantic authority is Lisp-owned:

- `contracts/reasoning-honesty-contract.lisp` states `no-proof-is-not-negation`,
  `no-evidence-is-not-unknown`, and `missing-module-is-blocked`;
- `tests/fixtures/reason-observe-honesty-v1.lisp` executes the no-evidence case
  and requires Canon 0 `()`;
- `lib/result-status.lisp` implements the same specialization boundary for
  `reason-observe` and `reason-in-observe`;
- the narration witness for an explicitly established `unknown` belongs in Lisp
  evidence rather than in a Rust test that first invents `unknown` from absent
  proof.

Rust tests may observe mechanism and integration, but they do not own the
expected epistemic classification. Historical host-side tests that encode the
older `neither -> unknown` rule are stale duplicates and should be retired only
after any unique presentation law they contain is preserved in Lisp.

## Non-goals

- No evaluator change.
- No new Rust `Value` variant.
- No automatic replacement of `reason`/`reason-in` return values.
- No claim that a bounded `partial` result is currently emitted by the ordinary
  unbounded reasoner; the tag exists for bounded callers that genuinely have
  that observation.
- No silent conversion of operational faults into `unknown`.
- No inference that Canon 0 means false, refuted, or unknown.
- No global definition of `unknown` without a named contract that states the
  scope under which non-proof was established.

This ADR records the current implemented library convention together with the
later reasoning-honesty restriction. Any future search-scoped `unknown` contract
must name its scope/completeness evidence explicitly and add executable Lisp
witnesses; it must not restore `unknown` as the default meaning of missing proof.