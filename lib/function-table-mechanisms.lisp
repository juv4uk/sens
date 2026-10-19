; Метадані механізмів виконання вже ратифікованих функцій.
; Ідентичність і ширина визначаються тільки таблицями lib/domains/d1.lisp…d10.lisp.
; Цей файл не ратифікує нових функцій, не призначає значень координатам і не
; створює механізм виконання лише через наявність рядка.
;
; Порожня структура () є значенням, а не функцією чи номером слота.
; Точні голови нижче — повна українська проєкція чинних D3/D4/D5 мешканців.

(
  (schema function-table-mechanisms/1)
  (authority "lib/domains/d1.lisp…d10.lisp")
  (lifecycle transitional)
  (retirement-issue 1046)
  (rows
    ; Керувальні форми та спискові механізми мають точні D3/D4 identity.
    (як-є evaluator quote-form)
    (атом? evaluator atom-primitive)
    (тотожне? evaluator eq-primitive)
    (сполучити evaluator cons-primitive)
    (перше evaluator car-primitive)
    (решта evaluator cdr-primitive)
    (за-умовою evaluator cond-form)
    (функція evaluator lambda-form)
    (визначити evaluator define-form)
    ; Рядки механізмів додають виконавця до вже визначеної D5:01010 функції,
    ; але не визначають арифметичного закону додавання.
    (додати common-lisp bounded-exact-add)
    (додати prolog bounded-exact-add)
    (додати clips bounded-exact-add)
    (додати datalog bounded-exact-add))
  ; Профіль обирається перед перевіркою доступності механізму.
  (profile-routes))
