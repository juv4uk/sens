; Орієнтація D8:11100001/11100011 від D6:111000/111001.
; Незалежні позитиви/негативи: swap лише одного боку НЕ зберігає добуток.
(list
  (equal?
    (спарувати-навпаки
      (list (quote а) (quote б)) (list (quote х) (quote у)))
    (спарувати-послідовності
      (list (quote х) (quote у)) (list (quote а) (quote б))))
  (хибне? (equal?
    (спарувати-навпаки
      (list (quote а) (quote б)) (list (quote х) (quote у)))
    (спарувати-послідовності
      (list (quote а) (quote б)) (list (quote х) (quote у)))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки
        (list (quote а) (quote б)) (list (quote х) (quote у))))
    (list (list (quote а) (quote б)) (list (quote х) (quote у))))
  (хибне? (equal?
    (розпарувати-пари
      (спарувати-навпаки
        (list (quote а) (quote б)) (list (quote х) (quote у))))
    (list (list (quote а) (quote б)) (list (quote х) (quote у)))))
  (хибне? (equal?
    (розпарувати-навпаки
      (спарувати-послідовності
        (list (quote а) (quote б)) (list (quote х) (quote у))))
    (list (list (quote а) (quote б)) (list (quote х) (quote у)))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки (quote ()) (quote ())))
    (list (quote ()) (quote ())))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки (list (quote а)) (list (quote х))))
    (list (list (quote а)) (list (quote х)))))
