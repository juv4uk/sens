; #4347/#4349 — explicit projection from canonical machine effects to x86-64.
;
; Upstream effect identity is target-neutral. This file alone chooses physical
; registers and consumes target layout. Projection rejection is distinct from
; effect-construction rejection.

(00001001 x86-machine-effect-form?
  (00001000 (effect operation arity)
    (00000111
      ((00000010 effect) (00000001 ()))
      ((00100010 (00101000 effect) arity)
       (00000011 (00000101 effect) operation))
      (t (00000001 ())))))

(00001001 x86-projection-rejected?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (00000011 value (00000001 x86-projection-rejected)))
      (t (00000001 ())))))

(00001001 x86-structural-machine-effect?
  (00001000 (effect)
    (00000111
      ((x86-machine-effect-form? effect (00000001 materialize-u64) 3) t)
      ((x86-machine-effect-form? effect (00000001 store-u64) 4) t)
      ((x86-machine-effect-form? effect (00000001 load-u64) 4) t)
      ((x86-machine-effect-form? effect (00000001 return-u64) 2) t)
      (t (00000001 ())))))

; Translate abstract representation slots to one target layout.
(00001001 x86-project-structural-slot-offset
  (00001000 (slot field0-offset field1-offset)
    (00000111
      ((00000011 slot (00000001 field0)) field0-offset)
      ((00000011 slot (00000001 field1)) field1-offset)
      (t (00000001 x86-projection-rejected)))))

(00001001
  x86-project-structural-machine-effect-with-layout
  (00001000
    (effect field0-offset field1-offset)
    (00000111
      ((x86-machine-effect-form?
         effect
         (00000001 materialize-u64)
         3)
        (10011100
          ((slot
             (00000101
               (00000110 effect)))
            (value
              (00000101
                (00000110
                  (00000110 effect)))))
          (00000111
            ((00000011
               slot
               (00000001 work))
              (00100111
                (00100111
                  (00000001 mov-r64-imm64)
                  (00000001 rax)
                  value)))
            (t
              (00000001 x86-projection-rejected)))))
      ((x86-machine-effect-form?
         effect
         (00000001 store-u64)
         4)
        (10011100
          ((base
             (00000101
               (00000110 effect)))
            (field-slot
              (00000101
                (00000110
                  (00000110 effect))))
            (value-slot
              (00000101
                (00000110
                  (00000110
                    (00000110 effect)))))
            (offset
              (x86-project-structural-slot-offset field-slot field0-offset field1-offset)))
          (00000111
            ((x86-projection-rejected? offset)
              (00000001 x86-projection-rejected))
            ((00000011
               base
               (00000001 arena))
              (00000111
                ((00000011
                   value-slot
                   (00000001 work))
                  (00000111
                    ((x86-admission-disp8? offset)
                      (00100111
                        (00100111
                          (00000001 mov-mem-disp8-r64)
                          (00000001 rdi)
                          offset
                          (00000001 rax))))
                    (t
                      (00000001 x86-projection-rejected))))
                (t
                  (00000001 x86-projection-rejected))))
            (t
              (00000001 x86-projection-rejected)))))
      ((x86-machine-effect-form?
         effect
         (00000001 load-u64)
         4)
        (10011100
          ((result-slot
             (00000101
               (00000110 effect)))
            (base
              (00000101
                (00000110
                  (00000110 effect))))
            (field-slot
              (00000101
                (00000110
                  (00000110
                    (00000110 effect)))))
            (offset
              (x86-project-structural-slot-offset field-slot field0-offset field1-offset)))
          (00000111
            ((x86-projection-rejected? offset)
              (00000001 x86-projection-rejected))
            ((00000011
               result-slot
               (00000001 result))
              (00000111
                ((00000011
                   base
                   (00000001 arena))
                  (00000111
                    ((x86-admission-disp8? offset)
                      (00100111
                        (00100111
                          (00000001 mov-r64-mem-disp8)
                          (00000001 rax)
                          (00000001 rdi)
                          offset)))
                    (t
                      (00000001 x86-projection-rejected))))
                (t
                  (00000001 x86-projection-rejected))))
            (t
              (00000001 x86-projection-rejected)))))
      ((x86-machine-effect-form?
         effect
         (00000001 return-u64)
         2)
        (10011100
          ((slot
             (00000101
               (00000110 effect))))
          (00000111
            ((00000011
               slot
               (00000001 result))
              (00100111
                (00100111
                  (00000001 ret))))
            (t
              (00000001 x86-projection-rejected)))))
      (t
        (00000001 x86-projection-rejected)))))

