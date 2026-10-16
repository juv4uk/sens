; D8 00010000, 00101101: вісім законів D1.
(list
  (equal? (різниця-списків (quote ()) (list (quote а))) (quote ()))
  (equal? (різниця-списків (list (quote а) (quote б) (quote а) (quote в)) (list (quote б)))
          (list (quote а) (quote а) (quote в)))
  (equal? (різниця-списків (list (quote а) (quote б)) (quote ())) (list (quote а) (quote б)))
  (equal? (різниця-списків (list (quote а) (quote б)) (list (quote б) (quote а))) (quote ()))
  (equal? (додати-якщо-нема (quote а) (list (quote а) (quote б))) (list (quote а) (quote б)))
  (equal? (додати-якщо-нема (quote в) (list (quote а) (quote б))) (list (quote в) (quote а) (quote б)))
  (equal? (додати-якщо-нема (quote а) (quote ())) (list (quote а)))
  (not? (equal? (додати-якщо-нема (quote в) (list (quote а))) (list (quote а)))))
