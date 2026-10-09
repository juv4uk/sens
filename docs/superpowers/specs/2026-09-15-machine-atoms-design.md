# #177 — Composable Lisp Machine Atoms Design

Date: 2026-09-15
Status: design only; implementation blocked on #176
Owner lane: ChatGPT
Depends on: #150 closed, #176 not yet landed

## Purpose

Issue #177 adds a Lisp-owned composition layer over admitted x86-64 machine forms. The layer must let Lisp construct machine instructions and blocks directly without promoting ISA mnemonics, registers, encodings, or CPU facts into public language semantics.

The authority graph remains:

```text
lib/surface/semantic-registry.lisp
        |
        | semantic -> machine projection only
        v
Lisp machine atoms / blocks
        |
        v
#176 admitted encoder contract
        |
        v
machine bytes
        |
        v
semantics-blind host
        |
        v
CPU
```

Reverse authority remains forbidden by `lib/machine/authority-boundary.lisp`.

## Current evidence this design must preserve

Current `main` already has:

- Lisp-owned structured lowering forms such as `(mov-r64-imm64 rax n)`, `(add-r64-r64 rax rcx)`, `(ret)`;
- a closed admission layer in `lib/machine/admission/x86-64.lisp`;
- a Lisp-owned encoder in `lib/machine/encoding/x86-64.lisp`;
- semantic lowering that produces structured forms first and only then requests admitted encoding;
- #150 machine non-interference guards preventing machine data from minting semantic IDs or peer surfaces.

The old `feat/lisp-assembler-atoms` branch is not replayed. Its retained design capital is only that machine construction should be Lisp-owned and host mechanism should remain semantics-blind. Its textual-assembler design is obsolete.

## Chosen architecture

### 1. Machine atoms are ordinary Lisp data constructors

#177 must not invent a second encoder table or a second ISA registry. A machine atom constructor creates only a canonical structured form accepted by the #176 contract.

Illustrative shape after #176 determines the canonical form schema:

```lisp
(x86-ret)
=> (ret)

(x86-mov-r64-imm64 'rax 42)
=> (mov-r64-imm64 rax 42)

(x86-vaddps 'ymm0 'ymm1 'ymm2)
=> canonical form defined by #176
```

The exact constructor names and exact returned list shape are not frozen by this design before #176 lands. The invariant is frozen: constructors produce #176-native machine forms, never textual assembly and never bytes.

### 2. One source of ISA truth

#176 owns the admitted encodable form contract. #177 consumes it.

#177 must not contain:

- opcode tables;
- REX/VEX/EVEX bit layouts;
- duplicate feature-gating tables;
- duplicate register-class legality tables when #176 already exposes that fact;
- mnemonic -> semantic-ID mappings;
- compiler semantic meaning.

If #177 needs a validation fact that #176 does not expose, that is treated as a missing #176 contract and resolved there rather than copied into the atom layer.

### 3. Machine blocks are compositional containers

A machine block is an ordered Lisp data object containing machine forms. It exists to compose atoms without immediately encoding them.

Minimum behavior:

```lisp
(machine-block
  (x86-mov-r64-imm64 'rax 2)
  (x86-mov-r64-imm64 'rcx 3)
  (x86-add-r64-r64 'rax 'rcx)
  (x86-ret))
```

must produce an inspectable ordered machine-form sequence. Encoding remains a separate projection.

The block layer must support deterministic append/concatenation so higher-level Lisp code can build control-flow and instruction sequences without string assembly.

### 4. Typed operands are machine-layer types, not language primitives

Register classes, immediates, memory operands and vector widths are machine-layer data contracts.

Representative operand categories expected after #176:

- GPR: r8/r16/r32/r64;
- XMM/YMM where admitted for the target profile;
- immediate widths and signedness where required by a form;
- memory operands with explicit base/index/scale/displacement shape;
- branch/relative targets represented structurally rather than precomputed textual labels.

These types live under `lib/machine/**`. They do not enter `lib/surface/semantic-registry.lisp` merely because Lisp can manipulate them.

### 5. Admission happens before byte materialization

The canonical data flow is:

```text
constructor
  -> structured machine form
  -> machine block
  -> CPU/profile + #176 form admission
  -> deterministic encoder
  -> bytes
```

Unsupported form/profile combinations fail before host execution. There is no "try to encode anyway" fallback.

## Proposed component boundaries

Final file names may adjust after #176 lands, but responsibilities are fixed:

