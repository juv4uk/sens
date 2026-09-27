# Compiler IR v0 (GitHub issue juv4uk/my-lisp#68)

Depends on #66 (authority boundary) and #67 (oracle corpus). Defines the
smallest data shape that can carry a lowered execution plan without
becoming a second language specification — per the issue's own framing,
this is data, not a second evaluator, and no execution backend is
required yet.

## Where it lives

`crates/my-lisp/src/ir.rs`, `pub(crate)` — not yet part of the public
API, per rule 7 (minimize change surface): no compiler backend consumes
it yet, so widening visibility now would be speculative. Exercised
entirely by its own `#[cfg(test)]` suite, including a full pass over
#67's frozen compiler-corpus fixtures.

## The `IrNode` shape

Nine variants, each mapping directly onto an admitted semantic identity
or ordinary structure, never inventing a new one:

- `Literal` — an exact/inexact value read from source, carried through
  unchanged (S1: never silently approximated during lowering).
- `VariableRef` — a symbol referenced for its value, tagged with a
  `Provenance` (see below).
- `Quote` — `(quote datum)`; the datum is kept as unlowered source
  `Expr`, per G3 (program structure is data) — lowering it further
  would give it executable meaning it never had.
- `Cond` — clauses kept in source order, un-evaluated; short-circuit
  evaluation order is part of admitted semantics
  (`docs/meta-eval-evidence.md`'s `cond-short-circuit` row), not a
  detail lowering may reorder.
- `Lambda` — parameter list kept as source `Expr` (covers fixed/
  dotted/bare-symbol shapes without IR reinventing lambda-list parsing).
- `Define` — covers both `define`/`визначити` (semantic ID `0011`) and
  the compatibility spelling `def` (ID `1000`, see "real bug" below).
- `Defmacro` — its own shape, body kept as unexpanded source `Expr`
  (macro expansion is `lib/macro.lisp`'s own transformation, a different
  stage than IR lowering).
- `Apply` — ordinary application; the callee's `Provenance` says
  whether it's an admitted semantic identity or a plain user binding.

## Provenance — the "why does this mean what it means" trace

Every `Literal`/`VariableRef` carries a `Provenance`:

- `Canon(CanonicalIdentity)` — one of the seven immutable Canon 0
  identities (quote/atom/eq/cons/car/cdr/cond), resolved via
  `eval::canon::identity_for_surface`.
- `NecessaryForm(NecessaryFormIdentity)` — `lambda`/`define` (0010/0011),
  via `eval::necessary_forms::identity_for_symbol`.
- `Defmacro` — semantic ID `0012`.
- `AdmittedSemanticIdentity(String)` — an ordinary callable admitted in
  `lib/surface/semantic-registry.lisp` (arithmetic, comparisons, library
  functions), carrying the numeric ID the same way
  `crates/my-lisp-cli/src/bin/cml-export.rs` already does.
- `OrdinaryBinding` — a plain user-defined function/variable with no
  registry entry. **Not a failure** — most real programs are built from
  bindings the registry has no opinion about.
- `Literal` — a value read directly from source.

`explain(&IrNode) -> String` turns any node into a one-line human trace
— #68's own acceptance criterion ("an agent or test can explain how a
source form became executable data").

## Fail-closed behavior (#66 applied to IR)

`classify_syntax_id` is the exhaustive gate: a fixed, small match from
numeric semantic ID to the five recognized special-form shapes
(quote/cond/lambda/define/defmacro). Anything claiming special-form
status that isn't in this set is rejected via
`LoweringError::UnrecognizedSyntaxIdentity`, never silently guessed at.
Structurally incomplete forms (empty operator position *that isn't*
`()` the value, wrong argument counts for a recognized special form)
fail via `LoweringError::MalformedForm`. Neither error path invents a
lowering for something it doesn't understand.

## Real bugs this module's own tests caught (not invented, not assumed)

Two, both found by running the corpus test against the real registry
resolvers before assuming they'd behave as expected:

1. **`(def x 1)` initially failed to lower as `Define`.** Two facts,
   both verified directly rather than assumed: `necessary_forms::identity_for_symbol("def")`
   returns `None` (asserted in that module's own tests), and
   `semantic_registry::semantic_id_for_surface("def")` *also* returns
   `None` — `build_surface_index` only indexes `Stable`-admission
   surfaces, and `def`'s row-1000 entry is `compatibility-only`. The
   real evaluator (`eval/mod.rs`) dispatches `"def"` as its own
   hardcoded literal string match for exactly this reason. Fixed by
   mirroring that same hardcoded check in `is_define_spelling`, not by
   routing through a registry lookup that structurally cannot see it.
2. **`(cond (() (quote wrong)) (t (quote right)))` initially failed to
   lower at all.** An earlier draft of `lower_list` treated *every*
   empty list as a malformed zero-argument call. `()` is Canon 0's
   `EmptyList` ground value — self-evaluating, per G8 (absence-of-
   element and absence-of-truth are the same value) — not a call.
   Fixed by lowering a bare `()` to a `Literal` with
   `Provenance::Canon(CanonicalIdentity::EmptyList)`.

Both are recorded as comments at their fix sites in `ir.rs`, not just
here — so a future reader hitting the same case again finds the
explanation at the code, not only in this document.

## Acceptance evidence (#68's own criteria)

- **"Lower a small but nontrivial corpus... and reconstruct enough
  provenance to explain each step"**: `lowers_and_explains_every_compiler_corpus_fixture`
  parses #67's 17 tagged `conformance.lisp` fixtures, lowers every
  sub-form, and calls `explain` on each, asserting a non-empty trace.
  Fixtures tagged with an `error` field (deliberately malformed at the
  *evaluator* level, e.g. `(defmacro foo)`'s missing arity) are allowed
  to fail lowering too, since arity checking is a runtime binding-count
  concern this IR does not attempt to replicate structurally — but
  every `expected`-tagged (success) fixture must lower cleanly.
- **"A fixture with an unknown/unadmitted semantic identity fails
  closed instead of inventing a lowering"**:
  `an_unrecognized_syntax_identity_is_rejected_not_guessed` proves
  `classify_syntax_id` returns `None` (not a guessed shape) for an
  invented ID (`"9999"`) that was never admitted.
- **"No execution backend is required yet"**: confirmed by
  construction — `ir.rs` has zero dependency on `Environment`,
  `Session`, or any evaluation function; lowering is pure
  source-`Expr`-to-data.
