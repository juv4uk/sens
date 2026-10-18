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

(визначити x86-minimal-structural-car-dependencies
  (як-є
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

(визначити x86-minimal-eq-cond-dependencies
  (як-є
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

(визначити x86-minimal-eq-cond-car-cons-dependencies
  (як-є
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

(визначити x86-minimal-family-member?
  (функція (family families)
    (за-умовою
      
      ((атом? families)  ())
      ((тотожне? family (перше families)) t)
      ((атом? ()) (x86-minimal-family-member? family (решта families))))))

(визначити x86-minimal-unique-form-families
  (функція (forms seen)
    (за-умовою
      
      ((атом? forms)  seen)
      ((атом? ())
       (нехай ((family (перше (перше forms))))
         (за-умовою
           ((x86-minimal-family-member? family seen)
            (x86-minimal-unique-form-families (решта forms) seen))
           ((атом? ())
            (x86-minimal-unique-form-families
              (решта forms)
              (приєднати seen (список family))))))))))

(визначити x86-minimal-row-second
  (функція (row)
    (перше (решта row))))

(визначити x86-minimal-row-third
  (функція (row)
    (перше (решта (решта row)))))

(визначити x86-minimal-map-row-second
  (функція (rows)
    (за-умовою
      
      ((атом? rows)  (як-є ()))
      ((атом? ())
       (сполучити
         (x86-minimal-row-second (перше rows))
         (x86-minimal-map-row-second (решта rows)))))))

(визначити x86-minimal-map-row-third
  (функція (rows)
    (за-умовою
      
      ((атом? rows)  (як-є ()))
      ((атом? ())
       (сполучити
         (x86-minimal-row-third (перше rows))
         (x86-minimal-map-row-third (решта rows)))))))

(визначити x86-minimal-structural-car-forms
  (функція (left right)
    (x86-lower-cons-car-u64-forms left right)))

(визначити x86-minimal-structural-car-observed-families
  (функція (left right)
    (x86-minimal-unique-form-families
      (x86-minimal-structural-car-forms left right)
      (як-є ()))))

(визначити x86-minimal-structural-car-dependency-families
  (функція ()
    (x86-minimal-map-row-second x86-minimal-structural-car-dependencies)))

(визначити x86-minimal-structural-car-dependency-classes
  (функція ()
    (x86-minimal-map-row-third x86-minimal-structural-car-dependencies)))

(визначити x86-minimal-structural-car-profile
  (функція (left right)
    (список
      (список (як-є witness) (як-є bounded-car-cons-u64))
      (список (як-є forms) (x86-minimal-structural-car-forms left right))
      (список
        (як-є observed-families)
        (x86-minimal-structural-car-observed-families left right))
      (список (як-є dependencies) x86-minimal-structural-car-dependencies)
      (список (як-є arena-lifetime) (як-є native-call))
      (список (як-є escape) (як-є forbidden))
      (список (як-є claim) (як-є bounded-structural-lower-bound)))))

(визначити x86-minimal-eq-cond-forms
  (функція (left right then-value else-value)
    (x86-lower-eq-cond-u64-forms left right then-value else-value)))

(визначити x86-minimal-eq-cond-observed-families
  (функція (left right then-value else-value)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-forms left right then-value else-value)
      (як-є ()))))

(визначити x86-minimal-eq-cond-dependency-families
  (функція ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-dependencies)))

(визначити x86-minimal-eq-cond-dependency-classes
  (функція ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-dependencies)))

(визначити x86-minimal-eq-cond-profile
  (функція (left right then-value else-value)
    (список
      (список (як-є witness) (як-є bounded-eq-cond-u64))
      (список
        (як-є forms)
        (x86-minimal-eq-cond-forms left right then-value else-value))
      (список
        (як-є observed-families)
        (x86-minimal-eq-cond-observed-families
          left right then-value else-value))
      (список (як-є dependencies) x86-minimal-eq-cond-dependencies)
      (список (як-є claim) (як-є bounded-conditional-growth-lower-bound)))))

(визначити x86-minimal-eq-cond-car-cons-forms
  (функція (left right then-car then-cdr else-car else-cdr)
    (x86-lower-eq-cond-car-cons-u64-forms
      left right then-car then-cdr else-car else-cdr)))

(визначити x86-minimal-eq-cond-car-cons-observed-families
  (функція (left right then-car then-cdr else-car else-cdr)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-car-cons-forms
        left right then-car then-cdr else-car else-cdr)
      (як-є ()))))

(визначити x86-minimal-eq-cond-car-cons-dependency-families
  (функція ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-car-cons-dependencies)))

(визначити x86-minimal-eq-cond-car-cons-dependency-classes
  (функція ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-car-cons-dependencies)))

(визначити x86-minimal-eq-cond-car-cons-profile
  (функція (left right then-car then-cdr else-car else-cdr)
    (список
      (список (як-є witness) (як-є bounded-eq-cond-car-cons-u64))
      (список
        (як-є forms)
        (x86-minimal-eq-cond-car-cons-forms
          left right then-car then-cdr else-car else-cdr))
      (список
        (як-є observed-families)
        (x86-minimal-eq-cond-car-cons-observed-families
          left right then-car then-cdr else-car else-cdr))
      (список (як-є dependencies) x86-minimal-eq-cond-car-cons-dependencies)
      (список (як-є arena-lifetime) (як-є native-call))
      (список (як-є escape) (як-є forbidden))
      (список
        (як-є claim)
        (як-є bounded-conditional-structural-composition-lower-bound)))))
