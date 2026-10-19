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

(визначити native-first-list-2
  (функція (a b)
    (сполучити a (сполучити b (як-є ())))))

(визначити native-first-list-4
  (функція (a b c d)
    (сполучити a (сполучити b (сполучити c (сполучити d (як-є ())))))))

(визначити native-first-execution-completed
  (функція (route value)
    (native-first-list-4
      (як-є execution-route)
      route
      (як-є (status completed))
      (native-first-list-2 (як-є value) value))))

(визначити native-first-execution-rejected
  (функція (route detail)
    (native-first-list-4
      (як-є execution-route)
      route
      (як-є (status rejected))
      (native-first-list-2 (як-є detail) detail))))

(визначити native-first-proper-list-length-2?
  (функція (value)
    (за-умовою
      ((атом? value)
       ні)
      ((атом? (решта value))
       ні)
      ((порожній? (решта (решта value)))
       так)
      (так
       ні))))

(визначити native-first-proper-list-length-3?
  (функція (value)
    (за-умовою
      ((атом? value)
       ні)
      ((атом? (решта value))
       ні)
      ((атом? (решта (решта value)))
       ні)
      ((тотожне? (решта (решта (решта value))) ())
       так)
      (так
       ні))))

(визначити native-first-plan-tag-state
  (функція (plan tag)
    (за-умовою
      ((атом? plan)
       (як-є distinct))
      ((тотожне? (перше plan) tag)
       (як-є same))
      (так
       (як-є distinct)))))

(визначити native-first-execute-native-plan-result
  (функція (plan result)
    (за-умовою
      ((атом? result)
       (native-first-execution-completed (як-є native) result))
      ((тотожне? (перше result) (як-є rejected))
       (native-first-execution-rejected (як-є native) result))
      (так
       (native-first-execution-completed (як-є native) result)))))

(визначити native-first-execute-native-plan
  (функція (plan)
    (native-first-execute-native-plan-result
      plan
      (x86-call-admitted-u64
        (перше (решта plan))
        (перше (решта (решта plan)))))))

(визначити native-first-execute-plan
  (функція (plan)
    (за-умовою
      ((тотожне? (native-first-plan-tag-state plan (як-є native-plan)) (як-є same))
       (за-умовою
         ((native-first-proper-list-length-3? plan)
          (native-first-execute-native-plan plan))
         (так
          (native-first-execution-rejected
            (як-є native)
            (native-first-list-2 (як-є malformed-native-plan) plan)))))
      ((тотожне? (native-first-plan-tag-state plan (як-є native-plan)) (як-є distinct))
       (за-умовою
         ((тотожне? (native-first-plan-tag-state plan (як-є evaluator-fallback)) (як-є same))
          (за-умовою
            ((native-first-proper-list-length-2? plan)
             (native-first-execution-completed
               (як-є evaluator)
               (обчислити (перше (решта plan)))))
            (так
             (native-first-execution-rejected
               (як-є invalid-plan)
               (native-first-list-2
                 (як-є malformed-evaluator-fallback-plan)
                 plan)))))
         ((тотожне? (native-first-plan-tag-state plan (як-є evaluator-fallback)) (як-є distinct))
          (native-first-execution-rejected
            (як-є invalid-plan)
            (native-first-list-2 (як-є unknown-native-first-plan) plan)))
         (так
          (native-first-execution-rejected
            (як-є invalid-plan)
            (native-first-list-2 (як-є malformed-fallback-tag-state) plan)))))
      (так
       (native-first-execution-rejected
         (як-є invalid-plan)
         (native-first-list-2 (як-є unknown-native-first-plan) plan))))))
(визначити native-first-execute-expression
  (функція (expression)
    (native-first-execute-plan
      (native-first-plan expression))))

(визначити native-first-execute-source-forms
  (функція (forms)
    (за-умовою
      ((атом? forms)
       (за-умовою
         ((тотожне? forms ())
          (як-є ()))
         (так
          (сполучити
            (native-first-execution-rejected
              (як-є evaluator)
              (native-first-list-2
                (як-є malformed-source-form-tail)
                forms))
            (як-є ())))))
      (так
       (сполучити
         (native-first-execute-expression (перше forms))
         (native-first-execute-source-forms (решта forms)))))))

(визначити native-first-execute-source
  (функція (source)
    (native-first-list-2
      (як-є source-execution)
      (native-first-execute-source-forms
        (читати-всі source)))))