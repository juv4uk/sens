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


; #3809 — bounded compiler-role derivation from the owner-ratified D3 L1-L5
; law.  There is deliberately no D3 coordinate→role table here.
;
; Law inputs are exact authority anchors:
;   D2-OPEN  — the D2 prefix fibre selected by L2/L5 for the head selector;
;   D3-EMPTY — the L1 structural-empty root.
;
; Derivation:
;   head selector = D2-OPEN prefix + suffix-0        (L2 + L5)
;   tail selector = dual3(head selector)             (L3 + L4)
;   pair construct = dual3(D3-EMPTY)                 (L1 + L3 + L4)
;
; DECOMPOSE is the representation-only mechanism from #3808.  It exposes
; width/bits and contains no language meaning.

(визначити compiler-true
  (функція (seed)
    (атом? seed)))

(визначити compiler-false
  (функція (seed)
    (атом? (сполучити seed ()))))

(визначити compiler-bit-not
  (функція (seed bit)
    (за-умовою
      (bit (compiler-false seed))
      ((compiler-true seed) (compiler-true seed)))))

(визначити compiler-bits-equal
  (функція (seed left right)
    (за-умовою
      ((атом? left) (атом? right))
      ((атом? right) (compiler-false seed))
      ((тотожне? (перше left) (перше right))
       (compiler-bits-equal seed (решта left) (решта right)))
      ((compiler-true seed) (compiler-false seed)))))

(визначити compiler-dual-bits
  (функція (seed bits)
    (за-умовою
      ((атом? bits) ())
      ((compiler-true seed)
       (сполучити
         (compiler-bit-not seed (перше bits))
         (compiler-dual-bits seed (решта bits)))))))

(визначити compiler-append-bit
  (функція (seed bits bit)
    (за-умовою
      ((атом? bits) (сполучити bit ()))
      ((compiler-true seed)
       (сполучити
         (перше bits)
         (compiler-append-bit seed (решта bits) bit))))))

(визначити compiler-shape-width
  (функція (shape)
    (перше shape)))

(визначити compiler-shape-bits
  (функція (shape)
    (перше (решта shape))))

(визначити compiler-role-from-l1-l5-bits
  (функція (seed bits d2-open-bits d3-empty-bits)
    (за-умовою
      ((compiler-bits-equal
         seed
         bits
         (compiler-append-bit seed d2-open-bits (compiler-false seed)))
       (як-є selector-head))
      ((compiler-bits-equal
         seed
         bits
         (compiler-dual-bits
           seed
           (compiler-append-bit seed d2-open-bits (compiler-false seed))))
       (як-є selector-tail))
      ((compiler-bits-equal
         seed
         bits
         (compiler-dual-bits seed d3-empty-bits))
       (як-є pair-construct))
      ((compiler-true seed) ()))))

(визначити compiler-role-from-l1-l5-shapes
  (функція (seed shape d2-open-shape d3-empty-shape)
    (за-умовою
      ((тотожне?
         (compiler-shape-width shape)
         (compiler-shape-width d3-empty-shape))
       (compiler-role-from-l1-l5-bits
         seed
         (compiler-shape-bits shape)
         (compiler-shape-bits d2-open-shape)
         (compiler-shape-bits d3-empty-shape)))
      ((compiler-true seed) ()))))

(визначити compiler-role-from-l1-l5
  (функція (decompose identity d2-open d3-empty)
    (compiler-role-from-l1-l5-shapes
      identity
      (decompose identity)
      (decompose d2-open)
      (decompose d3-empty))))
