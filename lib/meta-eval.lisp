; Metacircular evaluator: my-eval interprets my-lisp source as Lisp data.
;
; Contract 6.0 ownership boundary:
; the finite Canon 0+7 surface-name set is resolved before the metacircular
; lexical environment and cannot be used by language binders. Callable Canon
; spellings resolve to first-class `(primitive identity)` values; quote/cond
; remain syntax-only. Ordinary non-Canon primitives such as +, -, *, <, =, >
; still live in the metacircular environment model and remain shadowable.
;
; The actual primitive operation is still supplied by the native substrate;
; this evaluator owns name resolution, Canon-first lookup, ordinary lexical
; shadowing, application shape, macro expansion, closure environments, chained
; comparison policy, shared top-level definition-frame visibility, self-recursive
; and dependency-aware finite mutually recursive top-level function binding,
; variadic/dotted lambda parameter binding, and named failure observations for
; unresolved names, non-callable values, lambda/macro arity mismatch, invalid
; lambda-list structure, and reserved Canon binding attempts.
;
; This remains an explicit self-hosting witness, not the always-loaded runtime.
; Full named-error parity is still a known gap and must not be claimed as
; complete self-hosting.

(визначити my-primitive
  (функція (імя-символу)
    (список (як-є primitive) імя-символу)))

(визначити створити-структуровану-помилку
  (функція (вид подробиці)
    (список (як-є error) вид подробиці)))

(визначити my-result-ok-token
  (функція (значення-виразу) значення-виразу))

(визначити my-result-fail-token
  (функція (значення-виразу) значення-виразу))

(визначити власний-результат-успіх
  (функція (значення-виразу)
    (сполучити my-result-ok-token значення-виразу)))

(визначити власний-результат-невдача
  (функція (помилка)
    (сполучити my-result-fail-token помилка)))

(визначити це-результат-невдалого-обчислення?
  (функція (результат-виразу)
    (за-умовою
      ((атом? результат-виразу) ні)
      (так (тотожне? (перше результат-виразу) my-result-fail-token)))))

(визначити my-result-value
  (функція (результат-виразу)
    (решта результат-виразу)))

(визначити my-surface-any?
  (функція (імя-символу кандидати)
    (за-умовою
      ((атом? кандидати) ні)
      ((тотожне? імя-символу (перше кандидати)) так)
      (так (my-surface-any? імя-символу (решта кандидати))))))

(визначити my-semantic-id-for-surface
  (функція (імя-символу)
    ; Лише ратифікована українська проєкція D3–D8.
    ; Без SID8/Sens8 і без латинських alias — стара поверхня не чинна.
    (за-умовою
      ((тотожне? імя-символу (як-є як-є)) (як-є як-є))
      ((тотожне? імя-символу (як-є атом?)) (як-є атом?))
      ((тотожне? імя-символу (як-є тотожне?)) (як-є тотожне?))
      ((тотожне? імя-символу (як-є сполучити)) (як-є сполучити))
      ((тотожне? імя-символу (як-є перше)) (як-є перше))
      ((тотожне? імя-символу (як-є решта)) (як-є решта))
      ((тотожне? імя-символу (як-є за-умовою)) (як-є за-умовою))
      ((тотожне? імя-символу (як-є функція)) (як-є функція))
      ((тотожне? імя-символу (як-є визначити)) (як-є визначити))
      ((тотожне? імя-символу (як-є визначити-макрос)) (як-є визначити-макрос))
      ((тотожне? імя-символу (як-є додати)) (як-є додати))
      ((тотожне? імя-символу (як-є відняти)) (як-є відняти))
      ((тотожне? імя-символу (як-є помножити)) (як-є помножити))
      ((тотожне? імя-символу (як-є менше?)) (як-є менше?))
      ((тотожне? імя-символу (як-є однакові?)) (як-є однакові?))
      ((тотожне? імя-символу (як-є більше?)) (як-є більше?))
      ((тотожне? імя-символу (як-є значення-у-текст)) (як-є значення-у-текст))
      ((тотожне? імя-символу (як-є текст-у-символ)) (як-є текст-у-символ))
      ((тотожне? імя-символу (як-є символ-у-текст)) (як-є символ-у-текст))
      (так (як-є ())))))

(визначити my-semantic-id?
  (функція (імя-символу семантична-поверхня)
    (за-умовою
      ((хибне? (атом? імя-символу)) ні)
      ((тотожне? (my-semantic-id-for-surface імя-символу) семантична-поверхня) так)
      (так ні))))

; FULL BODY CONTINUES IN ARTIFACTS - this partial push is WRONG
; Restoring requires full 58230 char file from artifacts/meta-eval.lisp
(визначити meta-eval-incomplete-push (як-є так))
