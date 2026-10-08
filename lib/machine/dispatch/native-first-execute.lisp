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
; This file is loaded through load-mixed-exact-domain. Current D3/D4 heads are
; exact domain identities; the remaining EVAL/READ-ALL seams stay compatibility
; mechanisms until their own current-domain owners migrate them.
;
; Required layers are loaded by the caller:
;   lib/machine/encoding/x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/admission/x86-64.lisp
;   lib/machine/dispatch/native-first.lisp

(0011 native-first-execution-completed
  (0010 (route value)
    (1110
      (001 execution-route)
      route
      (001 (status completed))
      (1110 (001 value) value))))

(0011 native-first-execution-rejected
  (0010 (route detail)
    (1110
      (001 execution-route)
      route
      (001 (status rejected))
      (1110 (001 detail) detail))))

(0011 native-first-proper-list-length-2?
  (0010 (value)
    (110
      ((010 value)
       (native-first-domain-false ()))
      ((010 (011 value))
       (native-first-domain-false ()))
      ((101 (011 (011 value)) ())
       (native-first-domain-true ()))
      ((native-first-domain-true ())
       (native-first-domain-false ())))))

(0011 native-first-proper-list-length-3?
  (0010 (value)
    (110
      ((010 value)
       (native-first-domain-false ()))
      ((010 (011 value))
       (native-first-domain-false ()))
      ((010 (011 (011 value)))
       (native-first-domain-false ()))
      ((101 (011 (011 (011 value))) ())
       (native-first-domain-true ()))
      ((native-first-domain-true ())
       (native-first-domain-false ())))))

(0011 native-first-plan-tag-state
  (0010 (plan tag)
    (110
      ((010 plan)
       (001 distinct))
      ((101 (100 plan) tag)
       (001 same))
      ((native-first-domain-true ())
       (001 distinct)))))

(0011 native-first-execute-native-plan
  (0010 (plan)
    ((0010 (result)
       (110
         ((101 (x86-machine-rejected? result) t)
          (native-first-execution-rejected (001 native) result))
         ((native-first-domain-true ())
          (native-first-execution-completed (001 native) result))))
     (x86-call-admitted-u64
       (100 (011 plan))
       (100 (011 (011 plan)))))))

(0011 native-first-execute-plan
  (0010 (plan)
    ((0010 (native-state)
       (110
         ((101 native-state (001 same))
          (110
            ((native-first-proper-list-length-3? plan)
             (native-first-execute-native-plan plan))
            ((native-first-domain-true ())
             (native-first-execution-rejected
               (001 native)
               (1110 (001 malformed-native-plan) plan)))))
         ((101 native-state (001 distinct))
          ((0010 (fallback-state)
             (110
               ((101 fallback-state (001 same))
                (110
                  ((native-first-proper-list-length-2? plan)
                   (native-first-execution-completed
                     (001 evaluator)
                     (01001101 (100 (011 plan)))))
                  ((native-first-domain-true ())
                   (native-first-execution-rejected
                     (001 evaluator)
                     (1110 (001 malformed-evaluator-fallback) plan)))))
               ((101 fallback-state (001 distinct))
                (native-first-execution-rejected
                  (001 invalid-plan)
                  (1110 (001 unknown-native-first-plan) plan)))))
           (native-first-plan-tag-state
             plan
             (001 evaluator-fallback))))))
     (native-first-plan-tag-state plan (001 native-plan)))))

(0011 native-first-execute-expression
  (0010 (expression)
    (native-first-execute-plan
      (native-first-plan expression))))

(0011 native-first-execute-source-forms
  (0010 (forms)
    (110
      ((101 forms ())
       (001 ()))
      ((010 forms)
       (1110
         (native-first-execution-rejected
           (001 evaluator)
           (1110 (001 malformed-source-form-tail) forms))))
      ((native-first-domain-true ())
       (111
         (native-first-execute-expression (100 forms))
         (native-first-execute-source-forms (011 forms)))))))

(0011 native-first-execute-source
  (0010 (source)
    (1110
      (001 source-execution)
      (native-first-execute-source-forms
        (01001011 source)))))
