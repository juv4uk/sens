# First concrete backend-neutral semantic oracle instance

Course correction 2026-09-11: the goal was never "less Rust" — it's
that my-lisp is the semantic authority regardless of which engine
executes it (`semantic identity → Lisp-owned meaning/contract/witnesses
→ implementation projection: Rust today, CML/C/WASM/FPGA later`).
Acceptance criterion for that claim, stated directly:

> Чи зможе новий backend реалізувати цю semantic identity лише з
> Canon/semantic registry/Lisp-owned contracts/oracle corpus, не
> копіюючи приховані правила з Rust?

And the closing point: "щойно один і той самий semantic corpus реально
проходить через дві різні реалізації, фраза «Lisp — король семантики»
перестає бути архітектурним наміром і стає експериментально доведеним
фактом" — once the same corpus actually passes through two real
implementations, the claim becomes an experimental fact, not an
architectural intention.

## What this adds

`crates/my-lisp/tests/compiler_corpus_dual_backend.rs` — not a new
mechanism. Applies the same native-Rust-evaluator-vs-`lib/meta-eval.lisp`
comparison shape used elsewhere in this test suite (see
`crates/my-lisp/tests/meta_eval_corpus.rs`, which drives the same
comparison off a `meta-eval` corpus tag rather than a hand-copied
expression list) specifically to #67's frozen compiler-corpus
(`tests/fixtures/conformance.lisp`'s `(compiler-corpus . t)` fixtures)
rather than the separate, broader self-hosting-tracking corpus that
file already covers.

## The current, honest, verified fact

**9 of 14** value-producing compiler-corpus fixtures pass through both
the native Rust evaluator and `lib/meta-eval.lisp`'s Lisp-owned
meta-evaluator, with byte-identical results, right now:

- All 7 McCarthy-7/canon() fixtures (`quote`/`atom`/`eq`/`car`/`cdr`/
  `cons`/`cond`) that overlap with the fixtures tagged `meta-eval` for
  `meta_eval_corpus.rs`'s self-hosting sweep.
- 2 more from the closure-identity and dotted-lambda-list categories
  (verified live, not assumed from either file's prior scope).

**5 named as coverage gaps**, not failures — `my-eval` doesn't yet
dispatch these, so no comparison was possible, distinct from a real
disagreement:

- `(/ 5 6 8 7)` — exact rational arithmetic (`/` unbound in `my-eval`'s
  current scope).
- `(eq (lambda (x) x) (lambda (x) x))` — closure identity.
- `count-down`'s named-def-plus-recursion shape (multi-statement,
  `def` + call).
- `let`-based shadowing (`let` is a `core.lisp` macro, not yet expanded
  by `my-eval`).
- Variadic `defmacro` success path.

**Zero disagreements** — the hard requirement this test enforces. If
native and meta-eval ever produce different results for a fixture both
can run, the test fails loudly; a coverage gap (meta-eval simply
doesn't support the form yet) is recorded separately, not conflated
with a real semantic split.

## A real bug found while writing this test, not assumed

`my-eval`'s own failure representation is Lisp DATA (a value shaped
like `(error unbound-symbol NAME)`), not a Rust `Result::Err` —
matches `docs/meta-eval-evidence.md`'s documented `UnknownSymbol` ↔
`unbound-symbol` correspondence, but means `eval_program` on the
wrapping `(my-eval ...)` call returns `Ok` even when the *inner*
dispatch failed. A first draft of this test classified by `Result`
variant and produced false "DISAGREEMENT" reports for every coverage
gap (`native="5/336"` vs `meta-eval="(error unbound-symbol /)"` looked
like a value mismatch until the classification was corrected to
inspect the value shape, not just the `Result` variant).

## What this is not

Not a claim that meta-eval.lisp is "done," not a claim that 9/14 is a
target percentage, and not a second execution backend in the sense the
architecture eventually wants (CML/C/WASM/FPGA) — `lib/meta-eval.lisp`
is itself still Rust-hosted (it's a Lisp *program*, interpreted by the
same native Rust evaluator it's being compared against, one level up).
It is the first concrete instance of the actual acceptance test:
proof, not intention, that a semantic fact can be checked against more
than one execution path without rewriting the fact per path. A future
CML/FPGA execution backend passing the same untouched corpus would be
the next, stronger instance of the same proof.
