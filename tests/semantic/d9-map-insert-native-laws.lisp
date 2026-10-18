; D9:101101110 MAP-INSERT, 101011000 VEC->LIST from live Core4.
; Immutable overwrite replaces existing key; no duplicate keys are retained.
; D1 vector (1 1 1 0 1 1 1 1 1), bit 4 is an intentional old-value negative.
(список
  (equal?
    (мапа-отримати (quote k)
      (мапа-вставити (quote k) (quote v) (мапа-порожній)))
    (список (quote v)))
  (мапа-містить? (quote k)
    (мапа-вставити (quote k) (quote v) (мапа-порожній)))
  (equal?
    (мапа-отримати (quote k)
      (мапа-вставити (quote k) (quote нове)
        (мапа-вставити (quote k) (quote старе) (мапа-порожній))))
    (список (quote нове)))
  (equal?
    (мапа-отримати (quote k)
      (мапа-вставити (quote k) (quote нове)
        (мапа-вставити (quote k) (quote старе) (мапа-порожній))))
    (список (quote старе)))
  (equal?
    (довжина (мапа-список
      (мапа-вставити (quote k) (quote нове)
        (мапа-вставити (quote k) (quote старе) (мапа-порожній)))))
    #d24:000000000000000000000001)
  (мапа-містить? (quote k)
    (мапа-вставити (quote q) (quote b)
      (мапа-вставити (quote k) (quote a) (мапа-порожній))))
  (мапа-містить? (quote q)
    (мапа-вставити (quote q) (quote b)
      (мапа-вставити (quote k) (quote a) (мапа-порожній))))
  (equal? (вектор-список (список (quote a) (quote b)))
          (список (quote a) (quote b)))
  (equal? (вектор-список (вектор-порожній)) (quote ())))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити вектор-список vec->list)
(визначити вектор-порожній vec-empty)
