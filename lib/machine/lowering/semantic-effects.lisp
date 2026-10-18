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

(визначити machine-effect-current-domain-key?
  (функція (width bits expected-width expected-bits)
    (за-умовою
      ((тотожне? width expected-width)
       (тотожне? bits expected-bits))
      (так
       ні))))

; Current bounded arithmetic mappings. Exact D5 identity remains upstream
; semantic authority; this seam only selects already-defined target-neutral
; mechanism requests.
(визначити machine-lower-current-binary-effect
  (функція (width bits left right)
    (за-умовою
      ((machine-effect-current-domain-key? width bits 5 10)
       (machine-effect-bounded-u64-add left right))
      ((machine-effect-current-domain-key? width bits 5 11)
       (machine-effect-bounded-u64-sub left right))
      ((machine-effect-current-domain-key? width bits 5 22)
       (machine-effect-bounded-u64-mul left right))
      (так
       (як-є machine-effect-not-applicable)))))
