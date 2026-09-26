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

(00001001 native-first-execution-completed
  (00001000 (route value)
    (list
      (00000001 execution-route)
      route
      (00000001 (status completed))
      (list (00000001 value) value))))

(00001001 native-first-execution-rejected
  (00001000 (route detail)
    (list
      (00000001 execution-route)
      route
      (00000001 (status rejected))
      (list (00000001 detail) detail))))

(00001001 native-first-plan-tag-state
  (00001000 (plan tag)
    (00000111
      ((00000010 plan) (structural-kind pair)
       (00000111
         ((00000011 (00000101 plan) tag) (identity-relation same) (00000001 same))
         ((00000011 (00000101 plan) tag) (identity-relation distinct) (00000001 distinct))))
      ((00000001 native-first-plan-tag-state-fallback)
       native-first-plan-tag-state-fallback
       (00000001 distinct)))))

(00001001 native-first-execute-native-plan
  (00001000 (plan)
    (let ((result
            (x86-call-admitted-u64
              (second plan)
              (third plan))))
      (00000111
        ((equal? (x86-machine-rejected? result) t)
         (structural-relation same)
         (native-first-execution-rejected (00000001 native) result))
        ((equal? (x86-machine-rejected? result) t)
         (structural-relation distinct)
         (native-first-execution-completed (00000001 native) result))))))

(00001001 native-first-execute-plan
  (00001000 (plan)
    (let ((native-state
            (native-first-plan-tag-state plan (00000001 native-plan))))
      (00000111
        ((00000011 native-state (00000001 same)) (identity-relation same)
         (00000111
           ((equal? (length plan) 3) (structural-relation same)
            (native-first-execute-native-plan plan))
           ((equal? (length plan) 3) (structural-relation distinct)
            (native-first-execution-rejected
              (00000001 native)
              (list (00000001 malformed-native-plan) plan)))))
        ((00000011 native-state (00000001 distinct)) (identity-relation same)
         (let ((fallback-state
                 (native-first-plan-tag-state
                   plan
                   (00000001 evaluator-fallback))))
           (00000111
             ((00000011 fallback-state (00000001 same)) (identity-relation same)
              (00000111
                ((equal? (length plan) 2) (structural-relation same)
                 (native-first-execution-completed
                   (00000001 evaluator)
                   (eval (second plan))))
                ((equal? (length plan) 2) (structural-relation distinct)
                 (native-first-execution-rejected
                   (00000001 evaluator)
                   (list (00000001 malformed-evaluator-fallback) plan)))))
             ((00000011 fallback-state (00000001 distinct)) (identity-relation same)
              (native-first-execution-rejected
                (00000001 invalid-plan)
                (list (00000001 unknown-native-first-plan) plan))))))))))

(00001001 native-first-execute-expression
  (00001000 (expression)
    (native-first-execute-plan
      (native-first-plan expression))))

(00001001 native-first-execute-source-forms
  (00001000 (forms)
    (00000111
      ((00000010 forms) (structural-kind empty-list) (00000001 ()))
      ((00000010 forms) (structural-kind atom)
       (list
         (native-first-execution-rejected
           (00000001 evaluator)
           (list (00000001 malformed-source-form-tail) forms))))
      ((00000010 forms) (structural-kind pair)
       (00000100
         (native-first-execute-expression (00000101 forms))
         (native-first-execute-source-forms (00000110 forms)))))))

(00001001 native-first-execute-source
  (00001000 (source)
    (list
      (00000001 source-execution)
      (native-first-execute-source-forms
        (read-all source)))))
