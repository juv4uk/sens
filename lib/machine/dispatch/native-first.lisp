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

(0011 native-first-fallback
  (0010 (expression)
    (1110 (001 evaluator-fallback) expression)))

(0011 native-first-native-plan
  (0010 (forms arena-bytes)
    (1110 (001 native-plan) forms arena-bytes)))

(0011 native-first-plan-car-cons-u64
  (0010 (expression cons-expression)
    ((0010 (cons-arguments) (110
        ((010 cons-arguments)
         (native-first-fallback expression))
        ((native-first-domain-true ())
         ((0010 (rest-after-left) (110
             ((010 rest-after-left)
              (native-first-fallback expression))
             ((native-first-domain-true ())
              ((0010 (rest-after-right) (110
                  ((101 rest-after-right ())
                   ((0010 (typed-left) (110
                       ((101 (100 typed-left) (001 u64-imm))
                        ((0010 (typed-right) (110
                            ((101 (100 typed-right) (001 u64-imm))
                             (native-first-native-plan
                               (x86-lower-cons-car-u64-forms
                                 (x86-u64-imm-value typed-left)
                                 (x86-u64-imm-value typed-right))
                               x86-pair-cell-bytes))
                            ((native-first-domain-true ())
                             (native-first-fallback expression)))) (x86-as-u64-imm (100 rest-after-left))))
                       ((native-first-domain-true ())
                        (native-first-fallback expression)))) (x86-as-u64-imm (100 cons-arguments))))
                  ((native-first-domain-true ())
                   (native-first-fallback expression)))) (011 rest-after-left))))) (011 cons-arguments))))) (011 cons-expression))))
(0011 native-first-plan-car-argument
  (0010 (expression argument)
    (110
      ((010 argument)
       (native-first-fallback expression))
      ((native-first-domain-true ())
       ((0010 (head) (110
           ((010 head)
            (110
              ((101 head (001 111))
               (native-first-plan-car-cons-u64 expression argument))
              ((native-first-domain-true ())
               (native-first-fallback expression))))
           ((native-first-domain-true ())
            (native-first-fallback expression)))) (100 argument))))))

(0011 native-first-plan-car
  (0010 (expression)
    ((0010 (arguments) (110
        ((010 arguments)
         (native-first-fallback expression))
        ((native-first-domain-true ())
         (110
           ((010 (011 arguments))
            (native-first-plan-car-argument expression (100 arguments)))
           ((native-first-domain-true ())
            (native-first-fallback expression)))))) (011 expression))))

(0011 native-first-plan
  (0010 (expression)
    (110
      ((010 expression)
       (native-first-fallback expression))
      ((native-first-domain-true ())
       ((0010 (head) (110
           ((010 head)
            (110
              ((101 head (001 100))
               (native-first-plan-car expression))
              ((native-first-domain-true ())
               (native-first-fallback expression))))
           ((native-first-domain-true ())
            (native-first-fallback expression)))) (100 expression))))))

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

(0011 native-first-plan-domain
  (0010 (shape-or-empty expression)
    (110
      ((010 expression)
       (native-first-fallback expression))
      ((native-first-domain-d3-car? shape-or-empty (100 expression))
       (native-first-plan-domain-car shape-or-empty expression))
      ((native-first-domain-true ())
       (native-first-fallback expression)))))