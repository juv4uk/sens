; D9 immutable MAP residents — must resolve from shipped Core4, no self DEFINE.
; Coordinates: 101100011 EMPTY, 101100101 GET, 101100010 CONTAINS?,
; 101001100 MAP->LIST. D1 native vector expected (1 1 0 1 1 1 1 1).
; The third bit is intentionally NO, a wrong-key semantic negative.
(список
  (equal? (мапа-порожній) (quote ()))
  (мапа-містить? (quote k)
    (список (список (quote k) (quote v))))
  (мапа-містить? (quote missing)
    (список (список (quote k) (quote v))))
  (equal?
    (мапа-отримати (quote k) (список (список (quote k) (quote v))))
    (список (quote v)))
  (порожній?
    (мапа-отримати (quote missing)
      (список (список (quote k) (quote v)))))
  (equal?
    (мапа-список (список (список (quote k) (quote v))))
    (список (список (quote k) (quote v))))
  (equal?
    (мапа-отримати (quote k) (список (список (quote k) (quote v))))
    (список (quote v)))
  (equal? (мапа-список (мапа-порожній)) (quote ())))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити мапа-список map->list)
(визначити мапа-порожній map-empty)
(визначити мапа-отримати map-get)
(визначити порожній? null?)
