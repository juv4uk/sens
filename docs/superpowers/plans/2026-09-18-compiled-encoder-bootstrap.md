# Compiled Lisp-Owned Encoder Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove evaluator dependence from x86-64 byte generation by compiling the Lisp-owned encoder while preserving byte-for-byte parity and Lisp semantic authority.

**Architecture:** Treat `lib/machine/encoding/x86-64.lisp` as upstream source authority. First run the exact file through CML's broader existing `cml x86-elf` freestanding compiler path to discover the first real blocker. The dedicated `cml-compile x86-elf` process bridge is intentionally arithmetic-slice-only and is not the encoder bootstrap path. CML may add compiler mechanism, but must not copy encoder truth into Rust/CML tables. The final path must compare interpreted encoder bytes A with compiled encoder bytes B and execute both through the same admitted host mechanism.

**Tech Stack:** my-lisp, CML pinned at an exact commit, x86-64 Lisp encoder, GitHub Actions, existing native execution host mechanism.

**Spec:** GitHub issue #507 and `docs/superpowers/specs/2026-09-18-native-first-execution-design.md`.

## Global Constraints

- `lib/machine/encoding/x86-64.lisp` remains the encoder source of truth.
- CML owns compilation/lowering mechanism only.
- No duplicate normative opcode/encoding table may be introduced in CML.
- No Rust semantic matcher or Rust encoder replacement.
- Host code may allocate/call executable memory but must not decide Lisp meaning.
- Pin exact my-lisp and CML commits in every cross-repo witness.
- Fail closed on unsupported CML constructs; never silently fall back and call that “compiled”.
- #509 parity and #508 coverage ledger remain separate ownership lanes.

---

### Task 1: Whole-file CML RED

**Files:**
- Verification child only: `.github/workflows/verify-507-encoder-cml-red.yml`

- [ ] Check out my-lisp at the #507 branch.
- [ ] Check out CML at pinned master `d12db3370180c4d155e21a61ab788d63e02010e9`.
- [ ] Run the real command:
  `cd <pinned-cml> && cargo run --bin cml -- x86-elf <absolute-my-lisp>/lib/machine/encoding/x86-64.lisp /tmp/my-lisp-encoder`.
- [ ] Require non-zero exit.
- [ ] Capture the first compiler diagnostic verbatim.
- [ ] Classify the blocker: source admission, IR lowering, freestanding backend admission, linking/runtime ABI, callable/export ABI, or result representation.
- [ ] Create a CML issue for exactly that blocker, not a generic “compile encoder” request.

### Task 2: Minimal CML capability for the first blocker

**Repository:** `juv4uk/cml`

- [ ] RED test reproduces the blocker using the smallest encoder-derived source slice that preserves the same unsupported construct.
- [ ] Implement only the compiler mechanism needed for that slice.
- [ ] Verify no copied encoder byte/opcode expected table appears in CML.
- [ ] Re-run the whole upstream encoder file and record the next blocker.
- [ ] Repeat blocker-by-blocker; each independently reviewable change gets its own CML PR if it touches a distinct compiler concern.

### Task 3: Callable compiled-encoder witness

A standalone ELF that merely “compiles” is insufficient. The compiled artifact must expose a usable encoder operation.

- [ ] Define a versioned callable boundary for one encoder function first, beginning with `x86-encode-ret` or `x86-encode-mov-r64-imm64`.
- [ ] Invoke interpreted Lisp encoder -> bytes A.
- [ ] Invoke compiled encoder artifact with the same logical operands -> bytes B.
- [ ] Require `A == B` byte-for-byte.
- [ ] Submit A and B independently through existing closed admission/native execution and require the same physical result.
- [ ] Expand callable surface only after the first operation is proven.

### Task 4: Native-first integration

- [ ] Allow native-first execution to consume compiled encoder output without changing classifier semantics.
- [ ] Keep interpreted encoder as reference/fallback until compiled coverage is complete.
- [ ] Add provenance showing `encoder-route compiled|interpreted` in test diagnostics only.
- [ ] Never hide compiled-encoder failure by silently using interpreted output in a test claiming compiled success.

### Task 5: Integration gates

- [ ] Exact-head CML CI.
- [ ] Exact-head my-lisp CI + bilingual docs.
- [ ] Byte parity witness.
- [ ] Physical CPU parity witness.
- [ ] Update #507/#504 with exact supported surface and remaining blockers.
