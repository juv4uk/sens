; D8:01001101 MEMBER-IF, D8:00001000 EQL, D8:01011010 BUTLAST.
; Три Lisp-owned визначення; один позитивний/негативний вектор із десяти D1:1.
; Нульова викличність D8 не підміняється звичайним Lisp-ім'ям.
(list
  (equal? (знайти-елемент-якщо
            (функція (x) (атом? x))
            (list (cons (quote а) (quote б)) (quote в)))
          (quote в))
  (порожнє? (знайти-елемент-якщо
              (функція (x) (атом? x))
              (list (cons (quote а) (quote б)))))
  (not? (equal? (знайти-елемент-якщо
                  (функція (x) (атом? x))
                  (list (cons (quote а) (quote б)) (quote в)))
                (cons (quote а) (quote б))))
  (тотожне-значення? (quote а) (quote а))
  (not? (тотожне-значення? (quote а) (quote б)))
  (equal? (без-останнього (quote ())) (quote ()))
  (equal? (без-останнього (list (quote а))) (quote ()))
  (equal? (без-останнього (list (quote а) (quote б) (quote в)))
          (list (quote а) (quote б)))
  (not? (equal? (без-останнього (list (quote а) (quote б)))
                (list (quote б))))
  (equal? (без-останнього (list (quote а) (quote б)))
          (list (quote а))))
