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

(define native-first-fallback
  (lambda (expression)
    (list (quote evaluator-fallback) expression)))

(define native-first-native-plan
  (lambda (forms arena-bytes)
    (list (quote native-plan) forms arena-bytes)))

(define native-first-plan-car-cons-u64
  (lambda (expression cons-expression)
    (let ((cons-arguments (cdr cons-expression)))
      (cond
        ((atom? cons-arguments) (0)
         (let ((rest-after-left (cdr cons-arguments)))
           (cond
             ((atom? rest-after-left) (0)
              (let ((rest-after-right (cdr rest-after-left)))
                (cond
                  ((atom? rest-after-right) ()
                   (let ((typed-left (x86-as-u64-imm (car cons-arguments))))
                     (cond
                       ((eq? (car typed-left) (quote u64-imm))
                        (1)
                        (let ((typed-right (x86-as-u64-imm (car rest-after-left))))
                          (cond
                            ((eq? (car typed-right) (quote u64-imm))
                             (1)
                             (native-first-native-plan
                               (x86-lower-cons-car-u64-forms
                                 (x86-u64-imm-value typed-left)
                                 (x86-u64-imm-value typed-right))
                               x86-pair-cell-bytes))
                            ((quote native-first-fallback)
                             native-first-fallback
                             (native-first-fallback expression)))))
                       ((quote native-first-fallback)
                        native-first-fallback
                        (native-first-fallback expression)))))
                  ((quote native-first-fallback)
                   native-first-fallback
                   (native-first-fallback expression)))))
             ((quote native-first-fallback)
              native-first-fallback
              (native-first-fallback expression)))))
        ((quote native-first-fallback)
         native-first-fallback
         (native-first-fallback expression))))))

(define native-first-plan-car-argument
  (lambda (expression argument)
    (cond
      ((atom? argument) (0)
       (let ((head (car argument)))
         (cond
           ((atom? head) ()
            (native-first-fallback expression))
           ((atom? head) (0)
            (native-first-fallback expression))
           ((atom? head) (1)
            (cond
              ((eq? head (quote cons)) (1)
               (native-first-plan-car-cons-u64 expression argument))
              ((eq? head (quote cons)) (0)
               (native-first-fallback expression)))))))
      ((quote native-first-fallback)
       native-first-fallback
       (native-first-fallback expression)))))

(define native-first-plan-car
  (lambda (expression)
    (let ((arguments (cdr expression)))
      (cond
        ((atom? arguments) (0)
         (cond
           ((atom? (cdr arguments)) ()
            (native-first-plan-car-argument expression (car arguments)))
           ((quote native-first-fallback)
            native-first-fallback
            (native-first-fallback expression))))
        ((quote native-first-fallback)
         native-first-fallback
         (native-first-fallback expression))))))

(define native-first-plan
  (lambda (expression)
    (cond
      ((atom? expression) (0)
       (let ((head (car expression)))
         (cond
           ((atom? head) ()
            (native-first-fallback expression))
           ((atom? head) (0)
            (native-first-fallback expression))
           ((atom? head) (1)
            (cond
              ((eq? head (quote car)) (1)
               (native-first-plan-car expression))
              ((eq? head (quote car)) (0)
               (native-first-fallback expression)))))))
      ((quote native-first-fallback)
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

(визначити native-first-domain-true
  (функція (seed)
    (атом? seed)))

(визначити native-first-domain-false
  (функція (seed)
    (атом? (сполучити seed ()))))

(визначити native-first-domain-key3-shape?
  (функція (shape bit0 bit1 bit2)
    (за-умовою
      ((атом? shape)
       (native-first-domain-false ()))
      ((тотожне? (перше shape) 3)
       (native-first-domain-key3-bits?
         (перше (решта shape))
         bit0 bit1 bit2))
      ((native-first-domain-true ())
       (native-first-domain-false ())))))

(визначити native-first-domain-key3-bits?
  (функція (bits bit0 bit1 bit2)
    (за-умовою
      ((тотожне? (перше bits) bit0)
       (за-умовою
         ((тотожне? (перше (решта bits)) bit1)
          (тотожне?
            (перше (решта (решта bits)))
            bit2))
         ((native-first-domain-true ())
          (native-first-domain-false ()))))
      ((native-first-domain-true ())
       (native-first-domain-false ())))))

(визначити native-first-domain-d3-car?
  (функція (shape-or-empty value)
    (native-first-domain-key3-shape?
      (shape-or-empty value)
      (native-first-domain-true ())
      (native-first-domain-false ())
      (native-first-domain-false ()))))

(визначити native-first-domain-d3-cons?
  (функція (shape-or-empty value)
    (native-first-domain-key3-shape?
      (shape-or-empty value)
      (native-first-domain-true ())
      (native-first-domain-true ())
      (native-first-domain-true ()))))

(визначити native-first-plan-domain-cons-argument
  (функція (shape-or-empty expression argument)
    (за-умовою
      ((атом? argument)
       (native-first-fallback expression))
      ((native-first-domain-d3-cons? shape-or-empty (перше argument))
       (native-first-plan-car-cons-u64 expression argument))
      ((native-first-domain-true ())
       (native-first-fallback expression)))))

(визначити native-first-plan-domain-car
  (функція (shape-or-empty expression)
    (за-умовою
      ((атом? (решта expression))
       (native-first-fallback expression))
      ((атом? (решта (решта expression)))
       (за-умовою
         ((тотожне? (решта (решта expression)) ())
          (native-first-plan-domain-cons-argument
            shape-or-empty
            expression
            (перше (решта expression))))
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
