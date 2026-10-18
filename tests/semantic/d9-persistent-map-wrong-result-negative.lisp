; D9:101100101 MAP-GET — wrong value must produce exact D1:NO.
(load "lib/core.lisp")
(load "lib/persistent-map.lisp")
(список
  (equal? (мапа-отримати (quote k)
      (внутрішня-мапа-вставити (quote k) (quote v) (мапа-порожній)))
    (список (quote wrong))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
