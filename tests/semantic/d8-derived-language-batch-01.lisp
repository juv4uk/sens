; D8:00010110, 00001001, 00111010, 00110110 native SENS projection laws.
; Explicit positive / negative results, no new D8 direct call-head admission.
(list
  (equal? (розвернути-й-приєднати (list (quote а) (quote б)) (list (quote в)))
          (list (quote б) (quote а) (quote в)))
  (not? (equal? (розвернути-й-приєднати (list (quote а) (quote б)) (list (quote в)))
                (list (quote а) (quote б) (quote в))))
  (підмножина? (quote ()) (list (quote а)))
  (підмножина? (list (quote а) (quote в)) (list (quote в) (quote б) (quote а)))
  (not? (підмножина? (list (quote а) (quote г)) (list (quote а) (quote в))))
  (equal? (різниця-множин (list (quote а) (quote б) (quote в)) (list (quote б)))
          (list (quote а) (quote в)))
  (equal? (різниця-множин (quote ()) (list (quote б))) (quote ()))
  (not? (equal? (різниця-множин (list (quote а) (quote б)) (list (quote б)))
                (list (quote а) (quote б))))
  (equal? (приєднати-якщо-нема (quote а) (list (quote б)))
          (list (quote а) (quote б)))
  (equal? (приєднати-якщо-нема (quote а) (list (quote а) (quote б)))
          (list (quote а) (quote б))))
