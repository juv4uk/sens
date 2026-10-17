; D9:101011101 VEC-CONJ and D9:001011100 DEPENDENTS-OF.
; Eight D1:YES: list-carrier preservation, ordering, nested element, absent-key
; and a deliberate wrong-order falsifier. No direct 9-bit call head.
(list
  (equal? (вектор-додати (quote ()) (quote а)) (list (quote а)))
  (equal? (вектор-додати (list (quote а) (quote б)) (quote в)) (list (quote а) (quote б) (quote в)))
  (equal? (вектор-додати (list (quote а)) (list (quote б) (quote в))) (list (quote а) (list (quote б) (quote в))))
  (equal? (вектор-список (вектор-додати (list (quote а)) (quote б))) (list (quote а) (quote б)))
  (not? (equal? (вектор-додати (list (quote а)) (quote б)) (list (quote б) (quote а))))
  (equal? (залежні-від (quote ключ) (мапа-вставити (quote ключ) (list (quote а) (quote б)) (quote ()))) (list (list (quote а) (quote б))))
  (equal? (залежні-від (quote відсутній) (мапа-вставити (quote ключ) (quote а) (quote ()))) (quote ()))
  (equal? (залежні-від (quote ключ) (мапа-вставити (quote ключ) (quote а) (quote ()))) (мапа-отримати (quote ключ) (мапа-вставити (quote ключ) (quote а) (quote ())))))
