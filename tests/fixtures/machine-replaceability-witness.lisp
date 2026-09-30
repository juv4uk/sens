; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The witness executes only exact Function8 language forms. Removing a backend
; may remove execution capability, never the meaning of these already-ratified
; forms.

(00001001 machine-replaceability-witness
  (00001000 ()
    (00000111
      ((00000011 (00001100 2 3) 5)
       (00000111
         ((00000011
            (00000111
              ((00000011 2 2)
               111)
              ((00000010 (00000001 ()))
               222))
            111)
          (00000111
            ((00000011 (00000101 (00000100 2 3)) 2)
             (00000001 (machine-replaceability-witness (status pass))))
            ((00000010 (00000001 ()))
             (00100111
               (00000001 machine-replaceability-witness)
               (00000001 (status fail))
               (00100111 (00000001 case) (00000001 car-cons))
               (00100111 (00000001 expected) 2)
               (00100111
                 (00000001 actual)
                 (00000101 (00000100 2 3)))))))
         ((00000010 (00000001 ()))
          (00100111
            (00000001 machine-replaceability-witness)
            (00000001 (status fail))
            (00100111 (00000001 case) (00000001 eq-cond))
            (00100111 (00000001 expected) 111)
            (00100111
              (00000001 actual)
              (00000111
                ((00000011 2 2)
                 111)
                ((00000010 (00000001 ()))
                 222)))))))
      ((00000010 (00000001 ()))
       (00100111
         (00000001 machine-replaceability-witness)
         (00000001 (status fail))
         (00100111 (00000001 case) (00000001 add))
         (00100111 (00000001 expected) 5)
         (00100111 (00000001 actual) (00001100 2 3)))))))

(machine-replaceability-witness)
