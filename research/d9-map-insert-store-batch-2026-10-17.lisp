; D9 MAP-INSERT / VEC->LIST + content-store list projections
; Residency lib/domains/d9.lisp. Alist/list only; no host store.

; D9:101101110 MAP-INSERT — front pair + drop old key
(0011 мапа-вставити
  (0010 (ключ значення мапа)
    (111
      (111 ключ (111 значення (001 ())))
      (відсіяти
        (0010 (пара) (хибне? (equal? (100 пара) ключ)))
        мапа))))
(0011 map-insert мапа-вставити)

; D9:101011000 VEC->LIST
(0011 вектор-список
  (0010 (вектор) вектор))
(0011 vec->list вектор-список)

; D9:000100001 EMPTY-CONTENT-STORE → map-empty
(0011 порожній-вміст-сховище мапа-порожній)
(0011 empty-content-store порожній-вміст-сховище)

; D9:000100000 CONTENT-STORE-GET → map-get
(0011 вміст-сховище-отримати мапа-отримати)
(0011 content-store-get вміст-сховище-отримати)

; D9:000011110 CONTENT-STORE-CONTAINS? → map-contains?
(0011 вміст-сховище-містить? мапа-містить?)
(0011 content-store-contains? вміст-сховище-містить?)

; D9:000101101 CONTENT-STORE-PUT → map-insert
(0011 вміст-сховище-покласти мапа-вставити)
(0011 content-store-put вміст-сховище-покласти)
