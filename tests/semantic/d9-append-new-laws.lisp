; D9 APPEND-NEW — self-DEFINE + 8× D1:1
(0011 додати-нові
  (0010 (xs ys)
    (append xs
            (відсіяти
              (0010 (y) (not? (значення-у-списку? y xs)))
              ys))))
(list
  (equal? (додати-нові (list (quote а)) (list (quote б)))
          (list (quote а) (quote б)))
  (equal? (додати-нові (list (quote а)) (list (quote а)))
          (list (quote а)))
  (equal? (додати-нові (quote ()) (list (quote x)))
          (list (quote x)))
  (equal? (додати-нові (list (quote a) (quote b))
                       (list (quote b) (quote c)))
          (list (quote a) (quote b) (quote c)))
  (equal? (додати-нові (quote ()) (quote ()))
          (quote ()))
  (not? (equal? (додати-нові (list (quote а)) (list (quote б)))
                (list (quote б))))
  (equal? (додати-нові (list (quote x) (quote y))
                       (list (quote x)))
          (list (quote x) (quote y)))
  (equal? (додати-нові (list (quote 1))
                       (list (quote 2) (quote 1) (quote 3)))
          (list (quote 1) (quote 2) (quote 3))))
