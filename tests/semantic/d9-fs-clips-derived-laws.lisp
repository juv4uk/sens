; D9 FS/CLIPS: вісім точних D1-законів українських поверхонь.
(list
  (equal? (фс-об'єкт-адреси (quote ())) (quote ()))
  (equal? (фс-об'єкт-адреси
            (list (cons (quote адреса-а) (quote вміст-а))))
          (list (quote адреса-а)))
  (equal? (фс-об'єкт-адреси
            (list (cons (quote адреса-а) (quote вміст-а))
                  (cons (quote адреса-б) (quote вміст-б))))
          (list (quote адреса-а) (quote адреса-б)))
  (equal? (clips-змінна-терм (quote ?x))
          (list (quote var) (quote x)))
  (equal? (clips-змінна-терм (quote ?slot))
          (list (quote var) (quote slot)))
  (equal? (clips-шаблон-слот-порядок
            (quote персона)
            (list (cons (quote персона) (list (quote слот-а) (quote слот-б)))))
          (list (quote слот-а) (quote слот-б)))
  (equal? (clips-шаблон-слот-порядок
            (quote відсутнє)
            (list (cons (quote персона) (list (quote слот-а)))))
          (quote ()))
  (equal? (clips-шаблон-слот-порядок
            (quote персона)
            (list (quote пошкоджений)
                  (cons (quote персона) (list (quote слот-а)))))
          (list (quote слот-а))))
