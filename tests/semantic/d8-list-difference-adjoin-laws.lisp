; D8 00010000, 00101101: вісім законів D1.
(список
  (equal? (різниця-списків (quote ()) (список (quote а))) (quote ()))
  (equal? (різниця-списків (список (quote а) (quote б) (quote а) (quote в)) (список (quote б)))
          (список (quote а) (quote а) (quote в)))
  (equal? (різниця-списків (список (quote а) (quote б)) (quote ())) (список (quote а) (quote б)))
  (equal? (різниця-списків (список (quote а) (quote б)) (список (quote б) (quote а))) (quote ()))
  (equal? (додати-якщо-нема (quote а) (список (quote а) (quote б))) (список (quote а) (quote б)))
  (equal? (додати-якщо-нема (quote в) (список (quote а) (quote б))) (список (quote в) (quote а) (quote б)))
  (equal? (додати-якщо-нема (quote а) (quote ())) (список (quote а)))
  (хибне? (equal? (додати-якщо-нема (quote в) (список (quote а))) (список (quote а)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
