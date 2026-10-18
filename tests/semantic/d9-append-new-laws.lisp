; D9 APPEND-NEW — self-DEFINE + 8× D1:1
(0011 додати-нові
  (0010 (xs ys)
    (приєднати xs
            (відсіяти
              (функція (y) (хибне? (значення-у-списку? y xs)))
              ys))))
(список
  (equal? (додати-нові (список (quote а)) (список (quote б)))
          (список (quote а) (quote б)))
  (equal? (додати-нові (список (quote а)) (список (quote а)))
          (список (quote а)))
  (equal? (додати-нові (quote ()) (список (quote x)))
          (список (quote x)))
  (equal? (додати-нові (список (quote a) (quote b))
                       (список (quote b) (quote c)))
          (список (quote a) (quote b) (quote c)))
  (equal? (додати-нові (quote ()) (quote ()))
          (quote ()))
  (хибне? (equal? (додати-нові (список (quote а)) (список (quote б)))
                (список (quote б))))
  (equal? (додати-нові (список (quote x) (quote y))
                       (список (quote x)))
          (список (quote x) (quote y)))
  (equal? (додати-нові (список (quote 1))
                       (список (quote 2) (quote 1) (quote 3)))
          (список (quote 1) (quote 2) (quote 3))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити приєднати append)
(визначити список list)
(визначити хибне? not?)
