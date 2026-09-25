; #506 — Lisp-owned native-first execution bridge.
;
; #505 owns classification only. This file is the mechanical next step:
;   expression -> native-first-plan
;      native-plan        -> closed admission -> Lisp encoder -> raw CPU call
;      evaluator-fallback -> ordinary Lisp eval
;
; Language meaning remains outside this bridge. A plan that has already chosen
; the native route MUST NOT silently retry through the evaluator if admission
; or native mechanism rejects it; doing so would hide machine bugs.
;
; Required layers are loaded by the caller:
;   lib/machine/encoding/x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/admission/x86-64.lisp
;   lib/machine/dispatch/native-first.lisp

(def native-first-execution-completed
  (lambda (route value)
    (list
      (quote execution-route)
      route
      (quote (status completed))
      (list (quote value) value))))

(def native-first-execution-rejected
  (lambda (route detail)
    (list
      (quote execution-route)
      route
      (quote (status rejected))
      (list (quote detail) detail))))

(def native-first-plan-tag-state
  (lambda (plan tag)
    (cond
      ((atom? plan) (structural-kind pair)
       (cond
         ((eq? (car plan) tag) (identity-relation same) (quote same))
         ((eq? (car plan) tag) (identity-relation distinct) (quote distinct))))
      ((quote native-first-plan-tag-state-fallback)
       native-first-plan-tag-state-fallback
       (quote distinct)))))

(def native-first-execute-native-plan
  (lambda (plan)
    (let ((result
            (x86-call-admitted-u64
              (second plan)
              (third plan))))
      (cond
        ((equal? (x86-machine-rejected? result) t)
         (structural-relation same)
         (native-first-execution-rejected (quote native) result))
        ((equal? (x86-machine-rejected? result) t)
         (structural-relation distinct)
         (native-first-execution-completed (quote native) result))))))

(def native-first-execute-plan
  (lambda (plan)
    (let ((native-state
            (native-first-plan-tag-state plan (quote native-plan))))
      (cond
        ((eq? native-state (quote same)) (identity-relation same)
         (cond
           ((equal? (length plan) 3) (structural-relation same)
            (native-first-execute-native-plan plan))
           ((equal? (length plan) 3) (structural-relation distinct)
            (native-first-execution-rejected
              (quote native)
              (list (quote malformed-native-plan) plan)))))
        ((eq? native-state (quote distinct)) (identity-relation same)
         (let ((fallback-state
                 (native-first-plan-tag-state
                   plan
                   (quote evaluator-fallback))))
           (cond
             ((eq? fallback-state (quote same)) (identity-relation same)
              (cond
                ((equal? (length plan) 2) (structural-relation same)
                 (native-first-execution-completed
                   (quote evaluator)
                   (eval (second plan))))
                ((equal? (length plan) 2) (structural-relation distinct)
                 (native-first-execution-rejected
                   (quote evaluator)
                   (list (quote malformed-evaluator-fallback) plan)))))
             ((eq? fallback-state (quote distinct)) (identity-relation same)
              (native-first-execution-rejected
                (quote invalid-plan)
                (list (quote unknown-native-first-plan) plan))))))))))

(def native-first-execute-expression
  (lambda (expression)
    (native-first-execute-plan
      (native-first-plan expression))))

(def native-first-execute-source-forms
  (lambda (forms)
    (cond
      ((atom? forms) (structural-kind empty-list) (quote ()))
      ((atom? forms) (structural-kind atom)
       (list
         (native-first-execution-rejected
           (quote evaluator)
           (list (quote malformed-source-form-tail) forms))))
      ((atom? forms) (structural-kind pair)
       (cons
         (native-first-execute-expression (car forms))
         (native-first-execute-source-forms (cdr forms)))))))

(def native-first-execute-source
  (lambda (source)
    (list
      (quote source-execution)
      (native-first-execute-source-forms
        (read-all source)))))
