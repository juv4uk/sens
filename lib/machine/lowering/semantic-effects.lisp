; #4365 — one current semantic DomainIdentity -> target-neutral effect seam.
;
; This module owns only the direction:
;   exact current (domain-width, packed-bits)
;        -> canonical target-neutral machine-effect kind / effect request
;
; It contains no target, ISA, register, encoding, feature, layout, or host fact.
; Coordinates are mechanically guarded against knowledge/d1-d9-foundation.json
; by crates/sens/tests/machine_semantic_effect_lowering.rs.
;
; Generic effect-definition modules must not copy this router.

(00001001 machine-effect-current-domain-key?
  (00001000 (width bits expected-width expected-bits)
    (00000111
      ((00100010 width expected-width)
       (00100010 bits expected-bits))
      (t (00000001 ())))))

; Classify already-proved current D5 arithmetic residents into canonical
; target-neutral effect kinds. This function does not construct target forms.
(00001001 machine-effect-kind-for-current-binary-u64
  (00001000 (width bits)
    (00000111
      ((machine-effect-current-domain-key? width bits 5 10)
       (00000001 bounded-u64-add))
      ((machine-effect-current-domain-key? width bits 5 11)
       (00000001 bounded-u64-sub))
      ((machine-effect-current-domain-key? width bits 5 22)
       (00000001 bounded-u64-mul))
      (t
       (00000001 machine-effect-not-applicable)))))

; Main-safe first executable consumer. PLUS already has a merged canonical
; bounded-u64-add constructor. DIFFERENCE/TIMES kinds are reserved by the seam
; for #4358/#4361, whose effect constructors remain independently owned there.
(00001001 machine-effect-lower-current-binary-u64
  (00001000 (width bits left right)
    (10011100
      ((kind (machine-effect-kind-for-current-binary-u64 width bits)))
      (00000111
        ((00000011 kind (00000001 bounded-u64-add))
         (machine-effect-bounded-u64-add left right))
        (t
         (00000001 machine-effect-not-applicable))))))
