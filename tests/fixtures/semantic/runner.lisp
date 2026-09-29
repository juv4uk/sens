; tests/fixtures/semantic/runner.lisp — #1709 LISP-SEMANTIC-WITNESSES-1
; мінімальний протокол тверджень, який SENS належить сам собі.
; minimal assertion/verdict protocol, owned by the language itself.
;
; ПРИНЦИП: мова тестує власний зміст; реалізації лише доводять, що йому
; підкоряються. Expected outcome живе тут, у Lisp-даних, а host-код
; переносить лише те, що фактично відбулося.
;
; PRINCIPLE: the language tests its own meaning; implementations only prove
; that they obey it. The expected outcome lives here, in Lisp data; host code
; transports only what actually happened.
;
; Рядок твердження (alist; усі поля обов'язкові):
;   expect      — вид твердження: expect-value | expect-error | expect-rejected
;                 (assertion kind: value | named error | reader rejection)
;   expr        — вихідний текст: обчислити або відхилити
;                 (source text to evaluate, or to be rejected by the reader)
;   expected    — очікувана конвенція як ЖИВІ Lisp-дані, ніколи не рядок Rust:
;                   (value <datum>) | (error "Type") | (rejected "<source>")
;                 (expected outcome as live Lisp data, never a host literal)
;   active      — ряд виконуваний проти поточного рантайму
;                 (row is executable against the current runtime)
;   name        — коротка людська назва закону
;   semantic-id — точний голий SENS ідентифікатор функції під перевіркою
;   governs     — номери issue, які встановлюють закон
;   note        — що саме стверджує ряд
;
; Транспорт actual (host → Lisp), три конвенції однакової форми:
;   (value <datum>)       — обчислення дало значення
;   (error "Type")        — обчислення дало іменовану помилку
;   (rejected "<source>") — reader відхилив вихідний текст
; Payload — це форма, яку reader читає назад у той самий datum, який називає
; `expected`; для рядкових значень payload є рядковим літералом. Runner
; читає payload, відбудовує конвенцію й порівнює її з expected — у Lisp.
;
; Усі три конвенції мають рівно два елементи, тому порівняння тотальне: жодної
; гілки, жодного умовного оператора. Усе однаково.
; All three envelopes have exactly two elements, so the comparison is total:
; no branch, no conditional operator anywhere in this protocol.
;
; ЧОМУ ТУТ НЕМАЄ cond/if: 2-частинний cond на поточному main трактує 0 як
; істину (міграційна шкала), а 3-частинний — запит-форма, яку #1713/#1714
; замінює. Протокол, який перевіряє саме цей закон, не може стояти на ньому.
; WHY NO cond/if HERE: the two-part cond on current main still treats 0 as
; true (migration scale) and the three-part form is a query shape that
; #1713/#1714 replace. A protocol that tests that very law cannot stand on it.
;
; ВИМІРЯНА АСИМЕТРІЯ assoc У ЦЬОМУ РАНТАЙМІ (перевірено на main):
;   (cdr (assoc 'k '((k . v)))) → v          — прократкова пара
;   (cdr (assoc 'k '((k  v)))) → (v)        — звичайний список, зайвий рівень
; Тому кожна таблиця, з якої цей протокол читає через assoc+cdr, має бути
; прократковою: і поля рядка (так їх пише читач фістури), і таблиця міток.
; WHY THE VERDICT IS THE BARE RESULT, NOT A RECORD: the measured asymmetry
; above makes any field list the host would have to read back ambiguous, and a
; protocol that cannot reliably read itself is no use for testing a law. The
; verdict is the datum, and nothing else.
; MEASURED assoc ASYMMETRY IN THIS RUNTIME (verified on main):
;   (cdr (assoc 'k '((k . v)))) -> v     dotted pair
;   (cdr (assoc 'k '((k  v)))) -> (v)   proper list, one extra level
; Every table this protocol reads through assoc+cdr must therefore be dotted:
; the row fields (which is how the fixture reader writes them) and the label
; table alike.

; 00001001 define / визначити
; 00001000 lambda
; 00000101 car / перше
; 00000110 cdr / решта
; 00101101 assoc / знайти-за-ключем
; 00101111 second / друге
; 01001010 read / прочитати
; 00100010 equal? / однакові?
; 00100111 list / список

; Константи відповіді належать самій мові, а не host-ом: якщо представлення
; відповіді зміниться (#1714), обидві сторони тесту зміняться разом.
; The language's own answer constants, not host booleans: when the answer
; representation changes (#1714), both sides of the test move together.
(00001001 semantic-pass-answer (00100010 1 1))
(00001001 semantic-fail-answer (00100010 1 2))

; Поля рядка — прократкові пари, бо так їх пише читач фістури; assoc+cdr
; повертає їх значення. Кодом прократкову пару створити не можна
; ("a dotted pair is not executable code") — тому код спирається наassoc лише
; на читання, а не на побудову.
; Row fields are dotted pairs, because that is how the fixture reader writes
; them, and assoc+cdr returns their values. Code cannot build a dotted pair
; ("a dotted pair is not executable code"), so the code path only ever READS
; alists, it never constructs one.
(00001001 semantic-row-expect (00001000 (row) (00000110 (00101101 (00000001 expect) row))))
(00001001 semantic-row-expected (00001000 (row) (00000110 (00101101 (00000001 expected) row))))
(00001001 semantic-row-name (00001000 (row) (00000110 (00101101 (00000001 name) row))))

; Чи активний рядок? Активність — політика виконання корпусу, не семантика.
; Is the row active? Activation is corpus execution policy, not semantics.
(00001001 semantic-row-active?
  (00001000 (row)
    (00100010 (00000110 (00101101 (00000001 active) row)) (00000001 t))))

; Транспортований факт, прочитаний назад як datum. Host ніколи не порівнює.
; The transported fact, read back as a datum. The host never compares.
(00001001 semantic-actual-datum
  (00001000 (actual)
    (00100111 (00000101 actual) (01001010 (00101111 actual)))))

; Нормативне порівняння. Host дає лише actual; expected читається з рядка.
; The normative comparison. The host supplies ACTUAL only; expected is read
; from the Lisp-owned row.
(00001001 semantic-verdict
  (00001000 (row actual)
    (00100010 (semantic-row-expected row) (semantic-actual-datum actual))))

; Мітка обчислюється тут, у Lisp: host порівнює символ, який належить цьому
; протоколу, а не біт, вигаданий ним самим. Ключі — власний carrier відповіді
; цієї мови, тому зміна представлення (#1714) рухає мітку разом із відповіддю.
; The label is computed here, in Lisp: the host compares a symbol that belongs
; to this protocol, not a bit it invented. The keys are this language's own
; answer carrier, so a representation change (#1714) moves the label together
; with the answer.
(00001001 semantic-verdict-label
  (00001000 (row actual)
    (00000110 (00101101 (semantic-verdict row actual)
      (00000001 (((1) . pass) ((0) . fail)))))))

(00001001 semantic-layer-id
  (00001000 () (00000001 "LISP-SEMANTIC-WITNESSES-1")))
