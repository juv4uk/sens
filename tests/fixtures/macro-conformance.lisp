; tests/fixtures/macro-conformance.my — macro expansion contract
; (see CLAUDE.md): tests for defmacro and macro expansion semantics.
; Complements conformance.my (which covers defmacro arity/name validation
; in fixtures L121-122, L145 and the -> / ->> thread macros in L211-216).
; This file focuses on the expansion mechanism itself: argument passing,
; environment capture, expansion timing, nesting, and error behavior.
; Same format: one flat alist per fixture, one fixture per top-level form.
;
; Tier rationale: defmacro as a bootstrap form is Tier 1 (core semantics).
; Macro expansion *behavior* — how arguments are passed, when expansion
; happens, what errors occur and when — is Tier 2 (language contract),
; because it defines the contract the expansion mechanism must satisfy,
; not just the existence of the mechanism.
;
; Source: tests/fixtures/macro-conformance.my — macro expansion contract
; Ціль: тести семантики defmacro та розгортання макросів
; Формат: один асоціативний список на фікстуру, один топ-форма
; Рівень: Tier 2 (контракт мови) — розгортання макросів є контрактом,
;          не лише існуванням механізму

; --- defmacro argument passing: arguments are raw datums, not evaluated ---

; Макрос отримує сиру форму, не оцінене значення
((expr . "(defmacro identity-macro (x) x) (identity-macro (quote hello))") (expected . "hello") (tier . 2) (axioms . (G4)) (note . "macro receives unevaluated datum: (quote hello), not the symbol hello"))

; Макрос отримує сиру форму з операторами
((expr . "(defmacro quote-macro (x) (cons (quote quote) (cons x (quote ())))) (quote-macro (+ 1 2))") (expected . "(+ 1 2)") (tier . 2) (axioms . (G4)) (note . "macro sees raw (+ 1 2) datum, not the evaluated 3"))

; --- environment capture: transformer closes over definition-site env ---

; Макрос використовує допоміжну функцію, визначену поруч
((expr . "(def my-helper (lambda (x) (+ x 100))) (defmacro use-helper (x) (cons (quote my-helper) (cons x (quote ())))) (use-helper 1)") (expected . "101") (tier . 2) (axioms . (G4 G5)) (note . "transformer body has access to definition-site bindings (my-helper)"))

; Call-site bindings are NOT visible to the transformer — it runs with
; the environment where defmacro was evaluated, not where the macro is called.
; Прив'язки місця виклику НЕ видні трансформеру — він працює з середовищем,
; де було оцінено defmacro, не з того, де макрос викликається.
((expr . "(defmacro sees-def-site (x) (cons (quote quote) (cons def-site-val (quote ())))) (def def-site-val (quote from-def)) (sees-def-site ignored)") (expected . "from-def") (tier . 2) (axioms . (G4)) (note . "transformer captures definition-site binding, not call-site"))

; --- expansion timing: expansion happens at call site, no caching ---

; Each macro call triggers expansion independently (no memoization).
; Without set!, we verify this by observing that a macro producing
; different output for different inputs cannot be cached.
; Кожен виклик макроса запускає розгортання окремо (без мемоізації).
((expr . "(defmacro echo (x) (list (quote quote) x)) (list (echo a) (echo b) (echo c))") (expected . "(a b c)") (tier . 2) (axioms . (G4)) (note . "each call expands independently — different inputs produce different outputs, ruling out caching"))

; --- nesting: macro can produce forms that contain macro calls ---

; Макрос може продукувати форми, що містять виклики інших макросів
((expr . "(defmacro wrap (x) (list (quote quote) x)) (defmacro double-wrap (x) (list (quote wrap) (list (quote wrap) x))) (double-wrap hello)") (expected . "(wrap hello)") (tier . 2) (axioms . (G4)) (note . "double-wrap produces (wrap (wrap hello)), which expands to (quote (wrap hello)) = (wrap hello) — recursive macro expansion, but quote halts it"))

