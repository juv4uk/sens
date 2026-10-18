; D6:111000/111001 SENS law, рівнодовгі списки, positive + swapped negative.
(список
  (equal? (спарувати-послідовності (quote ()) (quote ())) (quote ()))
  (equal? (розпарувати-пари (quote ())) (список (quote ()) (quote ())))
  (equal? (спарувати-послідовності (список (quote а) (quote б))
                                  (список (quote в) (quote г)))
          (список (сполучити (quote а) (quote в)) (сполучити (quote б) (quote г))))
  (equal? (розпарувати-пари
            (спарувати-послідовності (список (quote а) (quote б))
                                    (список (quote в) (quote г))))
          (список (список (quote а) (quote б)) (список (quote в) (quote г))))
  (хибне? (equal? (розпарувати-пари
                  (спарувати-послідовності (список (quote а) (quote б))
                                          (список (quote в) (quote г))))
                (список (список (quote в) (quote г)) (список (quote а) (quote б))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
(визначити хибне? not?)
