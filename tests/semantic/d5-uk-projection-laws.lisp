; D5 structural + ZEROP (selectors already covered by d3-d6-28-native.bits).
; Очікується рівно вісім предикатів D1:1 — CI vector; exact D5 CADDR/CDAAR in 28-law suite.
(list
  (equal? (зворот (list (quote ()) (list (quote ()))))
          (list (list (quote ())) (quote ())))
  (значення-у-списку? (quote ()) (list (quote ())))
  (not? (значення-у-списку?
          (list (quote ())) (list (quote ()))))
  (equal? (знайти-за-ключем (quote ())
            (list (cons (quote ()) (list (quote ())))))
          (cons (quote ()) (list (quote ()))))
  (equal? (замінити (quote змінене) (quote попереднє)
            (list (quote попереднє) (list (quote попереднє))))
          (list (quote змінене) (list (quote змінене))))
  (equal? (зворот (зворот (list (quote ()) (list (quote ())))))
          (list (quote ()) (list (quote ()))))
  (нуль? #d24:000000000000000000000000)
  (not? (нуль? #d24:000000000000000000000001)))
