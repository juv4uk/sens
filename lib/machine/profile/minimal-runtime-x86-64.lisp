; #196 — machine-readable lower-bound profiles derived from bounded Lisp witnesses.
;
; This file is deliberately NOT a second ISA catalogue, opcode table, encoder,
; or admission list. Observed machine families are derived from already-existing
; semantic lowering. Hand-authored dependency rows explain only why each family
; is necessary for its bounded witness.
;
; Current claim boundaries:
;   structural-v0: (car (cons 2 3)) -> 2 using one 16-byte pair arena.
;   conditional-growth-v0: (cond ((eq A B) THEN) (t ELSE)) for bounded u64.
;   conditional-structural-v0: bounded COND with CAR(CONS ...) in both arms.
; None is a full allocator, GC, label resolver, calling convention, compiler,
; or self-hosting claim.

(00001001 x86-minimal-structural-car-dependencies
  (00000001
    ((materialize-value
       mov-r64-imm64
       required-for-minimal-runtime
       "materialize bounded u64 pair fields")
     (store-pair-field
       mov-mem-disp8-r64
       required-for-minimal-runtime
       "store bounded pair head/tail into the host-provided arena")
     (load-pair-field
       mov-r64-mem-disp8
       required-for-minimal-runtime
       "load the CAR field from the bounded pair")
     (return-result
       ret
       required-for-minimal-runtime
       "return the bounded result through the host ABI"))))

(00001001 x86-minimal-eq-cond-dependencies
  (00000001
    ((materialize-value
       mov-r64-imm64
       required-for-minimal-runtime
       "materialize bounded u64 predicate operands and selected-arm values")
     (compare-equality
       cmp-r64-r64
       required-for-minimal-runtime
       "produce the equality condition required by the bounded EQ predicate")
     (branch-on-false
       jnz-rel8
       required-for-minimal-runtime
       "select the ELSE arm when the bounded equality predicate is false")
     (return-selected-result
       ret
       required-for-minimal-runtime
       "return the selected bounded result through the guest ABI"))))

(00001001 x86-minimal-eq-cond-car-cons-dependencies
  (00000001
    ((materialize-values
       mov-r64-imm64
       required-for-minimal-runtime
       "materialize bounded EQ operands and branch-local pair fields, including r8-r11")
     (compare-equality
       cmp-r64-r64
       required-for-minimal-runtime
       "produce the equality condition required by the bounded EQ predicate")
     (branch-on-false
       jnz-rel8
       required-for-minimal-runtime
       "select the ELSE structural arm when bounded equality is false")
     (store-pair-field
       mov-mem-disp8-r64
       required-for-minimal-runtime
       "store the selected branch pair into the native-call arena")
     (load-pair-car
       mov-r64-mem-disp8
       required-for-minimal-runtime
       "load the selected branch CAR result from the bounded pair")
     (return-result
       ret
       required-for-minimal-runtime
       "return the selected structural result through the guest ABI"))))

(00001001 x86-minimal-family-member?
  (00001000 (family families)
    (00000111
      
      ((00000010 families)  ())
      ((00000011 family (00000101 families)) t)
      ((00000010 ()) (x86-minimal-family-member? family (00000110 families))))))

(00001001 x86-minimal-unique-form-families
  (00001000 (forms seen)
    (00000111
      
      ((00000010 forms)  seen)
      ((00000010 ())
       (10011100 ((family (00000101 (00000101 forms))))
         (00000111
           ((x86-minimal-family-member? family seen)
            (x86-minimal-unique-form-families (00000110 forms) seen))
           ((00000010 ())
            (x86-minimal-unique-form-families
              (00000110 forms)
              (00101001 seen (00100111 family))))))))))

(00001001 x86-minimal-row-second
  (00001000 (row)
    (00000101 (00000110 row))))

(00001001 x86-minimal-row-third
  (00001000 (row)
    (00000101 (00000110 (00000110 row)))))

(00001001 x86-minimal-map-row-second
  (00001000 (rows)
    (00000111
      
      ((00000010 rows)  (00000001 ()))
      ((00000010 ())
       (00000100
         (x86-minimal-row-second (00000101 rows))
         (x86-minimal-map-row-second (00000110 rows)))))))

