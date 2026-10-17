; D10 sassoc/vector-string/count/proper-list — self-DEFINE + 8× D1:1
(0011 пошук-асоціації знайти-за-ключем)
(0011 вектор->рядок
  (0010 (v) v))
(0011 рядок->вектор
  (0010 (s) s))
(0011 масив-у-список
  (0010 (a) a))
(0011 кількість-результатів довжина)
(0011 правильний-список-знань? список?)
(0011 правильний-список-результатів? список?)
(list
  (equal? (пошук-асоціації (quote k)
                           (list (list (quote k) (quote v))))
          (list (quote k) (quote v)))
  (equal? (вектор->рядок (list (quote a) (quote b)))
          (list (quote a) (quote b)))
  (equal? (рядок->вектор (list (quote x)))
          (list (quote x)))
  (equal? (масив-у-список (list (quote 1) (quote 2)))
          (list (quote 1) (quote 2)))
  (equal? (кількість-результатів (list (quote a) (quote b) (quote c)))
          #d24:000000000000000000000011)
  (правильний-список-знань? (list (quote a)))
  (правильний-список-результатів? (list (quote r)))
  (equal? (кількість-результатів (quote ()))
          #d24:000000000000000000000000))
