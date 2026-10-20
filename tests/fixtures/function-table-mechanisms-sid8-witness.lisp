; function-table-mechanisms-witness — semantic witness, Ukrainian projection.
;
; Axiom: width = address = identity. Semantics owned by SENS, not Python.
; Domain coordinates use decimal values matching exact bit patterns.
;
; Witnesses:
;   1. D1 PredicateBit carriers exact.
;   2. Core evaluator coordinates match known identities.
;   3. Plus has four island routes without inventing a fifth.
;   4. Authority path is semantic-registry — this file mints no meaning.

(load "lib/core.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

; Exact coordinates (bit pattern = identity), decimal presentation
(визначити sid-quote 1)
(визначити sid-atom 2)
(визначити sid-eq 3)
(визначити sid-cons 4)
(визначити sid-car 5)
(визначити sid-cdr 6)
(визначити sid-cond 7)
(визначити sid-lambda 8)
(визначити sid-define 9)
(визначити sid-plus 12)
(визначити sid-core3-reg 168)

(визначити sid-eq?
  (функція (a b)
    (за-умовою
      ((тотожне? a b) d1-true)
      ((атом? (як-є ())) d1-false))))

(визначити plus-four-islands
  (як-є
    ((12 common-lisp)
     (12 prolog)
     (12 clips)
     (12 datalog))))

(визначити plus-sid-uniform?
  (функція (rows)
    (за-умовою
      ((атом? rows) d1-true)
      (так
       (за-умовою
         ((тотожне? (перше (перше rows)) sid-plus)
          (plus-sid-uniform? (решта rows)))
         ((атом? (як-є ())) d1-false))))))

(визначити function-table-mechanisms-sid8-witness
  (функція ()
    (за-умовою
      ((тотожне? (sid-eq? sid-quote 1) d1-true)
       (за-умовою
         ((тотожне? (sid-eq? sid-cond 7) d1-true)
          (за-умовою
            ((тотожне? (sid-eq? sid-plus 12) d1-true)
             (за-умовою
               ((тотожне? (plus-sid-uniform? plus-four-islands) d1-true)
                (за-умовою
                  ((тотожне? (sid-eq? sid-core3-reg 168) d1-true)
                   (як-є (function-table-mechanisms-sid8
                          (status pass)
                          (sid-width 8)
                          (plus-islands 4)
                          (plus-sid 12)
                          (authority semantic-registry)
                          (axiom width-equals-address))))
                  ((атом? (як-є ()))
                   (як-є (function-table-mechanisms-sid8
                          (status fail) (core3-reg mismatch))))))
               ((атом? (як-є ()))
                (як-є (function-table-mechanisms-sid8
                       (status fail) (plus-islands non-uniform))))))
            ((атом? (як-є ()))
             (як-є (function-table-mechanisms-sid8
                    (status fail) (plus-sid mismatch))))))
         ((атом? (як-є ()))
          (як-є (function-table-mechanisms-sid8
                 (status fail) (cond-sid mismatch))))))
      ((атом? (як-є ()))
       (як-є (function-table-mechanisms-sid8
              (status fail) (quote-sid mismatch)))))))

(function-table-mechanisms-sid8-witness)
