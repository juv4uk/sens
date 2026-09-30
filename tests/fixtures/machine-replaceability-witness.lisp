; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The expected language answers are computed here using exact Function8 forms
; and explicit binary Number source. Removing a backend may remove execution
; capability, never the meaning of these already-ratified forms.

(00001001 machine-replaceability-add
  (00001100 #b10 #b11))

(00001001 machine-replaceability-eq-cond
  (00000111
    ((00000011 #b10 #b10)
     #b1101111)
    ((00000010 (00000001 ()))
     #b11011110)))

(00001001 machine-replaceability-car-cons
  (00000101 (00000100 #b10 #b11)))

(00001001 machine-replaceability-witness
  (00001000 ()
    (00000111
      ((00100010 machine-replaceability-add #b101)
       (00000111
         ((00100010 machine-replaceability-eq-cond #b1101111)
          (00000111
            ((00100010 machine-replaceability-car-cons #b10)
             (00000001 (machine-replaceability-witness (status pass))))
            ((00000010 (00000001 ()))
             (00100111
               (00000001 machine-replaceability-witness)
               (00000001 (status fail))
               (00100111 (00000001 case) (00000001 car-cons))
               (00100111 (00000001 expected) #b10)
               (00100111
                 (00000001 actual)
                 machine-replaceability-car-cons)))))
         ((00000010 (00000001 ()))
          (00100111
            (00000001 machine-replaceability-witness)
            (00000001 (status fail))
            (00100111 (00000001 case) (00000001 eq-cond))
            (00100111 (00000001 expected) #b1101111)
            (00100111
              (00000001 actual)
              machine-replaceability-eq-cond)))))
      ((00000010 (00000001 ()))
       (00100111
         (00000001 machine-replaceability-witness)
         (00000001 (status fail))
         (00100111 (00000001 case) (00000001 add))
         (00100111 (00000001 expected) #b101)
         (00100111 (00000001 actual) machine-replaceability-add))))))

(machine-replaceability-witness)
