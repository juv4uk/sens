; D9 content store: five direct and five inverse D1 witnesses.
(list
  (equal? (порожній-вміст-сховище) (quote ()))
  (equal? (вміст-сховище-розмір (порожній-вміст-сховище))
          #d24:000000000000000000000000)
  (equal? (вміст-сховище-розмір
            (list (cons (quote адреса-а) (quote значення-а))
                  (cons (quote адреса-б) (quote ()))))
          #d24:000000000000000000000010)
  (вміст-сховище-містить?
    (list (cons (quote адреса-а) (quote значення-а))
          (cons (quote адреса-б) (quote ())))
    (quote адреса-б))
  (not? (вміст-сховище-містить?
          (list (cons (quote адреса-а) (quote значення-а)))
          (quote адреса-б)))
  (equal? (вміст-сховище-отримати
            (list (cons (quote адреса-а) (quote значення-а)))
            (quote адреса-а))
          (list (quote значення-а)))
  (equal? (вміст-сховище-отримати
            (list (cons (quote адреса-б) (quote ())))
            (quote адреса-б))
          (list (quote ())))
  (equal? (вміст-сховище-отримати
            (list (cons (quote адреса-а) (quote значення-а)))
            (quote адреса-б))
          (quote ()))
  (not? (equal? (вміст-сховище-отримати
                  (list (cons (quote адреса-б) (quote ())))
                  (quote адреса-б))
                (quote ())))
  (not? (вміст-сховище-містить?
          (порожній-вміст-сховище) (quote адреса-а))))
