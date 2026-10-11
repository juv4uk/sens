; lib/compiler-nucleus.lisp
; sens#3759 / #3803 — first executable compiler nucleus slice owned by SENS.
;
; N0 is deliberately smaller than the final self-hosted compiler:
; - exact DomainIdentity is already a first-class runtime value;
; - authority rows are supplied as data by the bootstrap boundary;
; - this program performs the authority lookup/normalization itself;
; - it contains no D3 coordinate table, no Sid8/Sens8 identity, and no backend
;   opcode/mechanism table.
;
; Authority row shape for this bounded slice:
;
;   (exact-domain-identity execution-role proof-ref provenance)
;
; The role/proof/provenance payload is opaque here.  #3806 moves construction
; of that authority projection from the Rust/bootstrap oracle into executable
; SENS-owned law.  Until then this file is a real compiler component, but only
; a PARTIAL nucleus and not a self-host/fixed-point claim.
;
; Ukrainian spellings below are source/UI projections only.  They are chosen
; because the current registry routes Ukrainian D3/D4 surfaces directly to
; exact-domain identities.  The focused guard lowers this file before execution
; and rejects any historical Sid/Call node.

(визначити compiler-authority-find
  (функція (identity rows)
    (за-умовою
      ((атом? rows) ())
      ((тотожне? identity (перше (перше rows))) (перше rows))
      ((атом? ()) (compiler-authority-find identity (решта rows))))))

(визначити compiler-nucleus
  (функція (identity authority)
    (compiler-authority-find identity authority)))


; Representation-only bootstrap seam for #3808.
; DECOMPOSE is an explicitly supplied first-class mechanism.  The language
; chooses when to invoke it; the host function may reveal only exact width/bits
; and has no identity->meaning authority.
(визначити compiler-domain-shape
  (функція (decompose identity)
    (decompose identity)))


; #3809 — bounded compiler-role derivation from generated, provenance-bound
; D3 L1-L5 structural law data.  There is deliberately no D3 coordinate→role
; table here.
;
; LAW is transported from knowledge/bija3-l1-l5-structure-projection.json:
;   (domain-width l1-empty-bits l4-xor-mask l5-spine)
;
; The projection itself is mechanically generated from owner-ratified #3202.
; It carries no compiler role names.  SENS assigns the bounded compiler roles
; by executing the ratified structural relationships:
;   head selector = third ordered L5 spine member
;   tail selector = L4 dual(head selector)
;   pair construct = L4 dual(L1 empty)
;
; DECOMPOSE is the representation-only mechanism from #3808.

(визначити compiler-true
  (функція (seed)
    (атом? seed)))

(визначити compiler-false
  (функція (seed)
    (атом? (сполучити seed ()))))

(визначити compiler-bits-equal
  (функція (seed left right)
    (за-умовою
      ((атом? left) (атом? right))
      ((атом? right) (compiler-false seed))
      ((тотожне? (перше left) (перше right))
       (compiler-bits-equal seed (решта left) (решта right)))
      ((compiler-true seed) (compiler-false seed)))))

(визначити compiler-bit-xor
  (функція (seed left right)
    (за-умовою
      ((тотожне? left right) (compiler-false seed))
      ((compiler-true seed) (compiler-true seed)))))

(визначити compiler-xor-bits
  (функція (seed left right)
    (за-умовою
      ((атом? left)
       (за-умовою
         ((атом? right) ())
         ((compiler-true seed) ())))
      ((атом? right) ())
      ((compiler-true seed)
       (сполучити
         (compiler-bit-xor seed (перше left) (перше right))
         (compiler-xor-bits seed (решта left) (решта right)))))))

(визначити compiler-shape-width
  (функція (shape)
    (перше shape)))

(визначити compiler-shape-bits
  (функція (shape)
    (перше (решта shape))))

(визначити compiler-law-width
  (функція (law)
    (перше law)))

(визначити compiler-law-empty-bits
  (функція (law)
    (перше (решта law))))

(визначити compiler-law-xor-mask
  (функція (law)
    (перше (решта (решта law)))))

(визначити compiler-law-l5-spine
  (функція (law)
    (перше (решта (решта (решта law))))))

(визначити compiler-law-l5-head-bits
  (функція (law)
    (перше (решта (решта (compiler-law-l5-spine law))))))

(визначити compiler-role-from-l1-l5-bits
  (функція (seed bits law)
    (за-умовою
      ((compiler-bits-equal
         seed
         bits
         (compiler-law-l5-head-bits law))
       (як-є selector-head))
      ((compiler-bits-equal
         seed
         bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (як-є selector-tail))
      ((compiler-bits-equal
         seed
         bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (як-є pair-construct))
      ((compiler-true seed) ()))))

(визначити compiler-role-from-l1-l5
  (функція (decompose identity law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-law-width law))
       (compiler-role-from-l1-l5-bits
         identity
         (compiler-shape-bits (decompose identity))
         law))
      ((compiler-true identity) ()))))
