# План структурного мінімального профілю MACHINE-MIN-SUBSET-1

Цей план фіксує перший обмежений доказ для #196: не будувати другу таблицю opcode-ів, а вивести мінімально потрібні машинні родини з уже наявного структурного Lisp-witness `CAR(CONS 2 3)`. Профіль має пояснювати причину кожної залежності й залишати encoding/admission єдиним чинним машинним авторитетом.

# MACHINE-MIN-SUBSET-1 Structural Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first executable #196 minimal-runtime projection for the already-ratified bounded `CAR(CONS 2 3)` native witness without creating a second ISA/opcode table.

**Architecture:** The profile derives its observed machine families from the existing semantic lowerer, then attaches a small machine-effect dependency trace explaining why those observed families are required. The exact witness must still pass closed admission/Lisp-owned encoding and round-trip through the independent test decoder. The profile does not own opcodes, register encodings, semantic IDs, device policy, or a new calling convention.

**Tech Stack:** my-lisp, Lisp-owned x86-64 machine layer, Rust mechanism/observer tests.

**Spec:** GitHub issue #196 (`MACHINE-MIN-SUBSET-1`).

## Global Constraints

- Do not modify encoder or admission families for this slice.
- Do not create semantic IDs from ISA instruction names.
- Do not duplicate the i5-6400 inventory or opcode truth.
- The profile must be a projection over current semantic lowering + current admitted machine authority.
- The first witness is bounded structural `CAR(CONS 2 3)` only; no full allocator/GC/self-host claim.
- Existing broad #176/#178 coverage remains independent.

---

### Task 1: Executable lower-bound profile

**Files:**
- Create: `lib/machine/profile/minimal-runtime-x86-64.lisp`
- Create/Test: `crates/my-lisp/tests/machine_minimal_profile.rs`
- Modify: `tests/authority-inventory.lisp`
- Modify: `tests/authority-inventory.tsv`

**Interfaces:**
- Consumes: `x86-lower-cons-car-u64-forms`, current admission/encoder, #177 typed atom constructors.
- Produces: `x86-minimal-structural-car-forms`, `x86-minimal-structural-car-observed-families`, `x86-minimal-structural-car-dependencies`.

- [ ] **Step 1: Write a failing observer test** that requires a machine-readable profile derived from the existing bounded CAR lowering and checks that the observed family set is exactly `mov-r64-imm64`, `mov-mem-disp8-r64`, `mov-r64-mem-disp8`, `ret`.
- [ ] **Step 2: Run the focused test in CI and verify RED** because the profile file does not yet exist.
- [ ] **Step 3: Implement the minimal profile** as Lisp data/functions that derive the family set from `x86-lower-cons-car-u64-forms`; keep only effect/reason/classification metadata hand-authored.
- [ ] **Step 4: Prove typed-atom coverage** by checking representative #177 atom constructors project to the same canonical forms used by the witness.
- [ ] **Step 5: Prove admission/encoding** by passing the exact derived witness forms through `x86-encode-admitted-program-or-reject` and asserting a byte list, not rejection.
- [ ] **Step 6: Commit GREEN candidate** after the focused test passes.

### Task 2: Independent structural round-trip

**Files:**
- Modify: `crates/my-lisp/tests/support/x86_64_block_decoder.rs`
- Modify/Test: `crates/my-lisp/tests/machine_minimal_profile.rs`

**Interfaces:**
- Consumes: exact byte stream produced from the profile's derived witness.
- Produces: independent reconstruction of the complete structured machine-form list.

- [ ] **Step 1: Add RED assertion** that the independent decoder reconstructs the complete bounded CAR witness.
- [ ] **Step 2: Extend only the test observer decoder** with MOV r64,[base+disp8] and MOV [base+disp8],r64 decoding sufficient for current admitted forms; do not call the Lisp encoder from decoder logic.
- [ ] **Step 3: Verify exact form-by-form round-trip**, including pair head/tail offsets and final RET.
- [ ] **Step 4: Run focused and regression CI**, including authority guards, machine non-interference, machine block round-trip, minimal profile test, and native Vertical Day witness where selected by CI.

### Task 3: Ratify only the proven claim

**Files:**
- Update: PR description / #196 progress comment only.

**Interfaces:**
- Consumes: GREEN evidence from Tasks 1–2.
- Produces: a bounded claim that four current form families are sufficient for the existing structural CAR witness, not for a complete Lisp runtime.

- [ ] **Step 1: Record the exact dependency trace** `materialize-value -> mov-r64-imm64`, `store-pair-field -> mov-mem-disp8-r64`, `load-pair-field -> mov-r64-mem-disp8`, `return-result -> ret`.
- [ ] **Step 2: Record explicit () for the next growth witness** rather than adding instructions for completeness; conditional control remains a future necessity proof.
- [ ] **Step 3: Keep #196 open** because one structural lower bound is not yet a complete self-host/runtime minimum.
