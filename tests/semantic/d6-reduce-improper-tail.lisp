; D6:101110 REDUCE must not accept improper nonempty tails as NIL.
(згорнути (lambda (acc item) (сполучити item acc))
  (quote ()) (сполучити (quote а) (quote обірвано)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
