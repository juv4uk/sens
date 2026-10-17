; D9: four pure CLIPS structural laws, eight independent D1 results.
(list
  (equal? (clips-slot-name (list (quote slot) (quote колір))) (quote колір))
  (equal? (clips-slot-names (quote ())) (quote ()))
  (equal? (clips-slot-names
            (list (list (quote slot) (quote колір))
                  (list (quote slot) (quote форма))))
          (list (quote колір) (quote форма)))
  (equal? (clips-deftemplate-slots
            (list (quote deftemplate) (quote предмет)
                  (list (quote slot) (quote колір))
                  (list (quote slot) (quote форма))))
          (list (quote колір) (quote форма)))
  (equal? (clips-fact-clause (list (quote є) (quote об'єкт)))
          (list (list (quote є) (quote об'єкт))))
  (equal? (clips-fact-clause (quote ()))
          (list (quote ())))
  (not? (equal? (clips-slot-names
                  (list (list (quote slot) (quote колір))
                        (list (quote slot) (quote форма))))
                (list (quote форма) (quote колір))))
  (not? (equal? (clips-slot-name (list (quote slot) (quote колір)))
                (quote slot))))
