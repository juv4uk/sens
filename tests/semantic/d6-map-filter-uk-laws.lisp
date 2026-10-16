; Native D6:101000 MAP / D6:101001 FILTER — six independent D1 verdicts.
; Two explicit wrong-order/wrong-predicate negative witnesses, zero host oracles.
(0011 проба-відобразити
  (0010 (x) (111 (quote м) x)))
(0011 проба-відсіяти
  (0010 (x) (101 x (quote б))))
(list
  (equal? (відобразити проба-відобразити (list (quote а) (quote б)))
          (list (cons (quote м) (quote а)) (cons (quote м) (quote б))))
  (not? (equal? (відобразити проба-відобразити (list (quote а) (quote б)))
                (list (cons (quote м) (quote б)) (cons (quote м) (quote а)))))
  (equal? (відсіяти проба-відсіяти (list (quote а) (quote б) (quote в)))
          (list (quote б)))
  (not? (equal? (відсіяти проба-відсіяти (list (quote а) (quote б) (quote в)))
                (list (quote а))))
  (equal? (відобразити проба-відобразити (quote ())) (quote ()))
  (equal? (відсіяти проба-відсіяти (quote ())) (quote ())))
