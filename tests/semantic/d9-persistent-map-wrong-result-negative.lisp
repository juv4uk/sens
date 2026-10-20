; D9:101100101 MAP-GET — wrong value must produce exact D1:NO.
(load "lib/core.lisp")
(load "lib/persistent-map.lisp")
(список
  (однакові? (мапа-отримати (як-є k)
      (внутрішня-мапа-вставити (як-є k) (як-є v) (мапа-порожній)))
    (список (як-є wrong))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
