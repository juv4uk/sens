; D8:11111101 PAIR — рекурсивне спарювання двох належних списків.
; Вісім нативних D1 свідків: порядок CAR/CDR, межа NIL і два негативи.
; Без прямого D8 виклику, нових кодів або літералів D7 замість сутностей.
(список
  (equal? (пара (quote ()) (quote ())) (quote ()))
  (equal? (пара (список (quote а)) (список (quote б)))
          (список (сполучити (quote а) (quote б))))
  (equal? (пара (список (quote а) (quote б))
                 (список (quote в) (quote г)))
          (список (сполучити (quote а) (quote в))
                (сполучити (quote б) (quote г))))
  (equal? (пара (список (quote а) (quote б) (quote в))
                 (список (quote г) (quote д) (quote е)))
          (список (сполучити (quote а) (quote г))
                (сполучити (quote б) (quote д))
                (сполучити (quote в) (quote е))))
  (equal? (пара (quote ()) (список (quote а))) (quote ()))
  (equal? (пара (список (quote а)) (quote ())) (quote ()))
  (хибне? (equal? (пара (список (quote а)) (список (quote б)))
                (список (сполучити (quote б) (quote а)))))
  (хибне? (equal? (пара (список (quote а) (quote б))
                       (список (quote в) (quote г)))
                (список (сполучити (quote б) (quote в))
                      (сполучити (quote а) (quote г))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
(визначити хибне? not?)
