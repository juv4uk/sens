; D8:10101001 MAPCAN і D8:10111000 MAPCON — 8 D1-свідків.
; Різниця: MAPCAN передає елемент; MAPCON передає цілий поточний хвіст.
(list
  (null? (відобразити-й-склеїти (lambda (x) (list x)) (quote ())))
  (null? (залишки+склеїти (lambda (хвіст) (list хвіст)) (quote ())))
  (equal? (відобразити-й-склеїти
            (lambda (x) (list x))
            (list (quote а) (quote б)))
          (list (quote а) (quote б)))
  (equal? (відобразити-й-склеїти
            (lambda (x) (list x x))
            (list (quote а) (quote б)))
          (list (quote а) (quote а) (quote б) (quote б)))
  (null? (відобразити-й-склеїти
            (lambda (x) (quote ()))
            (list (quote а) (quote б))))
  (equal? (залишки+склеїти
            (lambda (хвіст) (list хвіст))
            (list (quote а) (quote б)))
          (list (list (quote а) (quote б)) (list (quote б))))
  (not? (equal? (залишки+склеїти
                  (lambda (хвіст) (list хвіст))
                  (list (quote а) (quote б)))
                (list (list (quote б)) (list (quote а) (quote б)))))
  (not? (equal? (відобразити-й-склеїти
                  (lambda (x) (list x))
                  (list (quote а) (quote б)))
                (list (quote б) (quote а)))))
