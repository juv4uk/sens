; #4365 — one current semantic DomainIdentity -> target-neutral effect seam.
;
; This module owns only the direction:
;   exact current (domain-width, packed-bits)
;        -> canonical target-neutral machine-effect request
;
; It contains no target, ISA, register, encoding, feature, layout, or host fact.
; The current coordinate is mechanically guarded against
; knowledge/d1-d9-foundation.json by the focused Rust witness.
;
; Generic effect-definition modules must not copy this router.

(00001001 machine-effect-current-domain-key?
  (00001000 (width bits expected-width expected-bits)
    (00000111
      ((00100010 width expected-width)
       (00100010 bits expected-bits))
      (t (00000001 ())))))

; First executable mapping only: the current D5 PLUS identity selects the
; already-merged bounded-u64-add mechanism. DIFFERENCE/TIMES remain
; not-applicable until their constructors are independently merged under #4358.
(00001001 machine-lower-current-binary-effect
  (00001000 (width bits left right)
    (00000111
      ((machine-effect-current-domain-key? width bits 5 10)
       (machine-effect-bounded-u64-add left right))
      (t
       (00000001 machine-effect-not-applicable)))))
