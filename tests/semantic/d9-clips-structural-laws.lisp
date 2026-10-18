; D9: four pure CLIPS structural laws, eight independent D1 results.
(список
  (equal? (кліпс-слот-ім'я (список (quote slot) (quote колір))) (quote колір))
  (equal? (кліпс-слот-імена (quote ())) (quote ()))
  (equal? (кліпс-слот-імена
            (список (список (quote slot) (quote колір))
                  (список (quote slot) (quote форма))))
          (список (quote колір) (quote форма)))
  (equal? (кліпс-визначити-шаблон-слоти
            (список (quote deftemplate) (quote предмет)
                  (список (quote slot) (quote колір))
                  (список (quote slot) (quote форма))))
          (список (quote колір) (quote форма)))
  (equal? (кліпс-факт-клауза (список (quote є) (quote об'єкт)))
          (список (список (quote є) (quote об'єкт))))
  (equal? (кліпс-факт-клауза (quote ()))
          (список (quote ())))
  (хибне? (equal? (кліпс-слот-імена
                  (список (список (quote slot) (quote колір))
                        (список (quote slot) (quote форма))))
                (список (quote форма) (quote колір))))
  (хибне? (equal? (кліпс-слот-ім'я (список (quote slot) (quote колір)))
                (quote slot))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити кліпс-визначити-шаблон-слоти clips-deftemplate-slots)
(визначити кліпс-факт-клауза clips-fact-clause)
(визначити кліпс-слот-ім'я clips-slot-name)
(визначити кліпс-слот-імена clips-slot-names)
(визначити список list)
(визначити хибне? not?)
