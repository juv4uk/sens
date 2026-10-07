; #4349 — bounded target-neutral structural machine effects.
;
; This layer consumes already-decided representation data (field offsets and
; bounded machine words). It does not know CAR/CONS/pair meaning, x86 registers,
; opcodes, addressing encodings, or a target ABI.
;
; One calibration sequence is demanded by the existing bounded two-field
; store/load witness:
;   materialize -> store -> materialize -> store -> load -> return.
;
; Offsets are inputs from the representation/layout authority. Target-specific
; displacement legality is checked only by the later target projection.

(00001001 machine-effect-u64-carrier?
  (00001000 (value)
    (00000111
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 18446744073709551615))
      (t (00000001 ())))))

(00001001 machine-effect-nonnegative-offset?
  (00001000 (value)
    (00000111
      ((machine-effect-exact-integer? value)
       (00000111
         ((00011110 value 0) 1 t)
         ((00011110 value 0) 0 (00000001 ()))))
      (t (00000001 ())))))

(00001001 machine-effect-bounded-two-field-store-load
  (00001000 (first-value second-value first-offset second-offset observed-offset)
    (00000111
      ((machine-effect-u64-carrier? first-value)
       (00000111
         ((machine-effect-u64-carrier? second-value)
          (00000111
            ((machine-effect-nonnegative-offset? first-offset)
             (00000111
               ((machine-effect-nonnegative-offset? second-offset)
                (00000111
                  ((machine-effect-nonnegative-offset? observed-offset)
                   (00100111
                     (00100111
                       (00000001 materialize-u64)
                       (00000001 work)
                       first-value)
                     (00100111
                       (00000001 store-u64)
                       (00000001 arena)
                       first-offset
                       (00000001 work))
                     (00100111
                       (00000001 materialize-u64)
                       (00000001 work)
                       second-value)
                     (00100111
                       (00000001 store-u64)
                       (00000001 arena)
                       second-offset
                       (00000001 work))
                     (00100111
                       (00000001 load-u64)
                       (00000001 result)
                       (00000001 arena)
                       observed-offset)
                     (00100111
                       (00000001 return-u64)
                       (00000001 result)))
                   (t (00000001 machine-effect-rejected))))
               (t (00000001 machine-effect-rejected))))
            (t (00000001 machine-effect-rejected))))
         (t (00000001 machine-effect-rejected))))
      (t (00000001 machine-effect-rejected)))))
