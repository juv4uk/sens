; D8:11100001 ZIP-swapped / D8:11100011 UNZIP-swapped
; Ratified D8 coordinates; derived functions built from D6 ZIP/UNZIP (#3710).
; Expected exact D1 witness vector: (1 1 0); last bit falsifies wrong orientation.
(список
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки
        (список (quote ліве-а) (quote ліве-б))
        (список (quote праве-а) (quote праве-б))))
    (список
      (список (quote ліве-а) (quote ліве-б))
      (список (quote праве-а) (quote праве-б))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки (список) (список)))
    (список (список) (список)))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки
        (список (quote ліве-а))
        (список (quote праве-а))))
    (список
      (список (quote праве-а))
      (список (quote ліве-а)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
