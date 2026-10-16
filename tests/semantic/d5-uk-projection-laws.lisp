; D5:10100 / 11100 / 11101 / 11111 — чотири власні SENS-визначення.
; Людська українська проєкція цього тесту; фізична D5 callability
; залишається окремою вимогою. Очікується рівно (1 1 1 1 1 1).
; Усі значення нижче — структурні дані, не десяткові коди функцій.
(list
  (equal? (зворот (list (quote ()) (list (quote ()))))
          (list (list (quote ())) (quote ())))
  (значення-у-списку? (quote ()) (list (quote ())))
  (not? (значення-у-списку?
          (list (quote ())) (list (quote ()))))
  (equal? (знайти-за-ключем (quote ())
            (list (cons (quote ()) (list (quote ())))))
          (cons (quote ()) (list (quote ()))))
  (equal? (замінити (list (quote ())) (quote ())
            (list (quote ()) (list (quote ()))))
          (list (list (quote ())) (list (list (quote ())))))
  (equal? (зворот (зворот (list (quote ()) (list (quote ())))))
          (list (quote ()) (list (quote ())))))
