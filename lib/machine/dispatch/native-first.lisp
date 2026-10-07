; #505 — Lisp-owned native-first execution-plan classifier.
;
; This file decides only whether an already-proven machine lowering applies to
; expression *data*. It does not define language meaning, encode bytes, or call
; the host. Unsupported expressions are ordinary evaluator-fallback outcomes.
;
; Required layers are loaded by the caller:
;   lib/machine/layout/pair-x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/lowering/semantic-x86-64.lisp

(00001001 native-first-fallback
  (00001000 (expression)
    (00100111 (00000001 evaluator-fallback) expression)))

(00001001 native-first-native-plan
  (00001000 (forms arena-bytes)
    (00100111 (00000001 native-plan) forms arena-bytes)))

(00001001 native-first-plan-car-cons-u64
  (00001000 (expression cons-expression)
    (10011100 ((cons-arguments (00000110 cons-expression)))
      (00000111
        ((00000010 cons-arguments) (0)
         (10011100 ((rest-after-left (00000110 cons-arguments)))
           (00000111
             ((00000010 rest-after-left) (0)
              (10011100 ((rest-after-right (00000110 rest-after-left)))
                (00000111
                  ((00000010 rest-after-right) ()
                   (10011100 ((typed-left (x86-as-u64-imm (00000101 cons-arguments))))
                     (00000111
                       ((00000011 (00000101 typed-left) (00000001 u64-imm))
                        (1)
                        (10011100 ((typed-right (x86-as-u64-imm (00000101 rest-after-left))))
                          (00000111
                            ((00000011 (00000101 typed-right) (00000001 u64-imm))
                             (1)
                             (native-first-native-plan
                               (x86-lower-cons-car-u64-forms
                                 (x86-u64-imm-value typed-left)
                                 (x86-u64-imm-value typed-right))
                               x86-pair-cell-bytes))
                            ((00000001 native-first-fallback)
                             native-first-fallback
                             (native-first-fallback expression)))))
                       ((00000001 native-first-fallback)
                        native-first-fallback
                        (native-first-fallback expression)))))
                  ((00000001 native-first-fallback)
                   native-first-fallback
                   (native-first-fallback expression)))))
             ((00000001 native-first-fallback)
              native-first-fallback
              (native-first-fallback expression)))))
        ((00000001 native-first-fallback)
         native-first-fallback
         (native-first-fallback expression))))))

(00001001 native-first-plan-car-argument
  (00001000 (expression argument)
    (00000111
      ((00000010 argument) (0)
       (10011100 ((head (00000101 argument)))
         (00000111
           ((00000010 head) ()
            (native-first-fallback expression))
           ((00000010 head) (0)
            (native-first-fallback expression))
           ((00000010 head) (1)
            (00000111
              ((00000011 head (00000001 cons)) (1)
               (native-first-plan-car-cons-u64 expression argument))
              ((00000011 head (00000001 cons)) (0)
               (native-first-fallback expression)))))))
      ((00000001 native-first-fallback)
       native-first-fallback
       (native-first-fallback expression)))))

(00001001 native-first-plan-car
  (00001000 (expression)
    (10011100 ((arguments (00000110 expression)))
      (00000111
        ((00000010 arguments) (0)
         (00000111
           ((00000010 (00000110 arguments)) ()
            (native-first-plan-car-argument expression (00000101 arguments)))
           ((00000001 native-first-fallback)
            native-first-fallback
            (native-first-fallback expression))))
        ((00000001 native-first-fallback)
         native-first-fallback
         (native-first-fallback expression))))))

(00001001 native-first-plan
  (00001000 (expression)
    (00000111
      ((00000010 expression) (0)
       (10011100 ((head (00000101 expression)))
         (00000111
           ((00000010 head) ()
            (native-first-fallback expression))
           ((00000010 head) (0)
            (native-first-fallback expression))
           ((00000010 head) (1)
            (00000111
              ((00000011 head (00000001 car)) (1)
               (native-first-plan-car expression))
              ((00000011 head (00000001 car)) (0)
               (native-first-fallback expression)))))))
      ((00000001 native-first-fallback)
       native-first-fallback
       (native-first-fallback expression)))))

; #4081 — exact-domain native-first classifier.
;
; Input is already-lowered source-shaped program-data:
;   (DomainIdentity arg...)
; The caller supplies a representation-only SHAPE-OR-EMPTY mechanism:
;   DomainIdentity -> (width (PredicateBit...))
;   any other value -> ()
;
; This block never matches CAR/CONS by spelling and never relies on a raw W3
; source token whose leading zero/width could be lost by the ordinary reader.

(0011 native-first-domain-true
  (0010 (seed)
    (010 seed)))

(0011 native-first-domain-false
  (0010 (seed)
    (010 (111 seed ()))))

(0011 native-first-domain-key3-shape?
  (0010 (shape bit0 bit1 bit2)
    (110
      ((010 shape)
       (native-first-domain-false ()))
      ((101 (100 shape) 3)
       (native-first-domain-key3-bits?
         (100 (011 shape))
         bit0 bit1 bit2))
      ((native-first-domain-true ())
       (native-first-domain-false ())))))

(0011 native-first-domain-key3-bits?
  (0010 (bits bit0 bit1 bit2)
    (110
      ((101 (100 bits) bit0)
       (110
         ((101 (100 (011 bits)) bit1)
          (101
            (100 (011 (011 bits)))
            bit2))
         ((native-first-domain-true ())
          (native-first-domain-false ()))))
      ((native-first-domain-true ())
       (native-first-domain-false ())))))

(0011 native-first-domain-d3-car?
  (0010 (shape-or-empty value)
    (native-first-domain-key3-shape?
      (shape-or-empty value)
      (native-first-domain-true ())
      (native-first-domain-false ())
      (native-first-domain-false ()))))

(0011 native-first-domain-d3-cons?
  (0010 (shape-or-empty value)
    (native-first-domain-key3-shape?
      (shape-or-empty value)
      (native-first-domain-true ())
      (native-first-domain-true ())
      (native-first-domain-true ()))))

(0011 native-first-plan-domain-cons-argument
  (0010 (shape-or-empty expression argument)
    (110
      ((010 argument)
       (native-first-fallback expression))
      ((native-first-domain-d3-cons? shape-or-empty (100 argument))
       (native-first-plan-car-cons-u64 expression argument))
      ((native-first-domain-true ())
       (native-first-fallback expression)))))

(0011 native-first-plan-domain-car
  (0010 (shape-or-empty expression)
    (110
      ((010 (011 expression))
       (native-first-fallback expression))
      ((010 (011 (011 expression)))
       (110
         ((101 (011 (011 expression)) ())
          (native-first-plan-domain-cons-argument
            shape-or-empty
            expression
            (100 (011 expression))))
         ((native-first-domain-true ())
          (native-first-fallback expression))))
      ((native-first-domain-true ())
       (native-first-fallback expression)))))

(визначити native-first-plan-domain
  (функція (shape-or-empty expression)
    (за-умовою
      ((атом? expression)
       (native-first-fallback expression))
      ((native-first-domain-d3-car? shape-or-empty (перше expression))
       (native-first-plan-domain-car shape-or-empty expression))
      ((native-first-domain-true ())
       (native-first-fallback expression)))))
