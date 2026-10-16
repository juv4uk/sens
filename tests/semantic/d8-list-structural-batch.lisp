; D8:10100010 / 01011111 — вісім SENS-власних D1-законів.
(list
  (null? (прибрати-дублікати (quote ())))
  (equal? (прибрати-дублікати (list (quote а) (quote б) (quote а) (quote в)))
          (list (quote б) (quote а) (quote в)))
  (equal? (прибрати-дублікати (list (quote а) (quote а) (quote а)))
          (list (quote а)))
  (equal? (прибрати-дублікати (list (quote а) (quote б)))
          (list (quote а) (quote б)))
  (equal? (прибрати-дублікати
           (прибрати-дублікати (list (quote а) (quote б) (quote а))))
          (прибрати-дублікати (list (quote а) (quote б) (quote а))))
  (null? (останній-хвіст (quote ())))
  (equal? (останній-хвіст (list (quote а) (quote б) (quote в)))
          (list (quote в)))
  (not? (equal? (останній-хвіст (list (quote а) (quote б)))
                (list (quote а)))))
