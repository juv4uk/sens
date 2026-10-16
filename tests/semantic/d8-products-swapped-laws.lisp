; D8:11100001 ZIP-swapped / D8:11100011 UNZIP-swapped (#3710).
; Очікуваний Native PredicateBit вектор (1 1 0); останній — фальсифікатор орієнтації.
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
      (спарувати-послідовності
        (list (quote ліве-а))
        (list (quote праве-а))))
    (list (list (quote праве-а)) (list (quote ліве-а))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки
        (list (quote ліве-а))
        (list (quote праве-а))))
    (list (list (quote праве-а)) (list (quote ліве-а)))))
