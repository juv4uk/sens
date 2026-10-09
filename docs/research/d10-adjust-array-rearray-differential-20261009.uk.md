# D10 differential review: ADJUST-ARRAY vs historical *REARRAY

**State:** HOLD / source-backed differential witness. This PR does not edit the canonical D10 inventory, assign coordinates, ratify a resident, or authorize physical T5.

## Why examine this now?

The current D10 inventory already selects **MAKE-ARRAY** and **REARRAY**. A new Common Lisp name is not enough to justify another semantic identity. The useful question is whether ADJUST-ARRAY has an observable law not already expressed by those selected operations and the ratified D8 array basis.

The primary Common Lisp specification gives several testable laws:

- If the input array is actually adjustable, ADJUST-ARRAY must return the identical array object.
- If the result is a distinct array, the original input remains unchanged.
- An explicit fill pointer can be set to the adjusted vector size.
- A displaced result shares storage with its immediate backing array.
- If A is displaced to B and B is adjusted, A remains displaced to B; implementations may not flatten the chain and forget the intermediate object.

The historical MacLisp *REARRAY contract is narrower in different directions: it redefines dimensions while preserving old contents in row-major order, fills any new tail cells according to array type, cannot change the array type through multi-argument *REARRAY, and supports a one-argument operation that kills the old array pointer. That contract is already represented by selected D10 REARRAY and is not copied into this candidate.

## Current neighbors and decision

| Neighbor | Current authority | Differential question |
|---|---|---|
| MAKE-ARRAY | selected D10 research candidate | Can construction plus existing mutation preserve identity and aliases when changing shape? |
| REARRAY | selected D10 research candidate, backed by MacLisp 1975 | Does row-major preservation + typed tail initialization cover adjustable identity, optional fill-pointer and displacement-chain behavior? |
| COPY-ARRAY | ratified D8 | Copying cannot by itself establish the identity/alias law. |
| ARRAY-DISPLACEMENT | concurrently proposed in #4865 | This observes immediate base + offset; it does not itself adjust dimensions or preserve/update the intermediate chain. The two selection decisions stay separate. |

### Decision: HOLD, not selected yet

The witness below proves the Common Lisp standard's observable behavior on an independent Common Lisp runtime. It does not prove historical MacLisp execution parity, and it does not by itself prove that ADJUST-ARRAY is an irreducible D10 root. After the oracle passes, compare the exact laws against MAKE-ARRAY + REARRAY + COPY-ARRAY + existing array access/update and ARRAY-DISPLACEMENT. Promote only if a residual language-visible law survives that derivability attack.

## Reproduce

\`\`\`sh
sbcl --script tests/oracles/d10_adjust_array_rearray_oracle.lisp
python3 scripts/check_d10_adjust_array_rearray_differential.py --self-test
\`\`\`

The checker pins the ratified D1-D9 foundation and checks that current D10 still retains the declared neighbor meanings. It intentionally does not require the moving inventory to remain at its old 625-row snapshot while parallel D10 selections are serialized.

## Primary sources

- [ANSI Common Lisp HyperSpec: ADJUST-ARRAY](https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_adjust-array.html).
- [MacLisp Reference Manual, 17 December 1975](https://softwarepreservation.computerhistory.org/LISP/MIT/MACLISP_Reference_Manual-Dec_17_1975.pdf), §2-8, printed pp. 2-86–2-89 (*REARRAY).
- [The Pitmanual: MacLisp arrays](https://www.maclisp.info/pitmanual/array.html), secondary cross-check only.

Every D10 field remains unselected, coordinate=null, ratified=false, physical_t5_authorized=false. No old array coordinates or storage layouts are reused.
