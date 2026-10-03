# #2590 — Non-local exit factor, RETURN/PROG parenthood, and width pressure gate

Status: STRUCTURAL-DISCOVERY, research-only.
Parent: #2583, #2593
Width gate: #2573, #2584
Placement law: #2236
Domain firewall: #2508
Coordination: #1599

## Summary

This research establishes the structural factorization and honest parenthood analysis for the post-D4 `non-local-exit` factor (F2 in #2583/#2593).

```text
Factor status: BOUNDED-INDEPENDENT
Remove-one reconstruction from D1-D4: FAILS
Source capability vs CPS compilability: INDEPENDENT at source / direct evaluator level
PROG classification: COMPOSITE (binder + sequence + intra-frame jump + exit delimiter)
Strongest honest parent: NO-PARENT (all proposed D1-D4 candidates change base operation)
Orthogonality vs shared-location-update (#2589): PROVEN (4 distinct states in 2x2 grid)
Binary coordinate: UNPLACED (residents=0, coordinates=0, roots=0)
```

## 1. Remove-One Reconstruction Attack

Under admitted D1-D4 semantics (EVAL, APPLY, LAMBDA, COND, local tail recursion):
- Every function activation frame returns strictly to its immediate caller.
- In a nested call stack `PROG(P0) -> middle -> inner`:
  - With `non-local-exit` removed, `inner` can only return normally to `middle`.
  - `middle`'s post-call continuation executes inevitably unless `middle` is modified to thread a sentinel or continuation.
  - With `non-local-exit` present, `(RETURN val)` unwinds frames directly to the delimiter `P0`, skipping `middle`'s continuation completely without modifying `middle`.
- Conclusion: `non-local-exit` cannot be reconstructed from admitted D1-D4 local control. The factor status is `BOUNDED-INDEPENDENT`.

## 2. Source Capability vs Whole-Program CPS Compilability

While whole-program Continuation Passing Style (CPS) can compile non-local exits into tail calls, this compilation requires a global transformation:
- Every function in the program must change its signature from direct return (`T`) to explicit continuation passing (`(T -> !) -> !`).
- At the level of the source language evaluator and runtime machine, the capability to unwind dynamic frames without whole-program rewriting is an irreducible primitive capability.

## 3. Classification of PROG as COMPOSITE

Historical Lisp `PROG` decomposes cleanly into four orthogonal sub-capabilities:
1. **Local binding**: allocation of local lexical/dynamic frame (equivalent to `LET`/`LAMBDA`);
2. **Sequential execution**: ordered statement evaluation (equivalent to `PROGN`);
3. **Intra-frame branching**: jumping to tags within the same activation frame (equivalent to `GO`);
4. **Dynamic exit delimiter**: establishing the dynamic extent target for `RETURN`.

Because `PROG` is an ad-hoc composition of these sub-capabilities, it must NOT be allocated an atomic resident in the binary map. Its classification is `COMPOSITE`.

## 4. Honest Parenthood Attack on RETURN

Placement law #2236 mandates that a parent candidate must share the **same base semantic operation**, differing only along observable control axes:
- **APPLY**: base operation is callable application (`callable + args + env -> result`), stack effect pushes frame. Base mismatch.
- **EVAL**: base operation is form evaluation (`form + env -> result`), stack effect evaluates locally. Base mismatch.
- **LAMBDA**: base operation is closure construction (`params + body + env -> closure`). Base mismatch.
- **COND**: base operation is local branch selection within the current frame. Base mismatch.
- **GO**: base operation is intra-frame instruction pointer jump without return value. Base mismatch.

All proposed candidates change the base semantic operation. Therefore, the strongest honest parent for `RETURN` under D1-D4 is **`NO-PARENT`** (or `UNKNOWN` under broader search).

## 5. Cross-Family Orthogonality Control (#2589 vs #2590)

Testing `shared-location-update` (F1) against `non-local-exit` (F2) across a 2x2 matrix:
- **Neither**: normal local return, store remains `OLD`.
- **Mutation only**: store changes `OLD -> NEW`, control returns normally through intermediate frames.
- **Exit only**: store remains `OLD`, control escapes non-locally skipping intermediate frames.
- **Both**: store changes `OLD -> NEW`, control escapes non-locally.

All 4 states produce distinct observable signatures. Neither factor collapses or implies the other. They are strictly orthogonal.

## 6. Width Consequence & Non-Conclusions

- **Binary Object**: `UNPLACED`
- **Proven Independent Roots**: 0
- **New D5 Residents**: 0
- **Coordinates Allocated**: 0
- **Width Inference**: NONE
- Factor independence does NOT grant a binary coordinate or bit suffix.
- UNKNOWN / NO-PARENT does not constitute an unplaced residue or authorize map mutation.
- Production control semantics and binary maps remain unmutated.