; --- macro calling user functions: transformer body uses library functions ---

; Макрос викликає бібліотечну функцію map
((expr . "(defmacro my-map-macro (fn lst) (list (quote map) fn lst)) (my-map-macro (lambda (x) (+ x 1)) (quote (1 2 3)))") (expected . "(2 3 4)") (tier . 2) (axioms . (G4 G5)) (note . "transformer body calls map — confirms macro can compose with library functions"))

; --- error timing: arity/form errors at expansion, body errors at runtime ---

; Невідповідність кількості аргументів — помилка розгортання
((expr . "(defmacro two-args (a b) (list (quote list) a b)) (two-args 1)") (error . "Arity") (tier . 2) (axioms . (S2)) (note . "arity mismatch detected at expansion time, not call time"))

; Невідповідність кількості аргументів — забагато аргументів
((expr . "(defmacro two-args (a b) (list (quote list) a b)) (two-args 1 2 3)") (error . "Arity") (tier . 2) (axioms . (S2)) (note . "too many arguments — same arity check, expansion time"))

; Помилка в тілі transformer — runtime
((expr . "(defmacro bad-body (x) (car 42)) (bad-body hello)") (error . "Type") (tier . 2) (axioms . (S2)) (note . "transformer body error (car of non-list) occurs at expansion time, reported as expansion error"))

; --- variadic macro: fixed + rest ---

; Варіативний макрос з фіксованими + rest параметрами
((expr . "(defmacro build-list (first . rest) (cons (quote list) (cons first rest))) (build-list 1 2 3)") (expected . "(1 2 3)") (tier . 2) (axioms . (G4)) (note . "variadic defmacro with dotted rest: first=1, rest=(2 3)"))

; --- macro producing different forms based on argument shape ---

; Макрос, що вибирає форму за типом аргументу
((expr . "(defmacro smart-quote (x) (cond ((00000010 x) (list (quote quote) x)) (t x))) (smart-quote hello)") (expected . "hello") (tier . 2) (axioms . (G4 G8)) (note . "macro inspects argument shape at expansion time: atom gets quoted via (list (quote quote) x)"))

; --- macro shadowing: def overwrites macro binding ---

; After (def m ...), m is a function, not a macro — (m) calls the function.
; Після (def m ...) m стає функцією, не макросом — (m) викликає функцію.
((expr . "(defmacro m (x) (list (quote quote) (quote from-macro))) (def m (lambda (x) (quote from-def))) (m (quote ignored))") (expected . "from-def") (tier . 2) (axioms . (G4)) (note . "def rebinds m from macro to function; subsequent (m) calls the function, not the macro — they share one namespace"))

; --- macro that expands to a macro call ---

; Макрос розгортається в інший макрос
((expr . "(defmacro expand-to-let (var val body) (list (quote let) (list (list var val)) body)) (expand-to-let x 10 (+ x 5))") (expected . "15") (tier . 2) (axioms . (G4 G5)) (note . "macro produces (let ((x 10)) (+ x 5)) which is itself a macro — tests macro-to-macro expansion chain"))

; --- defmacro with no body: transformer returns nil ---

; Макрос з порожньою тілом повертає nil
((expr . "(defmacro void-macro (x) ()) (void-macro ignored)") (expected . "()") (tier . 2) (axioms . (G4)) (note . "empty transformer body returns nil — consistent with lambda/def behavior"))

; --- macro preserving source location (qualitative, not value-tested) ---

; Qualitative: expansion preserves expression structure for error reporting.
; Not a value fixture — verified by observing that macro-produced errors
; reference the correct source location in error messages. See
; crates/my-lisp/tests/mccarthy.rs for implementation-specific tests.
; Якісно: розгортання зберігає структуру виразу для звітування про помилки.
; Не value-фікстура — перевіряється спостереженням, що помилки, створені
; макросами, вказують правильне джерело. Див. crates/my-lisp/tests/mccarthy.rs
