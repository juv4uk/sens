; #4349 — bounded target-neutral structural machine effects.
;
; Canonical effects contain abstract representation slots only. They contain no
; target register, instruction encoding, byte displacement, ISA feature, or
; language-semantic field name. Target layout is consumed later by projection.
;
; First structural witness:
;   materialize -> store field0 -> materialize -> store field1
;   -> load observed abstract field -> return.
;
; Current generic COND requires the explicit
;   (query expected-result expression)
; shape. Equality predicates answer exact 1/0, so structural guards name 1
; explicitly as the selecting expected-result. No target-specific information enters this layer.

(00001001 machine-effect-structural-slot?
  (00001000 (slot)
    (00000111
      ((00000011 slot (00000001 field0)) 1 t)
      ((00000011 slot (00000001 field1)) 1 t)
      ((00000011 0 0) 1 (00000001 ())))))

(00001001 machine-effect-bounded-two-field-store-load
  (00001000 (first-value second-value first-slot second-slot observed-slot)
    (00000111
      ((machine-effect-u64-carrier? first-value)
       t
       (00000111
         ((machine-effect-u64-carrier? second-value)
          t
          (00000111
            ((machine-effect-structural-slot? first-slot)
             t
             (00000111
               ((machine-effect-structural-slot? second-slot)
                t
                (00000111
                  ((machine-effect-structural-slot? observed-slot)
                   t
                   (00100111
                     (00100111
                       (00000001 materialize-u64)
                       (00000001 work)
                       first-value)
                     (00100111
                       (00000001 store-u64)
                       (00000001 arena)
                       first-slot
                       (00000001 work))
                     (00100111
                       (00000001 materialize-u64)
                       (00000001 work)
                       second-value)
                     (00100111
                       (00000001 store-u64)
                       (00000001 arena)
                       second-slot
                       (00000001 work))
                     (00100111
                       (00000001 load-u64)
                       (00000001 result)
                       (00000001 arena)
                       observed-slot)
                     (00100111
                       (00000001 return-u64)
                       (00000001 result))))
                  ((00000011 0 0) 1 (00000001 machine-effect-rejected))))
               ((00000011 0 0) 1 (00000001 machine-effect-rejected))))
            ((00000011 0 0) 1 (00000001 machine-effect-rejected))))
         ((00000011 0 0) 1 (00000001 machine-effect-rejected))))
      ((00000011 0 0) 1 (00000001 machine-effect-rejected)))))