; D8:11100001 ZIP-swapped / D8:11100011 UNZIP-swapped
; Ratified D8 coordinates; derived functions built from D6 ZIP/UNZIP (#3710).
; Expected exact D1 witness vector: (1 1 0); last bit falsifies wrong orientation.
(list
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки
        (list (quote ліве-а) (quote ліве-б))
        (list (quote праве-а) (quote праве-б))))
    (list
      (list (quote ліве-а) (quote ліве-б))
      (list (quote праве-а) (quote праве-б))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки (list) (list)))
    (list (list) (list)))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки
        (list (quote ліве-а))
        (list (quote праве-а))))
    (list
      (list (quote праве-а))
      (list (quote ліве-а)))))
