; D6:101110 REDUCE: real SENS D1 self-verdicts for nonempty/empty folds.
; Positive controls fail if REDUCE silently drops either head or tail.
(список
  (equal?
    (згорнути (lambda (acc item) (сполучити item acc))
      (quote ()) (список (quote а) (quote б) (quote в)))
    (список (quote в) (quote б) (quote а)))
  (equal?
    (згорнути (lambda (acc item) (сполучити item acc))
      (quote ()) (список (quote а) (quote б)))
    (список (quote б) (quote а)))
  (equal?
    (згорнути (lambda (acc item) (сполучити item acc))
      (quote а) (quote ()))
    (quote а)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
(визначити згорнути reduce)