(00001001 x86-minimal-map-row-third
  (00001000 (rows)
    (00000111
      
      ((00000010 rows)  (00000001 ()))
      ((00000010 ())
       (00000100
         (x86-minimal-row-third (00000101 rows))
         (x86-minimal-map-row-third (00000110 rows)))))))

(00001001 x86-minimal-structural-car-forms
  (00001000 (left right)
    (x86-lower-cons-car-u64-forms left right)))

(00001001 x86-minimal-structural-car-observed-families
  (00001000 (left right)
    (x86-minimal-unique-form-families
      (x86-minimal-structural-car-forms left right)
      (00000001 ()))))

(00001001 x86-minimal-structural-car-dependency-families
  (00001000 ()
    (x86-minimal-map-row-second x86-minimal-structural-car-dependencies)))

(00001001 x86-minimal-structural-car-dependency-classes
  (00001000 ()
    (x86-minimal-map-row-third x86-minimal-structural-car-dependencies)))

(00001001 x86-minimal-structural-car-profile
  (00001000 (left right)
    (00100111
      (00100111 (00000001 witness) (00000001 bounded-car-cons-u64))
      (00100111 (00000001 forms) (x86-minimal-structural-car-forms left right))
      (00100111
        (00000001 observed-families)
        (x86-minimal-structural-car-observed-families left right))
      (00100111 (00000001 dependencies) x86-minimal-structural-car-dependencies)
      (00100111 (00000001 arena-lifetime) (00000001 native-call))
      (00100111 (00000001 escape) (00000001 forbidden))
      (00100111 (00000001 claim) (00000001 bounded-structural-lower-bound)))))

(00001001 x86-minimal-eq-cond-forms
  (00001000 (left right then-value else-value)
    (x86-lower-eq-cond-u64-forms left right then-value else-value)))

(00001001 x86-minimal-eq-cond-observed-families
  (00001000 (left right then-value else-value)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-forms left right then-value else-value)
      (00000001 ()))))

(00001001 x86-minimal-eq-cond-dependency-families
  (00001000 ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-dependencies)))

(00001001 x86-minimal-eq-cond-dependency-classes
  (00001000 ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-dependencies)))

(00001001 x86-minimal-eq-cond-profile
  (00001000 (left right then-value else-value)
    (00100111
      (00100111 (00000001 witness) (00000001 bounded-eq-cond-u64))
      (00100111
        (00000001 forms)
        (x86-minimal-eq-cond-forms left right then-value else-value))
      (00100111
        (00000001 observed-families)
        (x86-minimal-eq-cond-observed-families
          left right then-value else-value))
      (00100111 (00000001 dependencies) x86-minimal-eq-cond-dependencies)
      (00100111 (00000001 claim) (00000001 bounded-conditional-growth-lower-bound)))))

(00001001 x86-minimal-eq-cond-car-cons-forms
  (00001000 (left right then-car then-cdr else-car else-cdr)
    (x86-lower-eq-cond-car-cons-u64-forms
      left right then-car then-cdr else-car else-cdr)))

(00001001 x86-minimal-eq-cond-car-cons-observed-families
  (00001000 (left right then-car then-cdr else-car else-cdr)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-car-cons-forms
        left right then-car then-cdr else-car else-cdr)
      (00000001 ()))))

(00001001 x86-minimal-eq-cond-car-cons-dependency-families
  (00001000 ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-car-cons-dependencies)))

(00001001 x86-minimal-eq-cond-car-cons-dependency-classes
  (00001000 ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-car-cons-dependencies)))

(00001001 x86-minimal-eq-cond-car-cons-profile
  (00001000 (left right then-car then-cdr else-car else-cdr)
    (00100111
      (00100111 (00000001 witness) (00000001 bounded-eq-cond-car-cons-u64))
      (00100111
        (00000001 forms)
        (x86-minimal-eq-cond-car-cons-forms
          left right then-car then-cdr else-car else-cdr))
      (00100111
        (00000001 observed-families)
        (x86-minimal-eq-cond-car-cons-observed-families
          left right then-car then-cdr else-car else-cdr))
      (00100111 (00000001 dependencies) x86-minimal-eq-cond-car-cons-dependencies)
      (00100111 (00000001 arena-lifetime) (00000001 native-call))
      (00100111 (00000001 escape) (00000001 forbidden))
      (00100111
        (00000001 claim)
        (00000001 bounded-conditional-structural-composition-lower-bound)))))
