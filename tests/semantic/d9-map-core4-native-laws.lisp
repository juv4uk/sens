; D9 immutable MAP residents — must resolve from shipped Core4, no self DEFINE.
; Coordinates: 101100011 EMPTY, 101100101 GET, 101100010 CONTAINS?,
; 101001100 MAP->LIST. D1 native vector expected (1 1 0 1 1 1 1 1).
; The third bit is intentionally NO, a wrong-key semantic negative.
(list
  (equal? (мапа-порожній) (quote ()))
  (мапа-містить? (quote k)
    (list (list (quote k) (quote v))))
  (мапа-містить? (quote missing)
    (list (list (quote k) (quote v))))
  (equal?
    (мапа-отримати (quote k) (list (list (quote k) (quote v))))
    (list (quote v)))
  (null?
    (мапа-отримати (quote missing)
      (list (list (quote k) (quote v)))))
  (equal?
    (мапа-список (list (list (quote k) (quote v))))
    (list (list (quote k) (quote v))))
  (equal?
    (map-get (quote k) (list (list (quote k) (quote v))))
    (list (quote v)))
  (equal? (map->list (map-empty)) (quote ())))
