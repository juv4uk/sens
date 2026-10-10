; Облік дозволених нових foreign Python-інструментів (постанова #5397).
; Кожне додавання має мати доведені independence_status=foreign та план міграції.
; Один запис: (foreign-tool "tools/<назва>.py" foreign "#задача" "план")
; Порожній реєстр означає: нових Python-інструментів не допущено.
; Історичні scripts/*.py не легалізуються цим файлом та мігрують окремо.
(00000001
  ((schema . foreign-tool-census/1)
   (independence_status . foreign)
   (entries . ())))
