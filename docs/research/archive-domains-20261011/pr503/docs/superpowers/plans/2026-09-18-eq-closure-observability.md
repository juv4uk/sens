# EQ Closure Observability Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Measure whether a bounded lower Lisp observation basis can distinguish two separately allocated, behaviorally identical closures that current EQ distinguishes.

**Architecture:** Persistent changes are research/docs only. A NEVER-MERGE child creates a temporary integration observer, executes real my-lisp source, removes the observer, and runs diff hygiene.

**Tech Stack:** my-lisp evaluator, GitHub Actions, temporary Rust integration observer.

**Spec:** GitHub issue #498.

## Global Constraints

- No production evaluator, EQ, Canon, registry, fixture, writer, machine, or Rust semantic changes.
- EQ is used only as the target witness, never inside the lower observation contexts.
- No host pointer/address/debug observation.
- The result may be only bounded observational evidence, never a global contextual-equivalence or irreducibility theorem.

---

### Task 1: Record the authored context corpus before execution

Create `docs/research/498/eq-closure-observability.lisp`.

Record two separately allocated identity closures `(lambda (x) x)` as the witness pair.

Target prediction:
- reused closure -> EQ same;
- two fresh closures -> EQ distinct.

Lower contexts, all without EQ:
- `atom`;
- application to `radio`, `()`, `42`, and a dotted pair;
- `eval` pass-through followed by application;
- `write-to-string`;
- `cons` transport followed by CAR/CDR and writer;
- canonical COND against static `(lambda (x) x)` datum;
- CAR-on-closure error category.

Pre-classification: `insufficient-evidence`.

### Task 2: Execute fresh live probes

Create verification-only child workflow and temporary `verify_498_eq_closure_observability.rs`.

Assert:
- target EQ same/distinct behavior;
- every authored lower context produces equal output/error category for left and right fresh closures;
- no lower source expression contains `eq`.

Run:
`cargo test -p my-lisp --test verify_498_eq_closure_observability -- --nocapture`

Remove temporary test and run `git diff --check`. Close child without merge.

### Task 3: Classify and verify research record

If all authored lower contexts coincide while EQ differs, record only:
`bounded-indistinguishability-witness`.

State exact context corpus and exact non-claim: untested contexts may still distinguish the closures.

Open research PR, run exact-head CI + bilingual gate, and feed the bounded result to #498/#471/#419.
