; Історичні свідки розгортання макросів, початкове джерело:
; tests/fixtures/macro-conformance.my, зіставлення з CLAUDE.md.
; Доповнюють conformance.my: перевірки арності та назв defmacro,
; а також макросів послідовного передавання -> та ->>.
; Перевіряємо передавання необчислених аргументів, захоплення оточення,
; момент розгортання, вкладені макроси й порядок виникнення помилок.
; Кожний рядок — окремий асоціативний список у верхньорівневій формі.
; Початкове визначення defmacro належить до першого рівня ядра.
; Поведінка розгортання є контрактом другого рівня: вона визначає
; вимоги до самого механізму, а не тільки факт існування defmacro.
; Цитовані історичні програми та очікувані результати не перекладаємо.

; --- Передавання в defmacro: аргументи залишаються необчисленими даними ---

; Макрос отримує сиру форму, не оцінене значення
((expr . "(defmacro identity-macro (x) x) (identity-macro (quote hello))") (expected . "hello") (tier . 2) (axioms . (G4)) (note . "macro receives unevaluated datum: (quote hello), not the symbol hello"))

; Макрос отримує сиру форму з операторами
((expr . "(defmacro quote-macro (x) (cons (quote quote) (cons x (quote ())))) (quote-macro (+ 1 2))") (expected . "(+ 1 2)") (tier . 2) (axioms . (G4)) (note . "macro sees raw (+ 1 2) datum, not the evaluated 3"))

; --- Захоплення оточення місця визначення перетворювача ---

; Макрос використовує допоміжну функцію, визначену поруч
((expr . "(def my-helper (lambda (x) (+ x 100))) (defmacro use-helper (x) (cons (quote my-helper) (cons x (quote ())))) (use-helper 1)") (expected . "101") (tier . 2) (axioms . (G4 G5)) (note . "transformer body has access to definition-site bindings (my-helper)"))

; Зв'язування місця виклику не видимі перетворювачу:
; він працює з оточенням, у якому обчислено defmacro,
; а не з оточенням місця застосування макроса.
((expr . "(defmacro sees-def-site (x) (cons (quote quote) (cons def-site-val (quote ())))) (def def-site-val (quote from-def)) (sees-def-site ignored)") (expected . "from-def") (tier . 2) (axioms . (G4)) (note . "transformer captures definition-site binding, not call-site"))

; --- Час розгортання: кожен виклик розгортається окремо, без кешування ---

; Кожен виклик запускає незалежне розгортання.
; Без set! перевіряємо це різними результатами на різних аргументах:
; готовий результат одного виклику не можна повторно використати для іншого.
((expr . "(defmacro echo (x) (list (quote quote) x)) (list (echo a) (echo b) (echo c))") (expected . "(a b c)") (tier . 2) (axioms . (G4)) (note . "each call expands independently — different inputs produce different outputs, ruling out caching"))

; --- Вкладеність: результат макроса може містити виклики інших макросів ---

; Макрос може продукувати форми, що містять виклики інших макросів
((expr . "(defmacro wrap (x) (list (quote quote) x)) (defmacro double-wrap (x) (list (quote wrap) (list (quote wrap) x))) (double-wrap hello)") (expected . "(wrap hello)") (tier . 2) (axioms . (G4)) (note . "double-wrap produces (wrap (wrap hello)), which expands to (quote (wrap hello)) = (wrap hello) — recursive macro expansion, but quote halts it"))

; --- Перетворювач може викликати користувацькі бібліотечні функції ---

; Макрос викликає бібліотечну функцію map
((expr . "(defmacro my-map-macro (fn lst) (list (quote map) fn lst)) (my-map-macro (lambda (x) (+ x 1)) (quote (1 2 3)))") (expected . "(2 3 4)") (tier . 2) (axioms . (G4 G5)) (note . "transformer body calls map — confirms macro can compose with library functions"))

; --- Час помилок: арність і форма перевіряються під час розгортання ---

; Невідповідність кількості аргументів — помилка розгортання
((expr . "(defmacro two-args (a b) (list (quote list) a b)) (two-args 1)") (error . "Arity") (tier . 2) (axioms . (S2)) (note . "arity mismatch detected at expansion time, not call time"))

; Невідповідність кількості аргументів — забагато аргументів
((expr . "(defmacro two-args (a b) (list (quote list) a b)) (two-args 1 2 3)") (error . "Arity") (tier . 2) (axioms . (S2)) (note . "too many arguments — same arity check, expansion time"))

; Помилка в тілі transformer — runtime
((expr . "(defmacro bad-body (x) (car 42)) (bad-body hello)") (error . "Type") (tier . 2) (axioms . (S2)) (note . "transformer body error (car of non-list) occurs at expansion time, reported as expansion error"))

; --- Макрос зі сталою частиною параметрів і рештою аргументів ---

; Варіативний макрос з фіксованими + rest параметрами
((expr . "(defmacro build-list (first . rest) (cons (quote list) (cons first rest))) (build-list 1 2 3)") (expected . "(1 2 3)") (tier . 2) (axioms . (G4)) (note . "variadic defmacro with dotted rest: first=1, rest=(2 3)"))

; --- Результат макроса залежить від структури необчисленого аргументу ---

; Макрос, що вибирає форму за типом аргументу
((expr . "(defmacro smart-quote (x) (cond ((00000010 x) (list (quote quote) x)) (t x))) (smart-quote hello)") (expected . "hello") (tier . 2) (axioms . (G4 G8)) (note . "macro inspects argument shape at expansion time: atom gets quoted via (list (quote quote) x)"))

; --- Затінення: def змінює зв'язування імені макроса ---

; Після (def m ...) ім'я m пов'язане з функцією, а не макросом.
; Наступний виклик (m) звертається саме до цієї функції.
((expr . "(defmacro m (x) (list (quote quote) (quote from-macro))) (def m (lambda (x) (quote from-def))) (m (quote ignored))") (expected . "from-def") (tier . 2) (axioms . (G4)) (note . "def rebinds m from macro to function; subsequent (m) calls the function, not the macro — they share one namespace"))

; --- Розгортання макроса у виклик іншого макроса ---

; Макрос розгортається в інший макрос
((expr . "(defmacro expand-to-let (var val body) (list (quote let) (list (list var val)) body)) (expand-to-let x 10 (+ x 5))") (expected . "15") (tier . 2) (axioms . (G4 G5)) (note . "macro produces (let ((x 10)) (+ x 5)) which is itself a macro — tests macro-to-macro expansion chain"))

; --- Порожнє тіло defmacro повертає історичний nil ---

; Макрос з порожньою тілом повертає nil
((expr . "(defmacro void-macro (x) ()) (void-macro ignored)") (expected . "()") (tier . 2) (axioms . (G4)) (note . "empty transformer body returns nil — consistent with lambda/def behavior"))

; --- Збереження місця в джерелі: якісна перевірка, не тест значення ---

; Для звіту про помилки розгортання має зберігати структуру виразу.
; Це не тест числового результату: перевіряємо, що помилки макроса
; вказують правильне місце у вихідному тексті.
; Спеціалізовані перевірки: crates/my-lisp/tests/mccarthy.rs.