### `lib/machine/atoms/x86-64.lisp`

Thin constructors for canonical #176 forms. No encoding facts.

### `lib/machine/block.lisp`

Architecture-neutral block composition helpers where practical: create, append, concatenate, inspect. It must not know x86 opcode semantics.

### Existing `lib/machine/admission/x86-64.lisp`

Remains the admission authority unless #176 replaces/refactors it. #177 calls the resulting #176-owned gate rather than duplicating it.

### Existing `lib/machine/encoding/x86-64.lisp`

Remains the byte projection authority. #177 never emits byte lists directly.

## Public-surface policy

Machine atoms are internal machine APIs.

Required invariants:

1. Adding `x86-vaddps`, `x86-aesenc`, `x86-popcnt`, register names, or operand records does not change semantic-registry digest.
2. No machine atom automatically appears as EN/UK/SA/SYM peer surface.
3. A future language-level feature may explicitly ratify a semantic operation that happens to lower to one of these forms, but that ratification must occur through the normal semantic-registry process and is outside #177.
4. Renaming a machine constructor cannot rename an existing semantic identity.

## Error model

#177 must fail closed and distinguish at least these classes at the machine-data level:

- malformed machine form;
- wrong operand class/width;
- unsupported form for active CPU profile;
- form known to XED/#176 evidence but intentionally not encodable yet;
- block contains an unadmitted form.

The atom layer should return the repository's existing machine-layer diagnostic shape rather than invent a new public `ErrorKind` unless #176 demonstrates that a new closed vocabulary entry is necessary.

## TDD plan

Implementation begins only after #176 lands.

### RED 1 — machine atoms do not exist yet

Write a focused witness that loads the machine atom library and expects representative constructors for scalar, branch, SSE/AVX, AES/PCLMUL, and BMI/bit-manipulation families.

The test must fail because the constructors/library are absent, not because of unrelated fixture setup.

### RED 2 — constructors must project to #176-native forms

For representative instructions, assert that constructor output is exactly the normalized form accepted by #176. No textual assembly and no bytes are accepted as GREEN.

### RED 3 — block composition is deterministic

Construct the same block through two composition paths and require structural equality and identical encoded output.

### RED 4 — unsupported profile form fails before execution

Use a form excluded by the i5-6400 profile or an explicitly unsupported #176 form. Assert fail-closed before `native-call-*` becomes reachable.

### RED 5 — non-interference

Add a machine-only atom and prove:

- semantic-registry digest is unchanged;
- public API semantic-ID set is unchanged;
- no peer surface is minted;
- #150 reverse-edge guard remains GREEN.

### RED 6 — encoder/decoder witness

Build a representative block with atom constructors, encode it through #176, and compare its decoded form against the pinned external evidence/oracle used by #176. The round-trip validates the machine layer without granting the decoder semantic authority.

## Minimum acceptance slice

#177 is not complete after only `ret`/`mov`/`add` constructors. Completion requires representative directly composable forms from the families named in the issue:

- scalar integer;
- branch/control-flow;
- SSE;
- AVX/AVX2;
- AES/PCLMUL;
- BMI/bit-manipulation.

For each representative family there must be:

1. Lisp constructor;
2. typed/validated canonical form;
3. profile admission witness;
4. deterministic encoding through #176;
5. independent decode/evidence witness where #176 supplies one.

## Non-goals

#177 does not:

- implement or complete #175 XED import;
- expand encoder coverage owned by #176;
- define language semantics for machine mnemonics;
- introduce a textual assembler as the canonical path;
- move opcode/ISA tables into the atom layer;
- implement optimizer policy;
- claim complete i5-6400 execution coverage beyond what #176 proves;
- implement #178 end-to-end completeness proof.

## Integration rule with #176

When #176 lands, implementation starts by reading its final normalized form schema, coverage report, exclusion diagnostics and profile gate. If the final #176 contract differs from current seed admission shapes, this design adapts constructor representation to #176 rather than preserving old forms for compatibility.

The seam is intentionally one-way:

```text
#177 constructors -> #176 contract
```

not:

```text
#176 encoder -> #177 private tables
```

## Completion claim allowed by #177

After all witnesses pass, the strongest valid claim is:

> my-lisp can compose representative admitted x86-64 instructions as Lisp-owned machine data and deterministically project those blocks through the #176-owned admission/encoding path without granting machine facts semantic authority.

It is not yet a claim of complete native compiler coverage. That stronger integration belongs to #178.
