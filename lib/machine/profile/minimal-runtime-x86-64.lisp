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

(0011 x86-minimal-structural-car-dependencies
  (001
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

(0011 x86-minimal-eq-cond-dependencies
  (001
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

(0011 x86-minimal-eq-cond-car-cons-dependencies
  (001
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

(0011 x86-minimal-family-member?
  (0010 (family families)
    (110
      
      ((010 families)  ())
      ((101 family (100 families)) t)
      ((010 ()) (x86-minimal-family-member? family (011 families))))))

(0011 x86-minimal-unique-form-families
  (0010 (forms seen)
    (110
      
      ((010 forms)  seen)
      ((010 ())
       (001000 ((family (100 (100 forms))))
         (110
           ((x86-minimal-family-member? family seen)
            (x86-minimal-unique-form-families (011 forms) seen))
           ((010 ())
            (x86-minimal-unique-form-families
              (011 forms)
              (1111 seen (1110 family))))))))))

(0011 x86-minimal-row-second
  (0010 (row)
    (100 (011 row))))

(0011 x86-minimal-row-third
  (0010 (row)
    (100 (011 (011 row)))))

(0011 x86-minimal-map-row-second
  (0010 (rows)
    (110
      
      ((010 rows)  (001 ()))
      ((010 ())
       (111
         (x86-minimal-row-second (100 rows))
         (x86-minimal-map-row-second (011 rows)))))))

(0011 x86-minimal-map-row-third
  (0010 (rows)
    (110
      
      ((010 rows)  (001 ()))
      ((010 ())
       (111
         (x86-minimal-row-third (100 rows))
         (x86-minimal-map-row-third (011 rows)))))))

(0011 x86-minimal-structural-car-forms
  (0010 (left right)
    (x86-lower-cons-car-u64-forms left right)))

(0011 x86-minimal-structural-car-observed-families
  (0010 (left right)
    (x86-minimal-unique-form-families
      (x86-minimal-structural-car-forms left right)
      (001 ()))))

(0011 x86-minimal-structural-car-dependency-families
  (0010 ()
    (x86-minimal-map-row-second x86-minimal-structural-car-dependencies)))

(0011 x86-minimal-structural-car-dependency-classes
  (0010 ()
    (x86-minimal-map-row-third x86-minimal-structural-car-dependencies)))

(0011 x86-minimal-structural-car-profile
  (0010 (left right)
    (1110
      (1110 (001 witness) (001 bounded-car-cons-u64))
      (1110 (001 forms) (x86-minimal-structural-car-forms left right))
      (1110
        (001 observed-families)
        (x86-minimal-structural-car-observed-families left right))
      (1110 (001 dependencies) x86-minimal-structural-car-dependencies)
      (1110 (001 arena-lifetime) (001 native-call))
      (1110 (001 escape) (001 forbidden))
      (1110 (001 claim) (001 bounded-structural-lower-bound)))))

(0011 x86-minimal-eq-cond-forms
  (0010 (left right then-value else-value)
    (x86-lower-eq-cond-u64-forms left right then-value else-value)))

(0011 x86-minimal-eq-cond-observed-families
  (0010 (left right then-value else-value)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-forms left right then-value else-value)
      (001 ()))))

(0011 x86-minimal-eq-cond-dependency-families
  (0010 ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-dependencies)))

(0011 x86-minimal-eq-cond-dependency-classes
  (0010 ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-dependencies)))

(0011 x86-minimal-eq-cond-profile
  (0010 (left right then-value else-value)
    (1110
      (1110 (001 witness) (001 bounded-eq-cond-u64))
      (1110
        (001 forms)
        (x86-minimal-eq-cond-forms left right then-value else-value))
      (1110
        (001 observed-families)
        (x86-minimal-eq-cond-observed-families
          left right then-value else-value))
      (1110 (001 dependencies) x86-minimal-eq-cond-dependencies)
      (1110 (001 claim) (001 bounded-conditional-growth-lower-bound)))))

(0011 x86-minimal-eq-cond-car-cons-forms
  (0010 (left right then-car then-cdr else-car else-cdr)
    (x86-lower-eq-cond-car-cons-u64-forms
      left right then-car then-cdr else-car else-cdr)))

(0011 x86-minimal-eq-cond-car-cons-observed-families
  (0010 (left right then-car then-cdr else-car else-cdr)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-car-cons-forms
        left right then-car then-cdr else-car else-cdr)
      (001 ()))))

(0011 x86-minimal-eq-cond-car-cons-dependency-families
  (0010 ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-car-cons-dependencies)))

(0011 x86-minimal-eq-cond-car-cons-dependency-classes
  (0010 ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-car-cons-dependencies)))

(0011 x86-minimal-eq-cond-car-cons-profile
  (0010 (left right then-car then-cdr else-car else-cdr)
    (1110
      (1110 (001 witness) (001 bounded-eq-cond-car-cons-u64))
      (1110
        (001 forms)
        (x86-minimal-eq-cond-car-cons-forms
          left right then-car then-cdr else-car else-cdr))
      (1110
        (001 observed-families)
        (x86-minimal-eq-cond-car-cons-observed-families
          left right then-car then-cdr else-car else-cdr))
      (1110 (001 dependencies) x86-minimal-eq-cond-car-cons-dependencies)
      (1110 (001 arena-lifetime) (001 native-call))
      (1110 (001 escape) (001 forbidden))
      (1110
        (001 claim)
        (001 bounded-conditional-structural-composition-lower-bound)))))
