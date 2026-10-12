; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The witness uses only exact Function8 language forms and explicit binary
; Number source. No machine/backend definition participates in the answer key.

(0011 machine-replaceability-add
  (01010 #b10 #b11))

(0011 machine-replaceability-eq-cond
  (110
    ((101 #b10 #b10)
     #b1101111)))

(0011 machine-replaceability-car-cons
  (100 (111 #b10 #b11)))

; Every assertion is a strict one-clause PredicateBit COND. If any assertion
; is NO, COND yields (), so the shell's exact pass-envelope check fails closed.
(0011 machine-replaceability-verdict
  (110
    ((101 machine-replaceability-add #b101)
     (110
       ((101 machine-replaceability-eq-cond #b1101111)
        (110
          ((101 machine-replaceability-car-cons #b10)
           (001 (machine-replaceability-witness (status pass))))))))))

machine-replaceability-verdict
