; D9:101100101 MAP-GET — wrong value must produce exact D1:NO.
(load "lib/core.lisp")
(load "lib/persistent-map.lisp")
(list
  (equal? (мапа-отримати (quote k)
      (внутрішня-мапа-вставити (quote k) (quote v) (мапа-порожній)))
    (list (quote wrong))))
