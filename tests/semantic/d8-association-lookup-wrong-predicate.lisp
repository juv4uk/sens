; D8:00101010 callback returns non-D1 data, exact COND must refuse.
(знайти-асоціацію-якщо
  (lambda (x) (quote не-предикат))
  (список (сполучити (quote ключ) (quote значення))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
