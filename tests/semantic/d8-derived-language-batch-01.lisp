; D8:00010110, 00001001, 00111010, 00110110 native SENS projection laws.
; Explicit positive / negative results, no new D8 direct call-head admission.
(список
  (equal? (розвернути-й-приєднати (список (quote а) (quote б)) (список (quote в)))
          (список (quote б) (quote а) (quote в)))
  (хибне? (equal? (розвернути-й-приєднати (список (quote а) (quote б)) (список (quote в)))
                (список (quote а) (quote б) (quote в))))
  (підмножина? (quote ()) (список (quote а)))
  (підмножина? (список (quote а) (quote в)) (список (quote в) (quote б) (quote а)))
  (хибне? (підмножина? (список (quote а) (quote г)) (список (quote а) (quote в))))
  (equal? (різниця-множин (список (quote а) (quote б) (quote в)) (список (quote б)))
          (список (quote а) (quote в)))
  (equal? (різниця-множин (quote ()) (список (quote б))) (quote ()))
  (хибне? (equal? (різниця-множин (список (quote а) (quote б)) (список (quote б)))
                (список (quote а) (quote б))))
  (equal? (приєднати-якщо-нема (quote а) (список (quote б)))
          (список (quote а) (quote б)))
  (equal? (приєднати-якщо-нема (quote а) (список (quote а) (quote б)))
          (список (quote а) (quote б))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
