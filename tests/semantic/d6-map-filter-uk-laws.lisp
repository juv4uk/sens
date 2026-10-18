; Native D6:101000 MAP / D6:101001 FILTER — six independent D1 verdicts.
; Two explicit wrong-order/wrong-predicate negative witnesses, zero host oracles.
(0011 проба-відобразити
  (0010 (x) (111 (quote м) x)))
(0011 проба-відсіяти
  (0010 (x) (101 x (quote б))))
(список
  (equal? (відобразити проба-відобразити (список (quote а) (quote б)))
          (список (сполучити (quote м) (quote а)) (сполучити (quote м) (quote б))))
  (хибне? (equal? (відобразити проба-відобразити (список (quote а) (quote б)))
                (список (сполучити (quote м) (quote б)) (сполучити (quote м) (quote а)))))
  (equal? (відсіяти проба-відсіяти (список (quote а) (quote б) (quote в)))
          (список (quote б)))
  (хибне? (equal? (відсіяти проба-відсіяти (список (quote а) (quote б) (quote в)))
                (список (quote а))))
  (equal? (відобразити проба-відобразити (quote ())) (quote ()))
  (equal? (відсіяти проба-відсіяти (quote ())) (quote ())))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
(визначити хибне? not?)
