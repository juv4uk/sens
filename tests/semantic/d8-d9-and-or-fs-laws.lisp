; D8 AND/OR/DIVIDE + D9 FS projections — self-DEFINE + 8× D1:1
(0011 та and)
(0011 або or)
(0011 поділити quotient)
(0011 значення-списком
  (0010 (xs) xs))
(0011 фс-порожній
  (0010 () (quote ())))
(0011 фс-містить?
  (0010 (ключ мапа)
    (not? (0101 (знайти-за-ключем ключ мапа)))))
(0011 фс-список
  (0010 (fs) fs))
(0011 мапа-факт-від
  (0010 (ключ мапа)
    (110
      ((0101 (знайти-за-ключем ключ мапа)) (quote ()))
      ((0100 (0101 (знайти-за-ключем ключ мапа)))
       (011 (знайти-за-ключем ключ мапа))))))
(list
  (та (equal? (quote a) (quote a)) (equal? (quote b) (quote b)))
  (not? (та (equal? (quote a) (quote a)) (equal? (quote a) (quote b))))
  (або (equal? (quote a) (quote b)) (equal? (quote a) (quote a)))
  (equal? (поділити #d24:000000000000000000001000
                    #d24:000000000000000000000010)
          #d24:000000000000000000000100)
  (equal? (значення-списком (list (quote x))) (list (quote x)))
  (equal? (фс-порожній) (quote ()))
  (фс-містить? (quote k) (list (list (quote k) (quote v))))
  (equal? (фс-список (list (quote a))) (list (quote a))))
