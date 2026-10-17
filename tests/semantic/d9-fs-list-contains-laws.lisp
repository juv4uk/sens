; D9 FS-LIST / FS-CONTAINS?: нативні закони з точним D1 вердиктом.
(list
  (equal?
    (фс-список (list (quote об'єкти) (list (list (quote а) (quote один))) (quote ревізія)))
    (list (list (quote а) (quote один))))
  (equal?
    (фс-список (list (quote об'єкти) (quote ()) (quote ревізія)))
    (quote ()))
  (фс-містить?
    (list (quote об'єкти) (list (list (quote а) (quote один))) (quote ревізія))
    (quote а))
  (not?
    (фс-містить?
      (list (quote об'єкти) (list (list (quote а) (quote один))) (quote ревізія))
      (quote немає)))
  (фс-містить?
    (list (quote об'єкти) (list (list (quote порожнє) (quote ()))) (quote ревізія))
    (quote порожнє))
  (not?
    (фс-містить?
      (list (quote об'єкти) (quote ()) (quote ревізія))
      (quote а)))
  (фс-містить?
    (list (quote об'єкти)
          (list (list (quote перший) (quote а)) (list (quote другий) (quote б)))
          (quote ревізія))
    (quote другий))
  (фс-містить?
    (list (quote об'єкти)
          (list (list (quote перший) (quote а)) (list (quote другий) (quote б)))
          (quote ревізія))
    (quote перший))
  (equal?
    (фс-список (list (quote об'єкти)
                     (list (list (quote порожнє) (quote ())))
                     (quote ревізія)))
    (list (list (quote порожнє) (quote ())))))

