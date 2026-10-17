; D9 resident projections over the active immutable persistent-map mechanism.
; Exact identities: MAP-EMPTY D9:101100011; MAP-GET D9:101100101;
; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; The source mechanism returns () or (value), and stores ordered dotted entries.
(load "lib/core.lisp")
(load "lib/persistent-map.lisp")
(list
  (equal? (мапа-порожній) (quote ()))
  (equal? (мапа-отримати (quote k)
      (внутрішня-мапа-вставити (quote k) (quote v) (мапа-порожній)))
    (list (quote v)))
  (equal? (мапа-отримати (quote missing) (мапа-порожній)) (quote ()))
  (мапа-містить? (quote k)
    (внутрішня-мапа-вставити (quote k) (quote v) (мапа-порожній)))
  (not? (мапа-містить? (quote missing) (мапа-порожній)))
  (equal? (мапа-список
      (внутрішня-мапа-вставити (quote k) (quote v) (мапа-порожній)))
    (list (cons (quote k) (quote v))))
  (equal? (мапа-отримати (quote k)
      (внутрішня-мапа-вставити (quote k) (quote ()) (мапа-порожній)))
    (list (quote ())))
  (equal? (мапа-список
      (внутрішня-мапа-вставити (quote k) (quote v2)
        (внутрішня-мапа-вставити (quote k) (quote v1) (мапа-порожній))))
    (list (cons (quote k) (quote v2)))))
