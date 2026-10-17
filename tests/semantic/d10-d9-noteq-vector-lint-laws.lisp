; D10 not-equal/vector + D9 dependents/lint — self-DEFINE + 8× D1:1
(0011 числа-нерівні?
  (0010 (a b) (not? (equal? a b))))
(0011 вектор->список
  (0010 (v) v))
(0011 список->вектор
  (0010 (xs) xs))
(0011 зріз-вектора
  (0010 (v start end)
    (взяти (відняти end start) (відкинути start v))))
(0011 список-усіх-значень
  (0010 (xs) xs))
(0011 аналіз-розмір довжина)
(list
  (числа-нерівні? #d24:000000000000000000000001
                  #d24:000000000000000000000010)
  (not? (числа-нерівні? #d24:000000000000000000000001
                        #d24:000000000000000000000001))
  (equal? (вектор->список (list (quote a) (quote b)))
          (list (quote a) (quote b)))
  (equal? (список->вектор (list (quote x)))
          (list (quote x)))
  (equal? (зріз-вектора (list (quote a) (quote b) (quote c))
                        #d24:000000000000000000000001
                        #d24:000000000000000000000011)
          (list (quote b) (quote c)))
  (equal? (список-усіх-значень (list (quote v)))
          (list (quote v)))
  (equal? (аналіз-розмір (list (quote a) (quote b) (quote c)))
          #d24:000000000000000000000011)
  (equal? (вектор->список (quote ())) (quote ())))
