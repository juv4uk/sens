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

(0011 machine-effect-current-domain-key?
  (0010 (width bits expected-width expected-bits)
    (110
      ((тотожне? width expected-width)
       (тотожне? bits expected-bits))
      (#d1:1
       #d1:0))))

; Current bounded arithmetic mappings. Exact D5 identity remains upstream
; semantic authority; this seam only selects already-defined target-neutral
; mechanism requests.
(0011 machine-lower-current-binary-effect
  (0010 (width bits left right)
    (110
      ((machine-effect-current-domain-key? width bits 5 10)
       (machine-effect-bounded-u64-add left right))
      ((machine-effect-current-domain-key? width bits 5 11)
       (machine-effect-bounded-u64-sub left right))
      ((machine-effect-current-domain-key? width bits 5 22)
       (machine-effect-bounded-u64-mul left right))
      (#d1:1
       (001 machine-effect-not-applicable)))))