(00001001 x86-project-machine-effect
  (00001000 (effect)
    (00000111
      ((machine-effect-bounded-u64-add-form? effect)
       (10011100
         ((left (00000101 (00000110 effect)))
          (right (00000101 (00000110 (00000110 effect)))))
         (00100111
           (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
           (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
           (00100111 (00000001 add-r64-r64) (00000001 rax) (00000001 rcx))
           (00100111 (00000001 ret)))))
      ((x86-structural-machine-effect? effect)
       (x86-project-structural-machine-effect-with-layout
         effect x86-pair-car-offset x86-pair-cdr-offset))
      (t (00000001 x86-projection-rejected)))))

(00001001 x86-project-machine-effects
  (00001000 (effects)
    (00000111
      ((00000010 effects) ())
      (t
       (10011100
         ((projected (x86-project-machine-effect (00000101 effects))))
         (00000111
           ((x86-projection-rejected? projected)
            (00000001 x86-projection-rejected))
           (t
            (10011100
              ((rest-projected
                 (x86-project-machine-effects (00000110 effects))))
              (00000111
                ((x86-projection-rejected? rest-projected)
                 (00000001 x86-projection-rejected))
                (t
                 (00101001 projected rest-projected)))))))))))

(00001001 x86-project-machine-effects-with-layout
  (00001000 (effects field0-offset field1-offset)
    (00000111
      ((00000010 effects) ())
      (t
       (10011100
         ((projected
            (x86-project-structural-machine-effect-with-layout
              (00000101 effects)
              field0-offset
              field1-offset)))
         (00000111
           ((x86-projection-rejected? projected)
            (00000001 x86-projection-rejected))
           (t
            (10011100
              ((rest-projected
                 (x86-project-machine-effects-with-layout
                   (00000110 effects)
                   field0-offset
                   field1-offset)))
              (00000111
                ((x86-projection-rejected? rest-projected)
                 (00000001 x86-projection-rejected))
                (t
                 (00101001 projected rest-projected)))))))))))

(00001001 x86-encode-machine-effect
  (00001000 (effect)
    (10011100 ((forms (x86-project-machine-effect effect)))
      (00000111
        ((x86-projection-rejected? forms)
         (00000001 x86-projection-rejected))
        (t
         (x86-encode-admitted-program forms))))))

(00001001 x86-encode-machine-effects
  (00001000 (effects)
    (10011100 ((forms (x86-project-machine-effects effects)))
      (00000111
        ((x86-projection-rejected? forms)
         (00000001 x86-projection-rejected))
        (t
         (x86-encode-admitted-program-or-reject forms))))))

; Semantic wrapper for the bounded Vertical Day CAR(CONS) proof. Canonical
; CAR/CDR semantics execute before effects exist. The canonical effect object
; carries field0/field1 only; x86 layout is first consumed by projection.
(00001001 x86-call-semantic-car-effect-u64
  (00001000 (pair-value)
    (10011100
      ((first-value (00000101 pair-value))
       (second-value (00000110 pair-value)))
      (10011100
        ((effects
           (machine-effect-bounded-two-field-store-load
             first-value
             second-value
             (00000001 field0)
             (00000001 field1)
             (00000001 field0))))
        (00000111
          ((00000010 effects)
           effects)
          (t
           (10011100 ((forms (x86-project-machine-effects effects)))
             (00000111
               ((x86-projection-rejected? forms)
                (00000001 x86-projection-rejected))
               (t
                (x86-call-admitted-u64 forms x86-pair-cell-bytes))))))))))
