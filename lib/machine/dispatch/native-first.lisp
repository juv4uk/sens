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
