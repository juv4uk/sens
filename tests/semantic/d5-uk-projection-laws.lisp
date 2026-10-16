; D5:10100 / 11100 / 11101 / 11111 — чотири власні SENS-визначення плюс D5:01000.
; Людська українська проєкція цього тесту; фізична D5 callability
; залишається окремою вимогою. Очікується рівно вісім предикатів D1:1.
; Структурні дані нижче — не коди функцій. Для SUBST окремі D7-атоми.
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
  (0100 (нуль? #d24:000000000000000000000001)))
