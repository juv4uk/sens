# Compiler authority boundary (GitHub issue juv4uk/my-lisp#66)

## Українське резюме

Ця межа фіксує просте правило: **Lisp визначає значення, а compiler/backend може змінювати лише механізм, представлення й стратегію виконання**. Поточний Rust evaluator не оголошується семантичним оракулом, але лишається частиною trusted execution root, доки Lisp-owned corpus і witnesses виконуються через цей runtime. Так само performance-policy має лише обирати серед уже admitted реалізацій; швидший backend не отримує права змінювати semantic ID, expected truth чи error category.

Turns the existing architectural principle — "Lisp defines meaning; a
compiler may change representation and execution strategy, but must
not invent or silently replace language semantics" — into something
checkable, not just stated. Precondition for #67 (oracle corpus) and
the rest of the compiler roadmap (#68-73): a corpus is only meaningful
if there is a clear, enforced line between what it is allowed to
freeze (Lisp-owned meaning) and what a compiler is free to vary
(mechanical execution strategy).

## What a compiler must preserve (observable semantics)

These are the things `cml`, `wsm-my-lisp`'s asm nucleus, a future WASM
compile target, or an FPGA lowering are never allowed to change,
because they are meaning, not implementation:

1. **Value identity.** `eq?`/`equal?` results, exact-vs-inexact
   distinction (`Exactness`), and exact-rational normalization (never
   silently coerced to float — this repo's own standing rule, see
   `docs/cyberpunk-numeric-representation.md`).
2. **Observable failure distinctions, where language-owned witnesses require them.**
   The language owns only the distinctions a Lisp contract or witness actually
   makes observable. Rust `ErrorKind` variant names are one backend's local
   projection, not a SENS vocabulary. A compiler may use any internal names or
   representation, provided its observable failures satisfy the same
   language-owned distinctions.
3. **Error detail, only where ADR-011 already ratifies it as
   contractual.** Per `docs/adr/ADR-011-ERROR-DETAIL-CONTRACT-BOUNDARY.md`,
   message text/span are diagnostic, not contractual, unless a future
   contract ratifies a shared structured schema — a compiler is free to
   vary diagnostic presentation, but not the *kind* classification.
4. **Evaluation order, where currently observable.** Operator before
   arguments; ordinary arguments left-to-right, stopping at the first
   failure (per `docs/meta-eval-evidence.md`'s
   `function-application-order` row). A compiler may reorder internally
   only when doing so cannot be observed (no side effects reordered
   across the boundary a Lisp program can detect).
5. **Macro/closure behavior.** Lexical capture, shared top-level
   definition frames (ADR-009), recursive SCC grouping — a compiled
   closure must behave identically to an interpreted one for any
   program that can tell the difference (captured-variable mutation,
   recursion, shadowing).
6. **Proof/provenance structures**, where a Lisp-owned library (Advice
   Taker, `lib/meta-eval.lisp`'s failure provenance) defines them — a
   compiler must not flatten or drop structure a Lisp program can
   inspect.

## What a compiler is free to vary (mechanical lowering)

- Physical representation: tagged words vs Rust enum vs WASM linear
  memory layout — `wsm-my-lisp`'s `Tag::Boxed` vs my-lisp's
  `Value::String(Rc<str>)` are already an example of two representations
  of the same semantic fact (`docs/cyberpunk-numeric-representation.md`,
  `docs/cyberpunk-opaque-capability-semantics.md`).
- Execution strategy: interpretation vs compiled-to-native vs
  hardware-synthesized (FPGA) — as long as observable behavior matches.
- Internal error representation, naming, and control flow, as long as
  observable failures satisfy the language-owned witnesses.
- Performance characteristics — nothing in this boundary makes any
  speed promise or requirement (explicitly a non-goal of #66 itself).

## Current trust root

A language-owned corpus can be the normative source of expected semantic
facts without the implementation that reads and executes that corpus becoming
semantically normative. Those are separate axes.

Today, `tests/fixtures/conformance.lisp` is the implementation-independent
contract corpus, and #113 is moving verdict logic into Lisp-owned witness
machinery. But the current execution still depends on reader/evaluator/runtime
mechanism implemented by the native system. Therefore the native Rust evaluator
is **not declared the semantic oracle**, while it **does remain part of the
current trusted execution root** used to run and observe Lisp-owned evidence.

The trust-minimization direction is:

```text
unchanged Lisp-owned corpus
          ↓
independent consumers / evaluators
          ↓
disagreement treated as evidence, never normalized away
          ↓
smaller explicitly named trusted semantic kernel
```

A disagreement does not automatically make either implementation correct. It
is evidence that the project must identify which assumption differs and which
language-owned contract/witness settles the semantic fact. Until independent
consumers reduce shared implementation assumptions, do not claim the trust
root has disappeared; name and minimize it instead.

See `docs/research/2026-09-15-semantic-self-sovereignty.md` for the dated
design-capital statement of this boundary.

## Performance non-interference

Performance policy is downstream of semantic admission and has no reverse
authority edge.

```text
implementation A passes semantic witnesses
implementation B passes semantic witnesses
                 ↓
semantically equal admitted candidates
for the covered contract
                 ↓
performance / energy / size policy selects A or B
                 ↓
NO backward edge into semantic meaning
```

Consequences:

- Benchmarks, CPU profiles, crossover thresholds, scheduler heuristics, target
  capabilities, and cost models are mechanism/policy evidence, not semantic
  authority.
- A faster implementation does not become more canonical, more semantically
  true, or a new semantic identity because it is faster.
- A selector may choose among already-admitted implementations; it may not
  rewrite semantic IDs, witness expected values, error categories, or other
  observable contracts in order to preserve its preferred performance result.
- If an optimization fails the language-owned witnesses, reject/fix the
  optimization or explicitly change the language contract through the semantic
  authority process. Performance backpressure cannot silently mutate meaning.

This rule applies equally to scalar-vs-SIMD selection, CPU/GPU/FPGA target
selection, future auto-schedulers, and ordinary compiler optimization passes.

## Explicitly forbidden

- A compiler-only special form, primitive, or macro that has no
  Lisp-side semantic definition (no "eighth McCarthy primitive," per
  #66's own acceptance criterion).
- A compiler silently treating an admitted error condition
  differently than the reference implementation (e.g. returning a
  successful-looking value where native/meta both raise `Type`).
- A compiler inventing a new language-observable failure distinction
  without a Lisp-owned contract or witness that admits that distinction.
- A compiler changing which of two independently-valid evaluation
  orders a program observes, when the reference implementation's order
  is itself part of the admitted contract.
- A performance selector or benchmark result being used as authority to
  redefine semantic identity or witness truth.

## Mechanical boundary

Rust still gets ordinary compile-time exhaustiveness from its own `match`es over
`ErrorKind`. That is a backend maintenance property, not language authority.
There is deliberately no second list of Rust variant spellings to keep in sync.
Cross-backend semantic drift is checked by Lisp-owned conformance witnesses,
which compare observable behavior rather than host enum names.

