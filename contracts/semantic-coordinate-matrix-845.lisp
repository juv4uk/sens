; #845 — read-only semantic coordinate matrix v2.
;
; Composition view only: this file owns no semantic meaning, allocates no SID,
; and copies no math/kernel/machine axis payload.
;
; The observer derives coordinates from the listed live sources. Missing axis
; evidence is legal and must remain explicit rather than being guessed.

(semantic-coordinate-matrix/2
  (identity-source . "lib/surface/semantic-registry.lisp")
  (math-axis-source . "tests/fixtures/semantic-coordinate-law-axis-v1.lisp")
  (kernel-axis-source . "contracts/sid-kernel-witness-735.lisp")
  (machine-axis-source . "lib/machine/capability-axis.lisp")
  (missing-axis-policy . explicit)
  (scope
    00001100 ; +
    00000011 ; eq
    00000100 ; cons
    00000101 ; car
    00000111)) ; cond
