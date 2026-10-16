; BATCH: extract from lib/domains/d5.lisp + d6.lisp — pure D3 CAR/CDR compositions.
; Not new semantic laws. Insert into lib/core4.lisp before D6 selector family.
; Then set tests/semantic/d5-uk-projection-laws.lisp to 10 D1:1 and CI expect
; (1 1 1 1 1 1 1 1 1 1). Land core4 + laws + ci in ONE commit (fasl freshness).

; === D5:01100..01111, 10000..10011 ===
; cdaar (р-п-п) D5:01100
(0011 р-п-п
  (0010 (x)
    (100 (100 (011 x)))))

; cdadr (р-п-р) D5:01101
(0011 р-п-р
  (0010 (x)
    (011 (100 (011 x)))))

; cddar (р-р-п) D5:01110
(0011 р-р-п
  (0010 (x)
    (100 (011 (011 x)))))

; cdddr (р-р-р) D5:01111
(0011 р-р-р
  (0010 (x)
    (011 (011 (011 x)))))

; caaar (п-п-п) D5:10000
(0011 п-п-п
  (0010 (x)
    (100 (100 (100 x)))))

; caadr (п-п-р) D5:10001
(0011 п-п-р
  (0010 (x)
    (011 (100 (100 x)))))

; cadar (п-р-п) D5:10010
(0011 п-р-п
  (0010 (x)
    (100 (011 (100 x)))))

; caddr (п-р-р) D5:10011
(0011 п-р-р
  (0010 (x)
    (011 (011 (100 x)))))

; === D6:100111 missing completion ===
; cadddr (п-р-р-р) D6:100111
(0011 п-р-р-р
  (0010 (x)
    (011 (011 (011 (100 x))))))

; Witnesses for laws fixture (append to list, expect 10 ones):
; (equal? (п-р-р (list (quote а) (quote б) (quote в))) (quote в))
; (equal? (р-п-п (list (list (list (quote в) (quote б)) (quote а)))) (quote в))
