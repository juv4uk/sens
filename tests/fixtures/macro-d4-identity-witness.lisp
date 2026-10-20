; macro-d4-identity-witness — semantic/logic, Ukrainian projection.
;
; Axiom: width = address = identity. Semantics is owned by SENS.
;
; Witnesses:
;   1. D1:1 fallback form is (атом? (як-є ()))
;   2. D4 LAMBDA surface is функція; D4 DEFINE surface is визначити
;   3. macro bootstrap COND is two-field with exact D1 else-branch
;   4. make-macro is substrate tag only — no invented SENS SID

(load "lib/core.lisp")
(load "lib/macro.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

; D4 surfaces by name (not old 4-bit tags as call heads)
(визначити d4-lambda (як-є функція))
(визначити d4-define (як-є визначити))

(визначити d4-lambda-id?
  (функція (x)
    (за-умовою
      ((тотожне? x d4-lambda) d1-true)
      ((атом? (як-є ())) d1-false))))

(визначити d4-define-id?
  (функція (x)
    (за-умовою
      ((тотожне? x d4-define) d1-true)
      ((атом? (як-є ())) d1-false))))

(визначити cond-else-is-d1?
  (функція ()
    (за-умовою
      ((тотожне? (як-є no) (як-є yes)) d1-false)
      ((атом? (як-є ())) d1-true))))

(визначити macro-d4-identity-witness
  (функція ()
    (за-умовою
      ((тотожне? (d4-lambda-id? (як-є функція)) d1-true)
       (за-умовою
         ((тотожне? (d4-define-id? (як-є визначити)) d1-true)
          (за-умовою
            ((тотожне? (cond-else-is-d1?) d1-true)
             (як-є (macro-d4-identity
                    (status pass)
                    (d4-lambda функція)
                    (d4-define визначити)
                    (d1-true (атом? (як-є ())))
                    (cond-else exact-d1))))
            ((атом? (як-є ()))
             (як-є (macro-d4-identity (status fail) (cond-else not-d1))))))
         ((атом? (як-є ()))
          (як-є (macro-d4-identity (status fail) (d4-define mismatch))))))
      ((атом? (як-є ()))
       (як-є (macro-d4-identity (status fail) (d4-lambda mismatch)))))))

(macro-d4-identity-witness)
