; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The witness executes only exact Function8 language forms and explicit binary
; Number source. Removing a backend may remove execution capability, never the
; meaning of these already-ratified forms.

(00001001 machine-replaceability-witness
  (00001000 ()
    (00000111
      ((00000011 (00001100 #b10 #b11) #b101)
       (00000111
         ((00000011
            (00000111
              ((00000011 #b10 #b10)
               #b1101111)
              ((00000010 (00000001 ()))
               #b11011110))
            #b1101111)
          (00000111
            ((00000011 (00000101 (00000100 #b10 #b11)) #b10)
             (00000001 (machine-replaceability-witness (status pass))))
            ((00000010 (00000001 ()))
             (00100111
               (00000001 machine-replaceability-witness)
               (00000001 (status fail))
               (00100111 (00000001 case) (00000001 car-cons))
               (00100111 (00000001 expected) #b10)
               (00100111
                 (00000001 actual)
                 (00000101 (00000100 #b10 #b11)))))))
         ((00000010 (00000001 ()))
          (00100111
            (00000001 machine-replaceability-witness)
            (00000001 (status fail))
            (00100111 (00000001 case) (00000001 eq-cond))
            (00100111 (00000001 expected) #b1101111)
            (00100111
              (00000001 actual)
              (00000111
                ((00000011 #b10 #b10)
                 #b1101111)
                ((00000010 (00000001 ()))
                 #b11011110)))))))
      ((00000010 (00000001 ()))
       (00100111
         (00000001 machine-replaceability-witness)
         (00000001 (status fail))
         (00100111 (00000001 case) (00000001 add))
         (00100111 (00000001 expected) #b101)
         (00100111 (00000001 actual) (00001100 #b10 #b11)))))))

(machine-replaceability-witness)
