; #2286 — pairlis/bind witness. Ukrainian projection.
; Historical PAIRLIS recursive construction and C1-BIND/LOOKUP observations.

(визначити pairlis-hist
  (функція (params args env)
    (за-умовою
      ((тотожне? params (як-є ())) env)
      (так
       (сполучити
         (сполучити (перше params) (перше args))
         (pairlis-hist (решта params) (решта args) env))))))

(pairlis-hist
  (як-є (X Y))
  (як-є (1 2))
  (як-є ((OLD . ENV))))

(спарувати
  (як-є (X Y))
  (як-є (1 2))
  (як-є ((OLD . ENV))))

(знайти-за-ключем
  (як-є X)
  (pairlis-hist
    (як-є (X X))
    (як-є (FIRST SECOND))
    (як-є ())))

(знайти-за-ключем
  (як-є X)
  (спарувати
    (як-є (X X))
    (як-є (FIRST SECOND))
    (як-є ())))

(спарувати
  (як-є ())
  (як-є ())
  (як-є ((OLD . ENV))))

(спарувати
  (як-є (X))
  (як-є (1 2))
  (як-є ()))

(спарувати
  (як-є (X Y))
  (як-є (1))
  (як-є ()))
