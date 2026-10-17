; D9 justified/vec/arglist — self-DEFINE + 8× D1:1
(0011 створити-обґрунтований
  (0010 (факт підтримка)
    (111 факт (111 підтримка (001 ())))))
(0011 обрізати-обґрунтування
  (0010 (список)
    (відсіяти
      (0010 (пара) (not? (0101 (011 пара))))
      список)))
(0011 вектор-з-список
  (0010 (xs) xs))
(0011 аргументи
  (0010 (xs) xs))
(0011 числовий-буфер-довжина довжина)
(0011 рядок-порожній?
  (0010 (s) (0101 s)))
(list
  (equal? (створити-обґрунтований (quote f) (list (quote s)))
          (list (quote f) (list (quote s))))
  (equal? (обрізати-обґрунтування
            (list (list (quote a) (list (quote s)))
                  (list (quote b) (quote ()))))
          (list (list (quote a) (list (quote s)))))
  (equal? (вектор-з-список (list (quote x) (quote y)))
          (list (quote x) (quote y)))
  (equal? (аргументи (list (quote 1) (quote 2)))
          (list (quote 1) (quote 2)))
  (equal? (числовий-буфер-довжина (list (quote a) (quote b)))
          #d24:000000000000000000000010)
  (рядок-порожній? (quote ()))
  (not? (рядок-порожній? (list (quote a))))
  (equal? (вектор-з-список (quote ())) (quote ())))
