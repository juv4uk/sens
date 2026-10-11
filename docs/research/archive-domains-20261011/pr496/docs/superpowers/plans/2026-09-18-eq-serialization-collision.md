# EQ Serialization Collision Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Falsify or support derivation of current EQ semantics through `write-to-string` plus text equality.

**Architecture:** Persist only research/plan artifacts. Execute live evaluator probes in a verification-only child with a temporary integration test removed before diff hygiene. One serialization collision is sufficient to falsify this route, but not EQ irreducibility.

**Tech Stack:** my-lisp evaluator, `eq`, `write-to-string`, string ordering/control dispatch, GitHub Actions.

**Spec:** GitHub issue #493.

## Global Constraints

- No production EQ/writer/string/evaluator/Canon/registry/fixture/Rust changes.
- Current EQ compares closures by identity: same closure reused = same, separately created closures = distinct.
- Current writer renders closures as `<lambda>`.
- The text route must not call EQ directly or indirectly.
- Result remains bounded to this route.

---

### Task 1: Record the collision prediction before execution

**Files:**
- Create: `docs/research/493/eq-serialization-collision.lisp`

- [ ] Record current EQ and writer capability assumptions.
- [ ] Predict:
  - one closure bound once compared with itself -> EQ same;
  - two separately created closures -> EQ distinct;
  - both separately created closures -> `write-to-string` yields identical `"<lambda>"`;
  - therefore any equality relation computed only from serialized text must false-positive same.
- [ ] Pre-classify as `insufficient-evidence`.

### Task 2: Execute a no-EQ text equality route in a NEVER-MERGE child

**Files:**
- Child only: `.github/workflows/verify-493-eq-serialization.yml`
- Runner temporary only: `crates/my-lisp/tests/verify_493_eq_serialization.rs`

- [ ] Verify current closure EQ same/distinct behavior.
- [ ] Verify the closure serialization collision.
- [ ] Define a research expression `text-same?` without EQ:
  - serialize both values;
  - use `string<?` in both directions;
  - canonical COND compares each result to `()`;
  - if neither text is less than the other, classify serialized texts as same.
- [ ] Show that two distinct closures are classified text-same.
- [ ] Include a control pair of distinct ordinary symbols whose serialized texts differ.
- [ ] Remove the temporary test and run `git diff --check`.
- [ ] Close the child PR without merge.

### Task 3: Record and verify the bounded result

**Files:**
- Modify: `docs/research/493/eq-serialization-collision.lisp`

- [ ] Record exact PR/run/SHA and test counts.
- [ ] If the collision holds, classify `serialization/text -> EQ` as `route-falsified-by-serialization-collision`.
- [ ] Explicitly state that writer text is presentation/serialization data and loses closure identity.
- [ ] Run exact-head CI + bilingual gate on the research PR.
- [ ] Feed the bounded result to #493/#471/#419 only.
