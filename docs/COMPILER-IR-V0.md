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

- `FunctionSid(Sid8)` — any registry-admitted function reference is
  identified only by its exact eight-bit SID. No Canon/necessary-form/name
  enum survives in IR provenance.
- `OrdinaryBinding` — a plain user-defined function/variable with no
  registry entry. **Not a failure** — most real programs are built from
  bindings the registry has no opinion about.
- `Literal` — a value read directly from source.

Special evaluation shapes such as quote/cond/lambda/define remain distinct
`IrNode` structures where execution order requires it, but those shapes are
not function identities. The function identity, whenever present, is only
`Sid8`.

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

## Historical bugs caught by this module

Older IR versions exposed two useful failure modes: compatibility surface
routing for `def`, and the former collision between empty structure and SID
`00000000`. Under Contract 9 both are now expressed without a second named
function ontology: `def` retains its own admitted SID and selects the define
mechanism mechanically, while `()` is a structural literal outside the
function-SID space.

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
