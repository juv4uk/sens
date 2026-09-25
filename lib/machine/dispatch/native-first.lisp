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

(def native-first-fallback
  (lambda (expression)
    (list (quote evaluator-fallback) expression)))

(def native-first-native-plan
  (lambda (forms arena-bytes)
    (list (quote native-plan) forms arena-bytes)))

(def native-first-plan-car-cons-u64
  (lambda (expression cons-expression)
    (let ((cons-arguments (cdr cons-expression)))
      (cond
        ((atom? cons-arguments) (structural-kind pair)
         (let ((rest-after-left (cdr cons-arguments)))
           (cond
             ((atom? rest-after-left) (structural-kind pair)
              (let ((rest-after-right (cdr rest-after-left)))
                (cond
                  ((atom? rest-after-right) (structural-kind empty-list)
                   (let ((typed-left (x86-as-u64-imm (car cons-arguments))))
                     (cond
                       ((eq? (car typed-left) (quote u64-imm))
                        (identity-relation same)
                        (let ((typed-right (x86-as-u64-imm (car rest-after-left))))
                          (cond
                            ((eq? (car typed-right) (quote u64-imm))
                             (identity-relation same)
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

(def native-first-plan-car-argument
  (lambda (expression argument)
    (cond
      ((atom? argument) (structural-kind pair)
       (let ((head (car argument)))
         (cond
           ((atom? head) (structural-kind empty-list)
            (native-first-fallback expression))
           ((atom? head) (structural-kind pair)
            (native-first-fallback expression))
           ((atom? head) (structural-kind atom)
            (cond
              ((eq? head (quote cons)) (identity-relation same)
               (native-first-plan-car-cons-u64 expression argument))
              ((eq? head (quote cons)) (identity-relation distinct)
               (native-first-fallback expression)))))))
      ((quote native-first-fallback)
       native-first-fallback
       (native-first-fallback expression)))))

(def native-first-plan-car
  (lambda (expression)
    (let ((arguments (cdr expression)))
      (cond
        ((atom? arguments) (structural-kind pair)
         (cond
           ((atom? (cdr arguments)) (structural-kind empty-list)
            (native-first-plan-car-argument expression (car arguments)))
           ((quote native-first-fallback)
            native-first-fallback
            (native-first-fallback expression))))
        ((quote native-first-fallback)
         native-first-fallback
         (native-first-fallback expression))))))

(def native-first-plan
  (lambda (expression)
    (cond
      ((atom? expression) (structural-kind pair)
       (let ((head (car expression)))
         (cond
           ((atom? head) (structural-kind empty-list)
            (native-first-fallback expression))
           ((atom? head) (structural-kind pair)
            (native-first-fallback expression))
           ((atom? head) (structural-kind atom)
            (cond
              ((eq? head (quote car)) (identity-relation same)
               (native-first-plan-car expression))
              ((eq? head (quote car)) (identity-relation distinct)
               (native-first-fallback expression)))))))
      ((quote native-first-fallback)
       native-first-fallback
       (native-first-fallback expression)))))
