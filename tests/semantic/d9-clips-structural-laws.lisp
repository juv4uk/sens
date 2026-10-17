; D9: four pure CLIPS structural laws, eight independent D1 results.
(list
  (equal? (clips-слот-ім'я (list (quote slot) (quote колір))) (quote колір))
  (equal? (clips-слот-імена (quote ())) (quote ()))
  (equal? (clips-слот-імена
            (list (list (quote slot) (quote колір))
                  (list (quote slot) (quote форма))))
          (list (quote колір) (quote форма)))
  (equal? (clips-deftemplate-слоти
            (list (quote deftemplate) (quote предмет)
                  (list (quote slot) (quote колір))
                  (list (quote slot) (quote форма))))
          (list (quote колір) (quote форма)))
  (equal? (clips-факт-клауза (list (quote є) (quote об'єкт)))
          (list (list (quote є) (quote об'єкт))))
  (equal? (clips-факт-клауза (quote ()))
          (list (quote ())))
  (not? (equal? (clips-слот-імена
                  (list (list (quote slot) (quote колір))
                        (list (quote slot) (quote форма))))
                (list (quote форма) (quote колір))))
  (not? (equal? (clips-слот-ім'я (list (quote slot) (quote колір)))
                (quote slot))))
