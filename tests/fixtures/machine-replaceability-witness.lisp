; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The witness uses only exact Function8 language forms and explicit binary
; Number source. No machine/backend definition participates in the answer key.

(00001001 machine-replaceability-add
  (00001100 #b10 #b11))

(00001001 machine-replaceability-eq-cond
  (00000111
    ((00000011 #b10 #b10)
     #b1101111)))

(00001001 machine-replaceability-car-cons
  (00000101 (00000100 #b10 #b11)))

; Every assertion is a strict one-clause PredicateBit COND. If any assertion
; is NO, COND yields (), so the shell's exact pass-envelope check fails closed.
(00001001 machine-replaceability-verdict
  (00000111
    ((00000011 machine-replaceability-add #b101)
     (00000111
       ((00000011 machine-replaceability-eq-cond #b1101111)
        (00000111
          ((00000011 machine-replaceability-car-cons #b10)
           (00000001 (machine-replaceability-witness (status pass))))))))))

machine-replaceability-verdict
