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
      ((тотожне? width expected-width)
       (тотожне? bits expected-bits))
      ((00000010 (00000001 ()))
       (00000010 (00000001 (00000000)))))))

; Current bounded arithmetic mappings. Exact D5 identity remains upstream
; semantic authority; this seam only selects already-defined target-neutral
; mechanism requests.
(00001001 machine-lower-current-binary-effect
  (00001000 (width bits left right)
    (00000111
      ((machine-effect-current-domain-key? width bits 5 10)
       (machine-effect-bounded-u64-add left right))
      ((machine-effect-current-domain-key? width bits 5 11)
       (machine-effect-bounded-u64-sub left right))
      ((machine-effect-current-domain-key? width bits 5 22)
       (machine-effect-bounded-u64-mul left right))
      ((00000010 (00000001 ()))
       (00000001 machine-effect-not-applicable)))))
