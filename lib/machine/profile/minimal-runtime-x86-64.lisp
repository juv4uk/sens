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

(def x86-minimal-structural-car-dependencies
  (quote
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

(def x86-minimal-eq-cond-dependencies
  (quote
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

(def x86-minimal-eq-cond-car-cons-dependencies
  (quote
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

(def x86-minimal-family-member?
  (lambda (family families)
    (cond
      ((atom? families) ())
      ((eq? family (car families)) t)
      (t (x86-minimal-family-member? family (cdr families))))))

(def x86-minimal-unique-form-families
  (lambda (forms seen)
    (cond
      ((atom? forms) seen)
      (t
       (let ((family (car (car forms))))
         (cond
           ((x86-minimal-family-member? family seen)
            (x86-minimal-unique-form-families (cdr forms) seen))
           (t
            (x86-minimal-unique-form-families
              (cdr forms)
              (append seen (list family))))))))))

(def x86-minimal-row-second
  (lambda (row)
    (car (cdr row))))

(def x86-minimal-row-third
  (lambda (row)
    (car (cdr (cdr row)))))

(def x86-minimal-map-row-second
  (lambda (rows)
    (cond
      ((atom? rows) (quote ()))
      (t
       (cons
         (x86-minimal-row-second (car rows))
         (x86-minimal-map-row-second (cdr rows)))))))

(def x86-minimal-map-row-third
  (lambda (rows)
    (cond
      ((atom? rows) (quote ()))
      (t
       (cons
         (x86-minimal-row-third (car rows))
         (x86-minimal-map-row-third (cdr rows)))))))

(def x86-minimal-structural-car-forms
  (lambda (left right)
    (x86-lower-cons-car-u64-forms left right)))

(def x86-minimal-structural-car-observed-families
  (lambda (left right)
    (x86-minimal-unique-form-families
      (x86-minimal-structural-car-forms left right)
      (quote ()))))

(def x86-minimal-structural-car-dependency-families
  (lambda ()
    (x86-minimal-map-row-second x86-minimal-structural-car-dependencies)))

(def x86-minimal-structural-car-dependency-classes
  (lambda ()
    (x86-minimal-map-row-third x86-minimal-structural-car-dependencies)))

(def x86-minimal-structural-car-profile
  (lambda (left right)
    (list
      (list (quote witness) (quote bounded-car-cons-u64))
      (list (quote forms) (x86-minimal-structural-car-forms left right))
      (list
        (quote observed-families)
        (x86-minimal-structural-car-observed-families left right))
      (list (quote dependencies) x86-minimal-structural-car-dependencies)
      (list (quote arena-lifetime) (quote native-call))
      (list (quote escape) (quote forbidden))
      (list (quote claim) (quote bounded-structural-lower-bound)))))

(def x86-minimal-eq-cond-forms
  (lambda (left right then-value else-value)
    (x86-lower-eq-cond-u64-forms left right then-value else-value)))

(def x86-minimal-eq-cond-observed-families
  (lambda (left right then-value else-value)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-forms left right then-value else-value)
      (quote ()))))

(def x86-minimal-eq-cond-dependency-families
  (lambda ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-dependencies)))

(def x86-minimal-eq-cond-dependency-classes
  (lambda ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-dependencies)))

(def x86-minimal-eq-cond-profile
  (lambda (left right then-value else-value)
    (list
      (list (quote witness) (quote bounded-eq-cond-u64))
      (list
        (quote forms)
        (x86-minimal-eq-cond-forms left right then-value else-value))
      (list
        (quote observed-families)
        (x86-minimal-eq-cond-observed-families
          left right then-value else-value))
      (list (quote dependencies) x86-minimal-eq-cond-dependencies)
      (list (quote claim) (quote bounded-conditional-growth-lower-bound)))))

(def x86-minimal-eq-cond-car-cons-forms
  (lambda (left right then-car then-cdr else-car else-cdr)
    (x86-lower-eq-cond-car-cons-u64-forms
      left right then-car then-cdr else-car else-cdr)))

(def x86-minimal-eq-cond-car-cons-observed-families
  (lambda (left right then-car then-cdr else-car else-cdr)
    (x86-minimal-unique-form-families
      (x86-minimal-eq-cond-car-cons-forms
        left right then-car then-cdr else-car else-cdr)
      (quote ()))))

(def x86-minimal-eq-cond-car-cons-dependency-families
  (lambda ()
    (x86-minimal-map-row-second x86-minimal-eq-cond-car-cons-dependencies)))

(def x86-minimal-eq-cond-car-cons-dependency-classes
  (lambda ()
    (x86-minimal-map-row-third x86-minimal-eq-cond-car-cons-dependencies)))

(def x86-minimal-eq-cond-car-cons-profile
  (lambda (left right then-car then-cdr else-car else-cdr)
    (list
      (list (quote witness) (quote bounded-eq-cond-car-cons-u64))
      (list
        (quote forms)
        (x86-minimal-eq-cond-car-cons-forms
          left right then-car then-cdr else-car else-cdr))
      (list
        (quote observed-families)
        (x86-minimal-eq-cond-car-cons-observed-families
          left right then-car then-cdr else-car else-cdr))
      (list (quote dependencies) x86-minimal-eq-cond-car-cons-dependencies)
      (list (quote arena-lifetime) (quote native-call))
      (list (quote escape) (quote forbidden))
      (list
        (quote claim)
        (quote bounded-conditional-structural-composition-lower-bound)))))
