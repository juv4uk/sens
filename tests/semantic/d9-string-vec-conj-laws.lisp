; D9 string-as-list + vec-conj — self-DEFINE + 8× D1:1
(0011 рядок-решта
  (0010 (s) (011 s)))
(0011 рядок-перший
  (0010 (s) (100 s)))
(0011 рядок-додати append)
(0011 рядок-містить? значення-у-списку?)
(0011 рядок-префікс?
  (0010 (pre s)
    (equal? pre (взяти (довжина pre) s))))
(0011 рядок-зріз
  (0010 (s start end)
    (взяти (відняти end start) (відкинути start s))))
(0011 вектор-додати
  (0010 (v x)
    (append v (list x))))
(list
  (equal? (рядок-перший (list (quote a) (quote b))) (quote a))
  (equal? (рядок-решта (list (quote a) (quote b))) (list (quote b)))
  (equal? (рядок-додати (list (quote a)) (list (quote b)))
          (list (quote a) (quote b)))
  (рядок-містить? (quote b) (list (quote a) (quote b)))
  (рядок-префікс? (list (quote a)) (list (quote a) (quote b)))
  (not? (рядок-префікс? (list (quote b)) (list (quote a) (quote b))))
  (equal? (рядок-зріз (list (quote a) (quote b) (quote c))
                      #d24:000000000000000000000001
                      #d24:000000000000000000000011)
          (list (quote b) (quote c)))
  (equal? (вектор-додати (list (quote a)) (quote b))
          (list (quote a) (quote b))))
