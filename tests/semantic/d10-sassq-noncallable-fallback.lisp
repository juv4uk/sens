; D10 SASSQ: fallback is required to be callable only on miss.
(асоціація-тотожність (quote немає)
  (список (сполучити (quote ключ-а) (quote знач-а)))
  (quote не-викличне))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
(визначити асоціація-тотожність sassq)
