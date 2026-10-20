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

(визначити предикат-так (атом? (як-є ())))
(визначити предикат-ні (тотожне? (як-є (0)) (як-є (1))))

; D4 surfaces by name (not old 4-bit tags as call heads)
(визначити голова-функція (як-є функція))
(визначити голова-визначити (як-є визначити))

(визначити тотожність-голови-функції?
  (функція (значення)
    (за-умовою
      ((тотожне? значення голова-функція) предикат-так)
      ((атом? (як-є ())) предикат-ні))))

(визначити тотожність-голови-визначити?
  (функція (значення)
    (за-умовою
      ((тотожне? значення голова-визначити) предикат-так)
      ((атом? (як-є ())) предикат-ні))))

(визначити гілка-так-є-предикатом-д1?
  (функція ()
    (за-умовою
      ((тотожне? (як-є no) (як-є yes)) предикат-ні)
      ((атом? (як-є ())) предикат-так))))

(визначити macro-d4-identity-witness
  (функція ()
    (за-умовою
      ((тотожне? (тотожність-голови-функції? (як-є функція)) предикат-так)
       (за-умовою
         ((тотожне? (тотожність-голови-визначити? (як-є визначити)) предикат-так)
          (за-умовою
            ((тотожне? (гілка-так-є-предикатом-д1?) предикат-так)
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
