; D6:101110 REDUCE must not accept improper nonempty tails as NIL.
(згорнути (функція (acc item) (сполучити item acc))
  (як-є ()) (сполучити (як-є а) (як-є обірвано)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
