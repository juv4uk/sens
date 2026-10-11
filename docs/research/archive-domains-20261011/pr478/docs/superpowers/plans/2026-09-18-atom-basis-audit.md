# ATOM Basis Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Falsify or support a strictly weaker derivation of current three-way `PRIM_ATOM` semantics without touching production semantics.

**Architecture:** Work only in `docs/research/470/**` plus verification-only child branches. The live evaluator supplies observations; temporary runner-only Rust integration tests may observe named outcomes but must not encode a replacement semantic oracle or persist in the research PR. The conclusion remains basis-relative and conservative.

**Tech Stack:** my-lisp source/evaluator, Lisp-owned structural contracts, GitHub Actions, temporary Rust integration observers.

**Spec:** GitHub issue #470 — `[P1][#419/#218] Falsify ATOM structural-kind as irreducible three-way observation`.

## Global Constraints

- No production evaluator, Canon registry, `language-contract.lisp`, semantic-fixture, machine, or Rust semantic producer edits.
- #305 owns stale Rust `atom` deletion; this plan must not edit `crates/my-lisp/src/eval/builtins.rs`.
- #218 remains authority for the current three-way result contract.
- Current target results are exactly `(structural-kind empty-list|pair|atom)`.
- Generic truth coercion remains forbidden.
- No host representation tag, `Value::is_atom`, peer-surface recursion, or hidden pair/shape oracle counts as a lower basis.
- No language-level try/catch is currently admitted; error recovery may not be assumed.
- Any result stronger than the executed evidence remains `insufficient-evidence`.

---

### Task 1: Record the lower-basis obstruction before execution

**Files:**
- Create: `docs/research/470/atom-basis-obstruction.lisp`

**Interfaces:**
- Consumes: current contracts `contracts/structural-observation-contract.lisp`, `contracts/answer-contract.lisp`, and existing fixture `tests/fixtures/structural-observation-v1.lisp` read-only.
- Produces: one research-only data record naming basis `B470`, candidate routes, predictions, and non-claims.

- [ ] **Step 1: State basis B470 explicitly**

Record:

```text
B470 = {Canon 0, quote, eq, cons, car, cdr, cond, lambda/application, define}
excluded = {atom, atom aliases, host shape tags, pair?, error catch/recovery, registry round-trip}
```

- [ ] **Step 2: State the two partial-observer candidate routes**

Route E: use `eq(x, ())` to separate Canon 0 from ordinary atoms.

Route P: force `car(x)` and discard the component to recognize a pair by successful projection.

- [ ] **Step 3: State falsification predictions before running**

```text
E(empty) -> identity-relation same
E(atom)  -> identity-relation distinct
E(pair)  -> Type

P(pair)  -> structural-kind pair
P(atom)  -> Type
P(empty) -> Type
```

Record that, without error recovery, composing E and P in either order is predicted to abort on one admitted ATOM class before a total three-way result can be produced.

- [ ] **Step 4: Commit the pre-execution research record**

Commit message:

```text
research(#470): state ATOM lower-basis falsification
```

### Task 2: Execute live evaluator probes on an isolated NEVER-MERGE child

**Files:**
- Create on child branch only: `.github/workflows/verify-470-atom-basis.yml`
- Temporary in runner only: `crates/my-lisp/tests/verify_470_atom_basis.rs`

**Interfaces:**
- Consumes: research branch from Task 1 and live `eval_program`.
- Produces: fresh Actions run proving or falsifying the exact predictions.

- [ ] **Step 1: Write the temporary integration observer in the workflow**

The observer must execute real my-lisp source and check:

```rust
// Target remains total:
(atom '())              => (structural-kind empty-list)
(atom 'radio)           => (structural-kind atom)
(atom '(radio . antenna)) => (structural-kind pair)

// EQ-zero route:
(eq '() '())                  => (identity-relation same)
(eq 'radio '())               => (identity-relation distinct)
(eq '(radio . antenna) '())   => ErrorKind::Type

// Projection-success route:
((lambda (x) ((lambda (ignored) '(structural-kind pair)) (car x)))
 '(radio . antenna))
  => (structural-kind pair)

same route on 'radio and '() => ErrorKind::Type
```

- [ ] **Step 2: Run only the focused temporary observer**

Run:

```bash
cargo test -p my-lisp --test verify_470_atom_basis -- --nocapture
```

Expected if the hypothesis is correct: all observer assertions pass, demonstrating that each proposed lower observer is partial on a different ATOM class.

- [ ] **Step 3: Remove the temporary test before diff hygiene**

Run:

```bash
rm crates/my-lisp/tests/verify_470_atom_basis.rs
git diff --check "origin/${{ github.base_ref }}...HEAD"
```

- [ ] **Step 4: Close the verification PR without merge**

Record exact verification PR, Actions run, head SHA, test count, and diff result.

### Task 3: Classify only the executed route

**Files:**
- Modify: `docs/research/470/atom-basis-obstruction.lisp`

**Interfaces:**
- Consumes: Task 2 run evidence.
- Produces: bounded classification for #470/#419.

- [ ] **Step 1: Add fresh-run provenance**

Include verification PR, Actions run, exact head SHA, runner, test count, failures, and diff-check status.

- [ ] **Step 2: Record the narrow conclusion**

If predictions hold, record:

```text
eq-zero + projection-success decomposition: route-falsified-as-total-classifier
reason: complementary partial domains + no admitted error recovery
```

Do **not** record global irreducibility.

- [ ] **Step 3: Record the surviving next hypotheses**

Explicitly leave open:
- a genuinely weaker total `pair?`/shape observer, if independently justified;
- a generic shape-case eliminator, to be classified as basis exchange unless weaker laws are shown;
- any future admitted error-as-data mechanism, which would change the lower basis and require a new experiment.

- [ ] **Step 4: Run exact-head PR CI**

Require the research PR's own CI to complete successfully on its final head before reporting the slice as verified.

- [ ] **Step 5: Feed the bounded result back to #470 and #419**

Do not edit the Canon demolition map until the evidence is reviewed there.
