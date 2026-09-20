; LIFE substrate-independence contract (#809).
;
; This is a Lisp-owned parity admission contract. It does not implement GraalVM
; or Rust execution. Both substrates are witnesses; neither owns expected truth.
;
; A parity row may become GREEN only when all required evidence is present:
; exact upstream pin, Lisp-owned expected datum, Rust observation, Graal
; observation, and substrate provenance. Missing Graal mechanism is an execution
; limitation, never a semantic mutation.

(life-substrate-parity/1
  ((owner . my-lisp)
   (life-contract-source . "contracts/life-1-contract.lisp")
   (expected-evidence-owner . lisp)
   (rust-role . witness)
   (graal-role . witness)
   (substrate-oracle . forbidden)
   (exact-upstream-pin . required)
   (same-life-contract-set . required)
   (contract-observables-only . required)
   (java-rust-internals-comparison . forbidden)
   (silent-graal-fallback . forbidden)
   (missing-substrate-mechanism . execution-limitation)
   (semantic-mutation-on-missing-mechanism . forbidden)
   (parity-admission . all-required-evidence))

  ; #93 has not yet supplied a real Graal differential execution witness.
  ; Keep this empty instead of manufacturing parity from Rust-only evidence.
  (rows
  ))
