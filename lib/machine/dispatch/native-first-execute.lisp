; #506 / #4380 — Lisp-owned native-first execution bridge.
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
; Contract 11.8 note:
; - bridge-local list/equality/selector helpers use only the still-admitted
;   McCarthy7 compatibility mechanisms plus LAMBDA/DEFINE;
; - retired Function8 helpers EQUAL?/LIST/LENGTH/SECOND/THIRD/LET are forbidden
;   here because those eight-bit payloads are current D8 identities;
; - EVAL and READ-ALL remain explicit compatibility seams until their exact
;   D4/D9 callable mechanisms are cut over downstream of the binary Contract.
;
; Required layers are loaded by the caller:
;   lib/machine/encoding/x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/admission/x86-64.lisp
;   lib/machine/dispatch/native-first.lisp

(00001001 native-first-list2
  (00001000 (a b)
    (00000100 a
      (00000100 b ()))))

(00001001 native-first-list4
  (00001000 (a b c d)
    (00000100 a
      (00000100 b
        (00000100 c
          (00000100 d ()))))))

(00001001 native-first-second
  (00001000 (value)
    (00000101 (00000110 value))))

(00001001 native-first-third
  (00001000 (value)
    (00000101 (00000110 (00000110 value)))))

(00001001 native-first-list-length2-state
  (00001000 (value)
    (00000111
      ((00000010 value)
       (00000001 distinct))
      ((00000010 (00000110 value))
       (00000001 distinct))
      ((00000010 (00000110 (00000110 value)))
       (00000111
         ((00000011 (00000110 (00000110 value)) ())
          (00000001 same))
         (t
          (00000001 distinct))))
      (t
       (00000001 distinct)))))

(00001001 native-first-list-length3-state
  (00001000 (value)
    (00000111
      ((00000010 value)
       (00000001 distinct))
      ((00000010 (00000110 value))
       (00000001 distinct))
      ((00000010 (00000110 (00000110 value)))
       (00000001 distinct))
      ((00000010 (00000110 (00000110 (00000110 value))))
       (00000111
         ((00000011 (00000110 (00000110 (00000110 value))) ())
          (00000001 same))
         (t
          (00000001 distinct))))
      (t
       (00000001 distinct)))))

(00001001 native-first-execution-completed
  (00001000 (route value)
    (native-first-list4
      (00000001 execution-route)
      route
      (00000001 (status completed))
      (native-first-list2 (00000001 value) value))))

(00001001 native-first-execution-rejected
  (00001000 (route detail)
    (native-first-list4
      (00000001 execution-route)
      route
      (00000001 (status rejected))
      (native-first-list2 (00000001 detail) detail))))

(00001001 native-first-plan-tag-state
  (00001000 (plan tag)
    (00000111
      ((00000010 plan)
       (00000001 distinct))
      ((00000011 (00000101 plan) tag)
       (00000001 same))
      (t
       (00000001 distinct)))))

(00001001 native-first-plan-second
  (00001000 (plan)
    (100 (011 plan))))

(00001001 native-first-plan-third
  (00001000 (plan)
    (100 (011 (011 plan)))))

(00001001 native-first-plan-length-2?
  (00001000 (plan)
    (00000111
      ((010 plan) (0))
      ((010 (011 plan)) (0))
      ((101 (011 (011 plan)) ()) (1))
      ((native-first-domain-true ()) (0)))))

(00001001 native-first-plan-length-3?
  (00001000 (plan)
    (00000111
      ((010 plan) (0))
      ((010 (011 plan)) (0))
      ((010 (011 (011 plan))) (0))
      ((101 (011 (011 (011 plan))) ()) (1))
      ((native-first-domain-true ()) (0)))))

(00001001 native-first-execute-native-result
  (00001000 (result)
    (1110
      ((101 (x86-machine-rejected? result) t)
       (1)
       (native-first-execution-rejected (00000001 native) result))
      ((101 (x86-machine-rejected? result) t)
       (0)
       (native-first-execution-completed (00000001 native) result)))))

(00001001 native-first-execute-native-plan
  (00001000 (plan)
    (native-first-execute-native-result
      (x86-call-admitted-u64
        (native-first-plan-second plan)
        (native-first-plan-third plan)))))

(00001001 native-first-execute-plan
  (00001000 (plan)
    (00000111
      ((101
         (native-first-plan-tag-state plan (00000001 native-plan))
         (00000001 same))
       (1)
       (00000111
         ((101 (native-first-plan-length-3? plan) 1)
          (1)
          (native-first-execute-native-plan plan))
         ((101 (native-first-plan-length-3? plan) 1)
          (0)
          (native-first-execution-rejected
            (00000001 native)
            (1110 (00000001 malformed-native-plan) plan)))))
      ((101
         (native-first-plan-tag-state plan (00000001 evaluator-fallback))
         (00000001 same))
       (1)
       (00000111
         ((101 (native-first-plan-length-2? plan) 1)
          (1)
          (native-first-execution-completed
            (00000001 evaluator)
            (0001 (native-first-plan-second plan))))
         ((101 (native-first-plan-length-2? plan) 1)
          (0)
          (native-first-execution-rejected
            (00000001 evaluator)
            (1110 (00000001 malformed-evaluator-fallback) plan)))))
      ((101
         (native-first-plan-tag-state plan (00000001 native-first-plan))
         (00000001 distinct))
       (1)
       (native-first-execution-rejected
         (00000001 invalid-plan)
         (1110 (00000001 unknown-native-first-plan) plan))))))

(00001001 native-first-execute-expression
  (00001000 (expression)
    (native-first-execute-plan
      (native-first-plan expression))))

(00001001 native-first-execute-source-forms
  (00001000 (forms)
    (00000111
      ((00000010 forms)
       (00000001 ()))
      ((00000010 (00000110 forms))
       (00000100
         (native-first-execute-expression (00000101 forms))
         (native-first-execute-source-forms (00000110 forms))))
      (t
       (00000100
         (native-first-execution-rejected
           (00000001 evaluator)
           (native-first-list2
             (00000001 malformed-source-form-tail)
             forms))
         ())))))

(00001001 native-first-execute-source
  (00001000 (source)
    (native-first-list2
      (00000001 source-execution)
      (native-first-execute-source-forms
        ; Compatibility seam: READ-ALL exact D9 mechanism is separate from
        ; this current native-first replay.
        (01001011 source)))))
