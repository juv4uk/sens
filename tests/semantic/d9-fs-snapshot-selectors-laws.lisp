; D9 three ratified immutable filesystem projections — six physical D1 laws.
(список
  (equal? (фс-об'єкти (список (quote сховище) (quote відповідності) (quote версія)))
          (quote сховище))
  (equal? (фс-зв'язки (список (quote сховище) (quote відповідності) (quote версія)))
          (quote відповідності))
  (equal? (фс-ревізія (список (quote сховище) (quote відповідності) (quote версія)))
          (quote версія))
  (equal? (фс-об'єкти (список (список (quote а) (quote б))
                            (список (quote шлях) (quote адреса)) (quote версія)))
          (список (quote а) (quote б)))
  (хибне? (equal? (фс-зв'язки (список (quote сховище) (quote відповідності) (quote версія)))
                (quote сховище)))
  (хибне? (equal? (фс-ревізія (список (quote сховище) (quote відповідності) (quote версія)))
                (quote відповідності))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
