; D9:010101111 FS-PACKAGE-FIELD та D9:001100000 FS-UNBIND.
; 9 нативних D1 самосвідків; пакетні ключі — структурні атоми.
(list
  (equal?
    (фс-пакет-поле (quote формат) (list (сполучити (quote формат) (quote корінь))))
    (quote корінь))
  (equal?
    (фс-пакет-поле (quote адреса)
      (list (сполучити (quote формат) (quote корінь))
            (сполучити (quote адреса) (quote мітка))))
    (quote мітка))
  (порожнє?
    (фс-пакет-поле (quote відсутня)
      (list (сполучити (quote формат) (quote корінь)))))
  (порожнє? (фс-пакет-поле (quote формат) (quote не-список)))
  (порожнє?
    (фс-пакет-поле (quote формат)
      (list (сполучити (list (quote формат)) (quote неправильно))
            (сполучити (quote формат) (quote корінь)))))
  (equal?
    (фс-розв'язати
      (list (quote об'єкти) (list (list (quote а) (quote один)) (list (quote б) (quote два))) #d24:000000000000000000000000)
      (quote а))
    (list (quote об'єкти) (list (list (quote б) (quote два))) #d24:000000000000000000000001))
  (equal?
    (фс-розв'язати
      (list (quote об'єкти) (list (list (quote а) (quote один))) #d24:000000000000000000000000)
      (quote відсутня))
    (list (quote об'єкти) (list (list (quote а) (quote один))) #d24:000000000000000000000001))
  (equal?
    (фс-розв'язати
      (list (quote об'єкти) (list (list (quote а) (quote один))) #d24:000000000000000000000000)
      (quote а))
    (list (quote об'єкти) (quote ()) #d24:000000000000000000000001))
  (equal?
    (фс-розв'язати
      (list (quote об'єкти)
            (list (list (quote а) (quote один))
                  (list (quote б) (quote два))
                  (list (quote а) (quote три))) #d24:000000000000000000000000)
      (quote а))
    (list (quote об'єкти) (list (list (quote б) (quote два))) #d24:000000000000000000000001)))
