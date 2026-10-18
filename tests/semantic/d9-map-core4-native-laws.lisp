; D9 immutable MAP residents — must resolve from shipped Core4, no self DEFINE.
; Coordinates: 101100011 EMPTY, 101100101 GET, 101100010 CONTAINS?,
; 101001100 MAP->LIST. D1 native vector expected (1 1 0 1 1 1 1 1).
; The third bit is intentionally NO, a wrong-key semantic negative.
(список
  (equal? (мапа-порожній) (як-є ()))
  (мапа-містить? (як-є k)
    (список (список (як-є k) (як-є v))))
  (мапа-містить? (як-є missing)
    (список (список (як-є k) (як-є v))))
  (equal?
    (мапа-отримати (як-є k) (список (список (як-є k) (як-є v))))
    (список (як-є v)))
  (порожній?
    (мапа-отримати (як-є missing)
      (список (список (як-є k) (як-є v)))))
  (equal?
    (мапа-список (список (список (як-є k) (як-є v))))
    (список (список (як-є k) (як-є v))))
  (equal?
    (мапа-отримати (як-є k) (список (список (як-є k) (як-є v))))
    (список (як-є v)))
  (equal? (мапа-список (мапа-порожній)) (як-є ())))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити мапа-список map->list)
(визначити мапа-порожній map-empty)
(визначити мапа-отримати map-get)
(визначити порожній? null?)
