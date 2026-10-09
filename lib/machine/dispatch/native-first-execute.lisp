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
; The host's existing `load` boundary uses the bounded mixed exact-domain reader.
; Current D3/D4 heads are exact domain identities. D4:1110 LIST is deliberately NOT used here because
; residency does not grant callability; records are built from exact D3 CONS.
; The remaining EVAL/READ-ALL seams stay compatibility mechanisms until their
; own current-domain owners migrate them.
;
; Required layers are loaded by the caller:
;   lib/machine/encoding/x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/admission/x86-64.lisp
;   lib/machine/dispatch/native-first.lisp

(0011 native-first-list-2
  (0010 (a b)
    (111 a (111 b (001 ())))))

(0011 native-first-list-4
  (0010 (a b c d)
    (111 a (111 b (111 c (111 d (001 ())))))))

(0011 native-first-execution-completed
  (0010 (route value)
    (native-first-list-4
      (001 execution-route)
      route
      (001 (status completed))
      (native-first-list-2 (001 value) value))))

(0011 native-first-execution-rejected
  (0010 (route detail)
    (native-first-list-4
      (001 execution-route)
      route
      (001 (status rejected))
      (native-first-list-2 (001 detail) detail))))

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

(0011 native-first-execute-native-plan-result
  (0010 (plan result)
    (110
      ((010 result)
       (native-first-execution-completed (001 native) result))
      ((101 (100 result) (001 rejected))
       (native-first-execution-rejected (001 native) result))
      ((native-first-domain-true ())
       (native-first-execution-completed (001 native) result)))))

(0011 native-first-execute-native-plan
  (0010 (plan)
    (native-first-execute-native-plan-result
      plan
      (x86-call-admitted-u64
        (100 (011 plan))
        (100 (011 (011 plan)))))))

(0011 native-first-execute-plan
  (0010 (plan)
    (110
      ((101 (native-first-plan-tag-state plan (001 native-plan)) (001 same))
       (110
         ((native-first-proper-list-length-3? plan)
          (native-first-execute-native-plan plan))
         ((native-first-domain-true ())
          (native-first-execution-rejected
            (001 native)
            (native-first-list-2 (001 malformed-native-plan) plan)))))
      ((101 (native-first-plan-tag-state plan (001 native-plan)) (001 distinct))
       (110
         ((101 (native-first-plan-tag-state plan (001 evaluator-fallback)) (001 same))
          (110
            ((native-first-proper-list-length-2? plan)
             (native-first-execution-completed
               (001 evaluator)
               (01001101 (100 (011 plan))))
            ((native-first-domain-true ())
             (native-first-execution-rejected
               (001 evaluator)
               (native-first-list-2 (001 malformed-evaluator-fallback) plan)))))
         ((101 (native-first-plan-tag-state plan (001 evaluator-fallback)) (001 distinct))
          (native-first-execution-rejected
            (001 invalid-plan)
            (native-first-list-2 (001 unknown-native-first-plan) plan))
         ((native-first-domain-true ())
          (native-first-execution-rejected
            (001 invalid-plan)
            (native-first-list-2 (001 malformed-fallback-tag-state) plan)))))
      ((native-first-domain-true ())
       (native-first-execution-rejected
         (001 invalid-plan)
         (native-first-list-2 (001 unknown-native-first-plan) plan))))))))

(0011 native-first-execute-expression
  (0010 (expression)
    (native-first-execute-plan
      (native-first-plan expression))))

(0011 native-first-execute-source-forms
  (0010 (forms)
    (110
      ((010 forms)
       (110
         ((101 forms ())
          (001 ()))
         ((native-first-domain-true ())
          (111
            (native-first-execution-rejected
              (001 evaluator)
              (native-first-list-2
                (001 malformed-source-form-tail)
                forms))
            (001 ())))))
      ((native-first-domain-true ())
       (111
         (native-first-execute-expression (100 forms))
         (native-first-execute-source-forms (011 forms)))))))

(0011 native-first-execute-source
  (0010 (source)
    (native-first-list-2
      (001 source-execution)
      (native-first-execute-source-forms
        (01001011 source)))))