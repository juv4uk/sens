# Compiler oracle corpus (GitHub issue juv4uk/my-lisp#67)

Depends on and follows #66 (`docs/COMPILER-AUTHORITY-BOUNDARY.md`): the
boundary defines *what* a compiler must preserve; this corpus is the
concrete, executable set of cases a compiler backend (`cml`,
`wsm-my-lisp`'s asm nucleus, a future WASM/FPGA target) must reproduce
exactly, before any lowering or optimization is trusted.

## What the corpus is

A curated **subset** of `tests/fixtures/conformance.lisp` — not a new,
parallel fixture file. Selected entries carry a new `(compiler-corpus
. t)` alist key, added directly alongside each entry's existing
`expr`/`expected`/`tier`/`axioms`/`role`/`note` fields — the same
layering pattern this file already uses, per wsm-my-lisp's own
proposal for how a consumer-side status key should attach to existing
fixtures rather than fork a second table that would need manual
synchronization.

`crates/my-lisp/tests/compiler_oracle_corpus.rs` is the runner:
filters `conformance.lisp` for tagged entries, evaluates each through the
current native reference evaluator (with `lib/core.lisp` loaded, matching
how the real CLI actually runs any program — an earlier draft of this
test omitted that and got a real, informative failure on the `let`
fixture below, which is itself evidence the gate works), and asserts
the recorded `expected` value or `error` kind still holds.

## Coverage against #67's required categories

| Required category | Corpus fixtures (from `conformance.lisp`) |
|---|---|
| McCarthy-7 + canon() | `(quote radio)`, `(atom (quote radio))`, `(eq (quote radio) (quote radio))`, `(car ...)`, `(cdr ...)`, `(cons ...)`, `(cond ...)` |
| Exact rationals, no float coercion | `(/ 5 6 8 7)` → `5/336` |
| Lexical shadowing, closures, dotted/variadic binding | `(eq (lambda (x) x) (lambda (x) x))` (closure identity), dotted-rest lambda, bare-symbol variadic lambda, variadic-arity error, `let`-shadowing, Canon-immutability rejection |
| Macros, error propagation | `defmacro` arity error, variadic `defmacro` success path |
| Recursion / tail calls | `count-down` 100,000-deep self-tail-call (`O(1)` host stack) |

17 fixtures total, verified: `every_corpus_fixture_matches_the_current_native_oracle`
passes in ~3 seconds — comfortably inside "small enough for ordinary
CI," #67's own acceptance criterion. If this grows past a few dozen,
`corpus_is_nonempty_and_covers_the_required_categories` has a
deliberately-set `< 40` guard that will start failing first, as a
prompt to split deep variants into nightly — the same CI-split pattern
already applied to meta-eval witnesses (commit `46b1fec`), not a new
mechanism to invent from scratch when the time comes.

## Two categories deliberately NOT forced into `conformance.lisp`'s shape

`conformance.lisp`'s alist format is one expression, one expected
value/error — it does not fit multi-statement setup. Rather than
distort either the corpus or the fixture format to cram these in, they
are referenced as already-existing, already-passing oracle evidence:

- **Advice Taker result/proof/provenance structures**:
  `crates/my-lisp/tests/advice_corpus.rs` (8 tests: `proved`/`rejected`/
  `conflict` observable outcomes across direct facts, multi-step rules,
  recursive rules, and conflicting-fact rejection).
- **Host/capability boundaries**: `crates/my-lisp/tests/host_resource_boundary.rs`
  (TCP handle mechanism-only boundary — the same opaque-handle identity
  model `docs/cyberpunk-opaque-capability-semantics.md` builds on).
- **Recursive SCC / mutual recursion** (beyond the single-function
  tail-recursion already tagged above): `crates/my-lisp/tests/meta_eval_mutual.rs`
  (2- and 3-member mutual recursion, forward references, member
  shadowing — already part of `docs/meta-eval-evidence.md`'s confirmed
  rows).

A future compiler backend's own conformance work should treat these
three files as part of the same oracle corpus in spirit, even though
they are not literally rows in `conformance.lisp`.

## Acceptance evidence (#67's own criteria)

- **"Corpus runs through current native... paths and records exact
  parity for the admitted scope"**: `every_corpus_fixture_matches_the_current_native_oracle`,
  passing.
- **"A deliberate result/error mutation is detected"**:
  `a_deliberately_wrong_expectation_is_detected_not_silently_accepted`
  constructs an in-memory corrupted entry (wrong value, then wrong
  error kind) and proves the checking function rejects both — an
  always-green CI test that exercises the detection path directly,
  rather than a one-off manual edit-and-revert experiment (the
  approach used to verify #66's gate).
- **"Small enough for ordinary CI; deep variants may live in nightly"**:
  17 fixtures, ~3 seconds, with a guard against silent unbounded growth.

Meta-evaluator parity (whether `lib/meta-eval.lisp` also reproduces these
same 17 fixtures) is intentionally out of scope for *this* corpus —
that is what `crates/my-lisp/tests/meta_eval_corpus.rs` and
`docs/meta-eval-evidence.md` already do, for the self-hosting question.
This corpus answers a different question: what must a *compiled*
execution path match, once one exists. The two efforts should stay
aware of each other but do not need to be the same mechanism.
