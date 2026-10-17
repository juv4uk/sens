; D9:101101110 MAP-INSERT, 101011000 VEC->LIST from live Core4.
; Immutable overwrite replaces existing key; no duplicate keys are retained.
; D1 vector (1 1 1 0 1 1 1 1 1), bit 4 is an intentional old-value negative.
(list
  (equal?
    (мапа-отримати (quote k)
      (мапа-вставити (quote k) (quote v) (мапа-порожній)))
    (list (quote v)))
  (мапа-містить? (quote k)
    (мапа-вставити (quote k) (quote v) (мапа-порожній)))
  (equal?
    (мапа-отримати (quote k)
      (мапа-вставити (quote k) (quote нове)
        (мапа-вставити (quote k) (quote старе) (мапа-порожній))))
    (list (quote нове)))
  (equal?
    (мапа-отримати (quote k)
      (мапа-вставити (quote k) (quote нове)
        (мапа-вставити (quote k) (quote старе) (мапа-порожній))))
    (list (quote старе)))
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
  (equal? (вектор-список (list (quote a) (quote b)))
          (list (quote a) (quote b)))
  (equal? (vec->list (vec-empty)) (quote ())))
