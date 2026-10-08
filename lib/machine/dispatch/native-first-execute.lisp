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

(00001001 native-first-execute-native-plan
  (00001000 (plan)
    ((00001000 (result)
       (00000111
         ((x86-machine-rejected? result)
          (native-first-execution-rejected (00000001 native) result))
         (t
          (native-first-execution-completed (00000001 native) result))))
     (x86-call-admitted-u64
       (native-first-second plan)
       (native-first-third plan)))))

(00001001 native-first-execute-plan
  (00001000 (plan)
    ((00001000 (native-state)
       (00000111
         ((00000011 native-state (00000001 same))
          (00000111
            ((00000011
               (native-first-list-length3-state plan)
               (00000001 same))
             (native-first-execute-native-plan plan))
            (t
             (native-first-execution-rejected
               (00000001 native)
               (native-first-list2
                 (00000001 malformed-native-plan)
                 plan)))))
         (t
          ((00001000 (fallback-state)
             (00000111
               ((00000011 fallback-state (00000001 same))
                (00000111
                  ((00000011
                     (native-first-list-length2-state plan)
                     (00000001 same))
                   (native-first-execution-completed
                     (00000001 evaluator)
                     ; Compatibility seam: exact D4 EVAL callability is a
                     ; separate downstream cut.
                     (01001101 (native-first-second plan))))
                  (t
                   (native-first-execution-rejected
                     (00000001 evaluator)
                     (native-first-list2
                       (00000001 malformed-evaluator-fallback)
                       plan)))))
               (t
                (native-first-execution-rejected
                  (00000001 invalid-plan)
                  (native-first-list2
                    (00000001 unknown-native-first-plan)
                    plan))))))
           (native-first-plan-tag-state
             plan
             (00000001 evaluator-fallback))))))
     (native-first-plan-tag-state
       plan
       (00000001 native-plan)))))

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
