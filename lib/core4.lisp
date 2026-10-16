
; my-lisp bootstrap library: derived behavior belongs in the language itself.
; Bootstrap-бібліотека my-lisp: похідна поведінка належить самій мові.
; my-lisp-Bootstrap-Bibliothek: Abgeleitetes Verhalten gehört in die Sprache selbst.

(0011 identity (0010 (value) value))

; Lisp-owned binary format descriptor for the canonical 8-bit bit syntax.
; The reader treats the following source forms as binary data until the next
; top-level source is read; decimal integers remain ordinary decimal values.
(0011 binary
  (0010 (width)
    (1110 (001 binary) width)))

; `list` used to be a Rust special form (`evaluate_list_func`) — moved here
; 2026-08-09 once variadic lambda parameters existed to express it: a bare
; symbol as the parameter list binds every argument, evaluated left to
; right, as one list. This is pure sugar over `cons`/`'()`, exactly the
; kind of thing G4/G5 (docs/language-core-axioms.md) say belongs in the
; language itself once the core can already express it, not bolted onto
; the host. Kept first in this file (not wherever it happens to be used)
; because `let`/`let*` below build their expansion with it.
; `list` раніше був спеціальною формою Rust (`evaluate_list_func`) —
; перенесено сюди 2026-08-09, щойно з'явились варіативні параметри lambda,
; якими його можна виразити: голий символ як список параметрів зв'язує
; кожен аргумент, обчислений зліва направо, в один список. Це чистий цукор
; над `cons`/`'()` — саме те, що G4/G5 (docs/language-core-axioms.md)
; кажуть має належати самій мові, щойно ядро вже може це виразити, не
; хосту. Лишено першим у файлі (не там, де випадково використовується),
; бо `let`/`let*` нижче будують свою розгортку через нього.
(0011 list (0010 args args))

; and/or are Lisp-owned short-circuit macros. A tested operand must return
; an exact D1 PredicateBit; 0 is not () and neither result is host T/NIL.
; Each COND clause below has exactly two fields: (test expression). The last
; operand is still returned as a value without being reinterpreted as a test.
(0011 and
  (make-macro
    (0010 rest
  (110
    ((010 rest) (010 ()))
    ((010 (011 rest)) (100 rest))
    ((010 ())
     (111 (001 110)
       (111
         (111 (100 rest)
           (111
             (111 (001 and) (011 rest))
             (001 ())))
         (111
           (111 (001 010)
             (111 (001 ()) (001 ())))
           (111
             (111
               (001 010)
               (111
                 (111 (001 111)
                   (111 (001 ())
                     (111 (001 ()) (001 ()))))
                 (001 ())))
             (001 ()))))))))))

(0011 or
  (make-macro
    (0010 rest
  (110
    ((010 rest) (010 (111 () ())))
    ((010 (011 rest)) (100 rest))
    ((010 ())
     (111 (001 110)
       (111
         (111 (100 rest)
           (111
             (111 (001 010)
               (111 (001 ()) (001 ())))
             (001 ())))
         (111
           (111
             (111 (001 010)
               (111 (001 ()) (001 ())))
             (111
               (111 (001 or) (011 rest))
               (001 ())))
           (001 ())))))))))

; gensym — my-lisp's defmacro is unhygienic by default (no automatic
; protection against accidental variable capture; verified live
; 2026-08-27, see docs/macro-hygiene-2026-08-27.md's own capture demo).
; This is the "fresh name" tool a macro author reaches for when a name
; must NOT be visible/capturable at the call site -- built entirely
; from existing primitives, zero new Rust code, zero new language
; machinery: mono-ns (monotonic, real-time-independent counter) makes
; each call's suffix distinct, write-to-string/string-append/
; string->symbol assemble it into a real symbol. Requires an explicit
; prefix (no default-prefix convenience yet -- G5: earn that later if
; a real caller needs it, don't build it speculatively now).
(0011 gensym
  (0010 (prefix)
    (string->symbol (110011110 prefix (write-to-string (mono-ns))))))

(0011 pair
  (0010 (left right)
    (111 left (111 right (001 ())))))

; D4:1000 CAAR | D4:1001 CADR | D4:0111 CDDR
; D5:10011 CADDR is executable; D6 selector coordinates are ratified,
; but not physically admitted as call heads. Never manufacture D6 dispatch.
; fourth = D5 CADDR ∘ D3 CDR; fifth = D5 CADDR ∘ D4 CDDR.
; D7 is text data, not an escape hatch for deeper selectors.

(0011 second
  (0010 (values)
    (1001 values)))

(0011 third
  (0010 (values)
    (10011 values)))

(0011 fourth
  (0010 (values)
    (10011 (011 values))))

; D8:01100000..01100111 — ратифіковані похідні 6-крокові селектори.
; Точні D8 координати не дають прямої викличності. Закон = D3 CAR/CDR.
; D8:01100000 CDAAAAAR
(0011 р-п-п-п-п-п
  (0010 (x)
    (011 (100 (100 (100 (100 (100 x))))))))

; D8:01100001 CDAAAADR
(0011 р-п-п-п-п-р
  (0010 (x)
    (011 (100 (100 (100 (100 (011 x))))))))

; D8:01100010 CDAAADAR
(0011 р-п-п-п-р-п
  (0010 (x)
    (011 (100 (100 (100 (011 (100 x))))))))

; D8:01100011 CDAAADDR
(0011 р-п-п-п-р-р
  (0010 (x)
    (011 (100 (100 (100 (011 (011 x))))))))

; D8:01100100 CDAADAAR
(0011 р-п-п-р-п-п
  (0010 (x)
    (011 (100 (100 (011 (100 (100 x))))))))

; D8:01100101 CDAADADR
(0011 р-п-п-р-п-р
  (0010 (x)
    (011 (100 (100 (011 (100 (011 x))))))))

; D8:01100110 CDAADDAR
(0011 р-п-п-р-р-п
  (0010 (x)
    (011 (100 (100 (011 (011 (100 x))))))))

; D8:01100111 CDAADDDR
(0011 р-п-п-р-р-р
  (0010 (x)
    (011 (100 (100 (011 (011 (011 x))))))))

; Похідна D5 селекторна родина. Нормативні коди — lib/domains/d5.lisp.
; Порядок букв зовнішній→внутрішній, виконання CAR/CDR внутрішній→зовнішній.
; Це визначення поверхневих функцій, не допуск прямого D5 call-head.
; D5:01100 р-п-п
(0011 р-п-п
  (0010 (x)
    (011 (100 (100 x)))))

; D5:01101 р-п-р
(0011 р-п-р
  (0010 (x)
    (011 (100 (011 x)))))

; D5:01110 р-р-п
(0011 р-р-п
  (0010 (x)
    (011 (011 (100 x)))))

; D5:01111 р-р-р
(0011 р-р-р
  (0010 (x)
    (011 (011 (011 x)))))

; D5:10000 п-п-п
(0011 п-п-п
  (0010 (x)
    (100 (100 (100 x)))))

; D5:10001 п-п-р
(0011 п-п-р
  (0010 (x)
    (100 (100 (011 x)))))

; D5:10010 п-р-п
(0011 п-р-п
  (0010 (x)
    (100 (011 (100 x)))))

; D5:10011 п-р-р
(0011 п-р-р
  (0010 (x)
    (100 (011 (011 x)))))

; cadddr — the classical car/cdr-composition name for the exact same
; operation fourth already performs; kept as an alias (same closure
; object, not a second definition) since real callers already spell it
; this way (lib/reason.lisp had its own local (def cadddr ...) before
; this, character-for-character identical to fourth's body).
; cadddr — класична car/cdr-композиційна назва для тієї самої операції,
; що вже виконує fourth; лишено як псевдонім (той самий об'єкт-closure,
; не друге визначення), бо реальні виклики вже пишуть саме так
; (lib/reason.lisp мав власний локальний (def cadddr ...) до цього,
; посимвольно ідентичний тілу fourth).
(0011 cadddr fourth)

; fifth — same single-parameter primitive-chain pattern as second/third/
; fourth, one step deeper. Found duplicated in two places at once:
; lib/narrate.lisp's own local (def fifth ...), character-for-character
; identical, and lib/persistent-map.lisp's node-right, same operation
; spelled out by hand rather than named.
; fifth — той самий однопараметричний ланцюжок примітивів, що й
; second/third/fourth, ще на крок глибший. Знайдено дубльованим одразу
; у двох місцях: власний локальний (def fifth ...) у lib/narrate.lisp,
; посимвольно ідентичний, і node-right у lib/persistent-map.lisp — та
; сама операція, виписана вручну замість названа.
(0011 fifth
  (0010 (values)
    (10011 (0111 values))))

(0011 caar
  (0010 (values)
    (1000 values)))

(0011 cadr second)

(0011 cddr
  (0010 (values)
    (0111 values)))

; length/map/filter build their result via a tail-recursive `-onto`
; accumulator, same shape as reverse/reverse-onto below, instead of consing
; after the recursive call returns (the way append naively would if it
; didn't reuse reverse/reverse-onto) — that non-tail shape grows the Rust
; call stack one frame per element, same risk `crates/my-lisp/tests/stack_safety.rs`
; exists to catch for the language's own tail calls. map/filter accumulate
; in reverse order, so they call `reverse` once at the end to undo that;
; length doesn't build a list at all, so it just returns its accumulator.
; length/map/filter будують результат через хвостово-рекурсивний
; `-onto`-акумулятор, тієї самої форми, що й reverse/reverse-onto нижче,
; замість консити після повернення з рекурсивного виклику (як append робив
; би наївно, якби не перевикористовував reverse/reverse-onto) — та
; не-хвостова форма ростить Rust call stack на один фрейм на елемент, той
; самий ризик, який `crates/my-lisp/tests/stack_safety.rs` існує, щоб
; ловити для власних хвостових викликів мови. map/filter накопичують у
; зворотному порядку, тож викликають `reverse` раз наприкінці, щоб це
; скасувати; length взагалі не будує список, тож просто повертає свій
; акумулятор.
; length/map/filter bauen ihr Ergebnis über einen endrekursiven
; `-onto`-Akkumulator auf, derselben Form wie reverse/reverse-onto unten,
; statt nach der Rückkehr des rekursiven Aufrufs zu konsen (wie append es
; naiv täte, würde es nicht reverse/reverse-onto wiederverwenden) — diese
; Nicht-Tail-Form lässt den Rust-Call-Stack um einen Frame pro Element
; wachsen, dasselbe Risiko, das `crates/my-lisp/tests/stack_safety.rs` für
; die eigenen Tail Calls der Sprache abfängt. map/filter akkumulieren in
; umgekehrter Reihenfolge und rufen daher am Ende einmal `reverse` auf, um
; das rückgängig zu machen; length baut gar keine Liste, sondern gibt
; einfach seinen Akkumulator zurück.
(0011 довжина-до
  (0010 (значення акумулятор)
    (110 ((0101 значення) акумулятор) ((0100 (0101 значення)) (довжина-до (011 значення) (01010 акумулятор #d24:000000000000000000000001))))))
(0011 length-onto довжина-до)


(0011 довжина
  (0010 (значення)
    (довжина-до значення #d24:000000000000000000000000)))
(0011 length довжина)

; D5:10101 REVERSE-ONTO: canonical ratified surface owns the exact-domain
; binding. The historical English spelling below is compatibility-only.
(0011 зворот-до
  (0010 (values acc)
    (110
      ((0101 values) acc)
      ((0100 (010 values))
       (зворот-до (011 values) (111 (100 values) acc))))))

(0011 reverse-onto зворот-до)

; D5:10100 ЗВОРОТ. Канонічне українське визначення через D5:10101.
(0011 зворот
  (0010 (значення)
    (зворот-до значення (001 ()))))
(0011 reverse зворот)

; D5:01000 ZEROP — похідний мовний закон тільки для допущених чисел D24+.
; У адитивній групі x = x+x рівносильне x = 0.
; D5:01010 PLUS перевіряє числовий домен, D3:101 EQ повертає D1.
(0011 нуль?
  (0010 (значення)
    (101 значення (01010 значення значення))))
; Та сама closure для явно типізованого зовнішнього написання тесту.
(0011 нуль-д24? нуль?)



; D5 PLUS/DIFFERENCE/TIMES/LESSP/GREATERP already have immutable
; exact-domain value-call mechanisms. Their canonical surfaces come from
; lib/domains/d5.lisp; do not rebind those immutable names in Core4.

; (reverse-onto (reverse left) right): reversing left first and then
; consing it back onto right, one element at a time, rebuilds
; left ++ right in the correct order — two tail-recursive passes instead
; of one non-tail pass, trading a little work for a Rust-stack-safe append.
; (reverse-onto (reverse left) right): спершу розвертаємо left, а тоді
; консимо його назад на right по елементу — відбудовує left ++ right у
; правильному порядку — два хвостово-рекурсивні проходи замість одного
; не-хвостового, невелика доплата роботою заради append, безпечного для
; Rust-стека.
; (reverse-onto (reverse left) right): left zuerst umkehren und dann
; Element für Element wieder auf right konsen, baut left ++ right in
; korrekter Reihenfolge wieder auf — zwei endrekursive Durchläufe statt
; eines Nicht-Tail-Durchlaufs, ein kleiner Mehraufwand für ein
; Rust-Stack-sicheres append.
(0011 append
  (0010 (left right)
    (зворот-до (10100 left) right)))

(0011 відобразити-до
  (0010 (дія значення акумулятор)
    (110 ((0101 значення) (зворот акумулятор)) ((0100 (0101 значення)) (відобразити-до дія (011 значення) (111 (дія (100 значення)) акумулятор))))))
(0011 map-onto відобразити-до)

; D6:101000 MAP: native SENS recursion over a proper list.
; D4:0101 NULL ends exactly the empty list; D3:111 CONS preserves order.
(0011 відобразити
  (0010 (дія значення)
    (110
      ((0101 значення) (001 ()))
      ((010 (001 ()))
       (111 (дія (100 значення))
            (відобразити дія (011 значення)))))))
(0011 map відобразити)

(0011 відсіяти-до
  (0010 (предикат значення акумулятор)
    (110 ((0101 значення) (зворот акумулятор)) ((0100 (0101 значення)) (let ((рішення (предикат (100 значення)))) (110 (рішення (відсіяти-до предикат (011 значення) (111 (100 значення) акумулятор))) ((not? рішення) (відсіяти-до предикат (011 значення) акумулятор))))))))
(0011 filter-onto відсіяти-до)

; D6:101001 FILTER: predicate must return an exact D1 bit.
; Retain only the D1:YES heads; empty list returns structural D3:000.
(0011 відсіяти
  (0010 (умова значення)
    (110
      ((0101 значення) (001 ()))
      ((умова (100 значення))
       (111 (100 значення) (відсіяти умова (011 значення))))
      ((010 (001 ()))
       (відсіяти умова (011 значення))))))
(0011 filter відсіяти)

; D6:101110 REDUCE: the law is Lisp-owned, not an implicit D6 opcode.
; D4:0101 NULL ends precisely an empty proper list. D3 CAR/CDR step only a pair.
; Provenance: knowledge/d6-v2-binary-law-families.json, family f10.
(0011 згорнути
  (0010 (операція стан елементи)
    (110
      ((0101 елементи) стан)
      ((010 (001 ()))
       (згорнути операція
         (операція стан (100 елементи))
         (011 елементи))))))

(0011 reduce згорнути)

; `let` desugars to an immediately-invoked `lambda`: `(let ((x 1) (y 2)) body)`
; expands to `((lambda (x y) body) 1 2)` — the classic trick, same shape as
; the `unless` example in docs/quote-tutorial.md. Bindings are evaluated in
; the *outer* environment before the new lexical frame exists (so
; `(let ((x 1) (y x)) ...)` fails — `y`'s value expression can't see `x`
; yet), matching Scheme/Racket's parallel `let`. Exactly two arguments,
; `body` a single expression: `defmacro` uses the same fixed-arity
; parameter binding as `lambda` (see docs/language-core.md), so there is no
; variadic/rest-body support to lean on. For a sequence of expressions,
; wrap them the same way the rest of this codebase already does —
; `(let (...) ((lambda () expr1 expr2)))`.
; `let` розгортається в негайно викликану `lambda`: `(let ((x 1) (y 2))
; тіло)` розгортається в `((lambda (x y) тіло) 1 2)` — класичний прийом,
; тієї самої форми, що й приклад `unless` у docs/quote-tutorial.md.
; Bindings обчислюються в *зовнішньому* середовищі до того, як з'явиться
; новий лексичний фрейм (тож `(let ((x 1) (y x)) ...)` провалиться — вираз
; значення `y` ще не бачить `x`), як і паралельний `let` у Scheme/Racket.
; Рівно два аргументи, `body` — один вираз: `defmacro` використовує те
; саме зв'язування параметрів фіксованої арності, що й `lambda` (див.
; docs/language-core.md), тож немає variadic/rest-body, на яке можна
; спертись. Для послідовності виразів загортай так само, як і решта цього
; коду вже робить — `(let (...) ((lambda () вираз1 вираз2)))`.
; `let` entzuckert sich zu einem sofort aufgerufenen `lambda`:
; `(let ((x 1) (y 2)) rumpf)` wird zu `((lambda (x y) rumpf) 1 2)` — der
; klassische Trick, dieselbe Form wie das `unless`-Beispiel in
; docs/quote-tutorial.md. Bindings werden in der *äußeren* Umgebung
; ausgewertet, bevor der neue lexikalische Frame existiert (daher
; scheitert `(let ((x 1) (y x)) ...)` — der Wertausdruck von `y` sieht `x`
; noch nicht), passend zu Schemes/Rackets parallelem `let`. Genau zwei
; Argumente, `body` ein einzelner Ausdruck: `defmacro` nutzt dieselbe
; Parameterbindung fester Arität wie `lambda` (siehe docs/language-core.md),
; es gibt also kein variadisches/Rest-Body, auf das man sich stützen
; könnte. Für eine Folge von Ausdrücken genauso einpacken, wie es der
; Rest dieses Codes bereits tut — `(let (...) ((lambda () ausdruck1 ausdruck2)))`.
; Build the parallel LET expansion from current D3 list and predicate laws.
; Do not depend on legacy list/map helpers whose predicates may return (1)/(0)
; while executing under strict D3:110 COND.
(0011 core4-let-parameters
  (0010 (bindings)
    (110
      ((010 bindings) (001 ()))
      ((010 (001 ()))
       (111
         (100 (100 bindings))
         (core4-let-parameters (011 bindings)))))))

(0011 core4-let-values
  (0010 (bindings)
    (110
      ((010 bindings) (001 ()))
      ((010 (001 ()))
       (111
         (100 (011 (100 bindings)))
         (core4-let-values (011 bindings)))))))

(0011 let
  (make-macro
    (0010 (bindings body)
  (111
    (111
      (001 00001000)
      (111
        (core4-let-parameters bindings)
        (111 body (001 ()))))
    (core4-let-values bindings)))))

; `let*` is `let` with sequential (not parallel) dependency: each binding's
; value expression can see every binding before it. Expands recursively —
; `(let* ((x 1) (y (+ x 1))) body)` becomes
; `(let ((x 1)) (let* ((y (+ x 1))) body))`, peeling one binding into its
; own nested `let` at a time until none are left, at which point `body`
; evaluates directly. Each expansion step is itself new code handed back to
; the evaluator, the same macro-expansion mechanism `unless` and `let`
; already use — `let*` calling `let*` is ordinary recursion, not a special
; case the evaluator needs to know about.
; `let*` — це `let` з послідовною (не паралельною) залежністю: вираз
; значення кожного binding бачить усі попередні. Розгортається
; рекурсивно — `(let* ((x 1) (y (+ x 1))) тіло)` стає
; `(let ((x 1)) (let* ((y (+ x 1))) тіло))`, знімаючи по одному binding у
; власний вкладений `let`, поки жодного не лишиться, і тоді `тіло`
; обчислюється напряму. Кожен крок розгортання сам є новим кодом,
; переданим назад evaluator'у, тим самим механізмом розгортання макросів,
; що вже використовують `unless` і `let` — виклик `let*` із `let*` —
; звичайна рекурсія, не особливий випадок, про який має знати evaluator.
; `let*` ist `let` mit sequenzieller (nicht paralleler) Abhängigkeit: der
; Wertausdruck jedes Bindings sieht alle vorherigen. Entfaltet sich
; rekursiv — `(let* ((x 1) (y (+ x 1))) rumpf)` wird zu
; `(let ((x 1)) (let* ((y (+ x 1))) rumpf))`, wobei jeweils ein Binding in
; ein eigenes verschachteltes `let` geschält wird, bis keines mehr übrig
; ist, woraufhin `rumpf` direkt ausgewertet wird. Jeder Entfaltungsschritt
; ist selbst neuer Code, der an den Evaluator zurückgegeben wird, derselbe
; Makro-Expansionsmechanismus, den `unless` und `let` bereits nutzen —
; `let*`, das `let*` aufruft, ist gewöhnliche Rekursion, kein Sonderfall,
; von dem der Evaluator wissen müsste.
; `eq` is deliberately atom-only per McCarthy's original primitive (see
; docs/language-core.md) — `(eq '(1 2) '(1 2))` errors rather than comparing
; structurally. `equal?` is the structural/deep-equality counterpart, built
; on top of `eq` and `atom` rather than replacing them. Its answer is the
; Core4 15-state scale (#1391): `(1)` — the same structure, `(0)` — different.
; Canonical three-part `cond` consumes the answer explicitly; a two-part
; clause selects only on a «yes» answer.
(0011 equal?
  (0010 (a b)
    (110
      ((010 a)
       (110
         ((010 b) (101 a b))
         ((010 ()) (010 (001 (0))))))
      ((010 b) (010 (001 (0))))
      ((equal? (100 a) (100 b))
       (equal? (011 a) (011 b)))
      ((010 ()) (010 (001 (0)))))))

; NOT is a strict PredicateBit combinator. Any non-D1 input is rejected by
; D3 COND instead of being coerced through retired host truthiness.
(0011 not?
  (0010 (value)
    (110
      (value (010 (001 (0))))
      ((010 ()) (010 ())))))


; nth/member?/assoc (G5 test: already expressible via existing means?)
; — yes, same recursive-list-walk shape as length/reverse above.
; Surfaced from the fpga-lisp session's assembler.lisp (2026-08-10), which
; had independently reimplemented all three locally (as nth, contains?/
; any-eq?, and assoc-str) because lib/core.lisp didn't have them — real,
; evidenced duplication, not a speculative gap. A generalized assoc here
; also matches the shape lib/meta-eval.lisp's own env-lookup already hand-
; rolls for its specific (symbol . value) alist case.
; nth/member?/assoc (G5-тест: уже виразне через наявне?) — так, та сама
; форма рекурсивного обходу списку, що й length/reverse вище. Знахідка
; з сесії fpga-lisp, assembler.lisp (2026-08-10), яка незалежно
; перевинайшла всі три локально (як nth, contains?/any-eq? і assoc-str),
; бо lib/core.lisp їх не мав — реальне, доказове дублювання, не
; спекулятивна прогалина. Узагальнений assoc тут також збігається з
; формою, яку lib/meta-eval.lisp's власний env-lookup уже вручну пише для
; свого специфічного випадку asoc-списку (symbol . value).
; D6:000100 NTH — індекс тільки явно кваліфікований D24, відлік від нуля.
; Порожній хвіст / завеликий індекс повертає (); не викликаємо 000100 як число.
(0011 елемент-списку
  (0010 (індекс елементи)
    (110
      ((0101 елементи) (001 ()))
      ((0100 (0101 елементи))
       (110
         ((101 індекс #d24:000000000000000000000000) (100 елементи))
         ((0100 (101 індекс #d24:000000000000000000000000))
          (елемент-списку
            (01011 індекс #d24:000000000000000000000001)
            (011 елементи))))))))

(0011 nth елемент-списку)

; D5:11101 MEMBER. Точне D1 рішення і хвостова рекурсія.
(0011 значення-у-списку?
  (0010 (item lst)
    (110
      ((0101 lst) (010 (001 (0))))
      ((equal? item (100 lst)) (010 ()))
      ((010 ()) (значення-у-списку? item (011 lst))))))
(0011 member? значення-у-списку?)

; D5:11100 ASSOC. Один структурний пошук через D3 CAR/CDR.
(0011 знайти-за-ключем
  (0010 (key alist)
    (110
      ((0101 alist) (001 ()))
      ((equal? key (100 (100 alist))) (100 alist))
      ((010 ()) (знайти-за-ключем key (011 alist))))))
(0011 assoc знайти-за-ключем)


; D5:11110 PAIRLIS: Lisp-owned structural law. Canonical Ukrainian surface
; owns the exact-domain binding; English spelling is compatibility-only.
(0011 спарувати
  (0010 (keys values tail)
    (110
      ((0100 (010 keys)) tail)
      ((010 keys) 
       (111
         (111 (100 keys) (100 values))
         (спарувати (011 keys) (011 values) tail))))))

(0011 pairlis спарувати)

(0011 let*
  (make-macro
    (0010 (bindings body)
  ; D3 ATOM повертає точний D1:1 для порожнього списку прив'язок.
  ; Непорожні прив'язки переходять до рекурсивного LET через D1:1 за замовчуванням.
  (110
    ((010 bindings) body)
    ((010 (001 ())) 
     ; Build the recursive expansion from the primitive tree substrate only.
     ; This keeps let* semantics in Lisp while allowing generic macro
     ; frontends to execute the law without importing the higher-level list
     ; helper as host/compiler semantic authority.
     (111 (001 let)
           (111 (111 (100 bindings) (001 ()))
                 (111 (111 (001 let*)
                             (111 (011 bindings)
                                   (111 body (001 ()))))
                       (001 ())))))))))

; D6:001011 COMPOSE / D6:101101 FLIP — похідні функції, виведені лише з D4 lambda.
; Координати вже ратифіковані (lib/domains/d6.lisp), механізм — ні
; (knowledge/d6-mechanism-ledger.json: mechanism_status=MISSING). Визначаємо їх
; мовою SENS через наявний D4:0010 LAMBDA, без нових координат і без Rust.
; `скласти-функції f g` → (λ (x) (f (g x))) — права композиція.
(0011 скласти-функції
  (0010 (f g)
    (0010 (x)
      (f (g x)))))

; `поміняти-аргументи f` → (λ (a b) (f b a)) — зміна порядку двох аргументів.
(0011 поміняти-аргументи
  (0010 (f)
    (0010 (a b)
      (f b a))))

; D6:001101 — ACONS, приєднати пару ключ/значення до асоціацій.
; Лише два D3:111 CONS; без direct D6 callability.
(0011 додати-асоціацію
  (0010 (ключ значення асоціації)
    (111 (111 ключ значення) асоціації)))



; D6:001110 ADD1 / D6:001111 SUB1 — purely derived D24+ arithmetic.
; D5:01010 PLUS and D5:01011 DIFFERENCE preserve the qualified mathematical carrier.
; No implied arithmetic on D1-D10 identities, no new direct D6 call admission.
(0011 додати-1
  (0010 (значення)
    (01010 значення #d24:000000000000000000000001)))

(0011 відняти-1
  (0010 (значення)
    (01011 значення #d24:000000000000000000000001)))

(0011 add1 додати-1)
(0011 sub1 відняти-1)

; ===== D6 derived functions (партія 1: 16 селекторів; партія 2: арифметичні/предикатні похідні) =====
; Ратифіковані координати lib/domains/d6.lisp; механізм = SENS-визначення через D3/D4/D5.
; Нових координат не створюємо; одне джерело семантики — SENS.

; cdaaar (р-п-п-п)
(0011 р-п-п-п
  (0010 (x)
    (011 (100 (100 (100 x))))))

; cdaadr (р-п-п-р)
(0011 р-п-п-р
  (0010 (x)
    (011 (100 (100 (011 x))))))

; cdadar (р-п-р-п)
(0011 р-п-р-п
  (0010 (x)
    (011 (100 (011 (100 x))))))

; cdaddr (р-п-р-р)
(0011 р-п-р-р
  (0010 (x)
    (011 (100 (011 (011 x))))))

; cddaar (р-р-п-п)
(0011 р-р-п-п
  (0010 (x)
    (011 (011 (100 (100 x))))))

; cddadr (р-р-п-р)
(0011 р-р-п-р
  (0010 (x)
    (011 (011 (100 (011 x))))))

; cdddar (р-р-р-п)
(0011 р-р-р-п
  (0010 (x)
    (011 (011 (011 (100 x))))))

; cddddr (р-р-р-р)
(0011 р-р-р-р
  (0010 (x)
    (011 (011 (011 (011 x))))))

; caaaar (п-п-п-п)
(0011 п-п-п-п
  (0010 (x)
    (100 (100 (100 (100 x))))))

; caaadr (п-п-п-р)
(0011 п-п-п-р
  (0010 (x)
    (100 (100 (100 (011 x))))))

; caadar (п-п-р-п)
(0011 п-п-р-п
  (0010 (x)
    (100 (100 (011 (100 x))))))

; caaddr (п-п-р-р)
(0011 п-п-р-р
  (0010 (x)
    (100 (100 (011 (011 x))))))

; cadaar (п-р-п-п)
(0011 п-р-п-п
  (0010 (x)
    (100 (011 (100 (100 x))))))

; cadadr (п-р-п-р)
(0011 п-р-п-р
  (0010 (x)
    (100 (011 (100 (011 x))))))

; caddar (п-р-р-п)
(0011 п-р-р-п
  (0010 (x)
    (100 (011 (011 (100 x))))))

; cadddr (п-р-р-р)
(0011 п-р-р-р
  (0010 (x)
    (100 (011 (011 (011 x))))))

; add1 (збільшити-на-один)
(0011 збільшити-на-один
  (0010 (x)
    (додати x #d24:000000000000000000000001)))

; sub1 (зменшити-на-один)
(0011 зменшити-на-один
  (0010 (x)
    (відняти x #d24:000000000000000000000001)))

; neg (змінити-знак)
(0011 змінити-знак
  (0010 (x)
    (відняти #d24:000000000000000000000000 x)))

; recip (обернене)
(0011 обернене
  (0010 (x)
    (частка #d24:000000000000000000000001 x)))

; leq? (не-більше?)
; Партія D6 з дослідження #3622: LEFT TAKE / DROP для невід'ємного D24+ n.
; Резидентні коди D6:110000 / D6:110001, не D8-right aliases.
; У тілі лише D5 ZEROP, D6 SUB1, D3 CAR/CDR/CONS/COND, D4 NULL.
(0011 взяти
  (0010 (кількість елементи)
    (110
      ((нуль? кількість) (001 ()))
      ((0101 елементи) (001 ()))
      ((0101 (001 ()))
       (111 (100 елементи)
            (взяти (001111 кількість) (011 елементи)))))))

(0011 відкинути
  (0010 (кількість елементи)
    (110
      ((нуль? кількість) елементи)
      ((0101 елементи) (001 ()))
      ((0101 (001 ()))
       (відкинути (001111 кількість) (011 елементи))))))

; D8:00100001 SUBSEQ — лише списки та кваліфіковані D24 межі.
; На 0 <= початок <= кінець <= LENGTH(елементи):
; SUBSEQ(xs,a,b) = D6:110000 TAKE(D5:01011 (b-a), D6:110001 DROP(a,xs)).
; Визначення власне SENS; це не прямий допуск D8:bits.
(0011 підпослідовність
  (0010 (елементи початок кінець)
    (взяти (01011 кінець початок)
           (відкинути початок елементи))))

(0011 не-більше?
  (0010 (a b) (0100 (11011 a b))))

; geq? (не-менше?)
(0011 не-менше?
  (0010 (a b) (0100 (11010 a b))))


; ===== D6 derived (партія 3) =====
; remainder (остача)
(0011 остача
  (0010 (a b) (mod a b)))
; gcd (нсд)
(0011 нсд
  (0010 (a b)
    (110 ((01000 b) a) (#d1:1 (нсд b (mod a b))))))
; expt (піднести-до-степеня)
(0011 піднести-до-степеня
  (0010 (b n)
    (110 ((01000 n) 1) (#d1:1 (10110 b (піднести-до-степеня b (01011 n 1)))))))
; rassoc (знайти-за-значенням)
(0011 знайти-за-значенням
  (0010 (v al)
    (110 ((010 al) ()) (#d1:1 (110 ((101 v (011 (100 al))) (100 al)) (#d1:1 (знайти-за-значенням v (011 al))))))))
; intersection (перетин)
(0011 перетин
  (0010 (a b) (filter (0010 (x) (member? x b)) a)))
; union (об'єднання)
(0011 об'єднання
  (0010 (a b)
    (110 ((010 a) b) (#d1:1 (110 ((member? (100 a) b) (об'єднання (011 a) b)) (#d1:1 (111 (100 a) (об'єднання (011 a) b))))))))


; ===== D6 derived (партія 4) =====
; evenp (парне?)
(0011 парне?
  (0010 (x) (01000 (mod x 2))))
; oddp (непарне?)
(0011 непарне?
  (0010 (x) (0100 (01000 (mod x 2)))))
; integerp (ціле?)
(0011 ціле?
  (0010 (x) (01001 x)))
; rationalp (раціональне?)
(0011 раціональне?
  (0010 (x) (01001 x)))
; D6:111100 ANY — екзистенційний обхід D3 CAR/CDR і D4 NULL.
; Порожній список: D1:NO; знайдений свідок: D1:YES. FILTER не потрібен.
(0011 будь-яке?
  (0010 (умова елементи)
    (110
      ((0101 елементи) (0100 (0101 (001 ()))))
      ((умова (100 елементи)) (0101 (001 ())))
      ((010 (001 ())) (будь-яке? умова (011 елементи))))))

; D6:111101 ALL — універсальний обхід, порожній список = D1:YES.
; Відмова при першому D1:NO, не через host truthiness чи FILTER.
(0011 усі?
  (0010 (умова елементи)
    (110
      ((0101 елементи) (0101 (001 ())))
      ((умова (100 елементи)) (усі? умова (011 елементи)))
      ((010 (001 ())) (0100 (0101 (001 ())))))))


; ===== D6 derived (партія 5) =====
; curry (частково-застосувати)
(0011 частково-застосувати
  (0010 (f x)
    (0010 (y)
      (f x y))))
; scan (накопичувати)
; D6:101111 SCAN: terminal(last) = D6:101110 REDUCE на непорожніх
; proper lists; порожня presentation залишається () (#3370/#3674).
; Допоміжна функція повертає початковий і кожен наступний стан, включно
; з остаточним. Це власне мовна рекурсія, не новий opcode.
(0011 накопичувати-до
  (0010 (дія стан елементи)
    (110
      ((0101 елементи) (111 стан (001 ())))
      ((010 (001 ()))
       (111 стан (накопичувати-до дія
                                  (дія стан (100 елементи))
                                  (011 елементи)))))))

(0011 накопичувати
  (0010 (дія стан елементи)
    (110
      ((0101 елементи) (001 ()))
      ((010 (001 ()))
       (накопичувати-до дія стан елементи)))))
; unzip (розпарувати-пари)
(0011 розпарувати-пари
  (0010 (ps)
    (111 (map (0010 (p) (100 p)) ps) (map (0010 (p) (011 p)) ps))))
; zip (спарувати-послідовності)
(0011 спарувати-послідовності
  (0010 (a b)
    (110 ((010 a) ())
      ((010 b) ())
      (#d1:1 (111 (111 (100 a) (100 b)) (спарувати-послідовності (011 a) (011 b)))))))


; D8:11100001 ZIP-swapped / D8:11100011 UNZIP-swapped.
; Ратифіковані координати #3960, product law #3710, без нових opcode.
; Похідні від D6:111000 і D6:111001. Точні слова не розширюються.
(0011 спарувати-навпаки
  (0010 (ліві праві)
    (спарувати-послідовності праві ліві)))

(0011 розпарувати-навпаки
  (0010 (пари)
    ((0010 (результат)
       (111 (100 (011 результат))
            (111 (100 результат) (001 ()))))
     (розпарувати-пари пари))))

; D8:11110001 = ANY(NOT p), ратифікований добутковий кут.
; Лише SENS-похідна реалізація на D6:111100 ANY + D4:0100 NOT.
(0011 є-що-не-задовольняє?
  (0010 (p значення)
    (будь-яке? (0010 (x) (0100 (p x))) значення)))

; D8:11110011 = ALL(NOT p), включно з порожнім списком.
; Лише SENS-похідна реалізація на D6:111101 ALL + D4:0100 NOT.
(0011 усі-не-задовольняють?
  (0010 (p значення)
    (усі? (0010 (x) (0100 (p x))) значення)))


; D8:01010111 NOTANY — ратифікована точна координата #3960.
; Похідний закон: NOTANY(p,xs) = D4:0100 NOT(D6:111100 ANY(p,xs)).
; Точний D1 PredicateBit, без виклику D8-примітива або нової семантики.
(0011 жодне-не-задовольняє?
  (0010 (умова елементи)
    (хибне? (будь-яке? умова елементи))))


; D8:00110011 ACONS-SWAPPED — чинна продуктова координата #3960.
; Закон орієнтації #3741: tau(ACONS(k,v,A)) = ACONS(v,k,tau(A)).
; tau(pair) = CONS(CDR(pair),CAR(pair)); D6 MAP зберігає порядок alist.
; Лише мовна похідна функція SENS, не новий D8 primitive.
(0011 додати-асоціацію-навпаки
  (0010 (ключ значення асоціації)
    (додати-асоціацію значення ключ
      (відобразити
        (функція (пара) (111 (011 пара) (100 пара)))
        асоціації))))

; D8:11000001 TAKE-right / D8:11000011 DROP-right — похідні закони.
; Дослідження #3622; тільки композиція D6 TAKE/DROP і D5 REVERSE.
; Кількість передається як D24+, прямої D8 callability не додається.
(0011 взяти-справа
  (0010 (кількість елементи)
    (зворот (взяти кількість (зворот елементи)))))
(0011 відкинути-справа
  (0010 (кількість елементи)
    (зворот (відкинути кількість (зворот елементи)))))


; D8 derived batch — owner-ratified D8 coordinates, SENS language laws only.
; D8:00010110 REVAPPEND = D5:10101 REVERSE-ONTO, same closure.
(0011 розвернути-й-приєднати зворот-до)

; D8:00001001 SUBSETP — D1-positive exact structural recursion.
(0011 підмножина?
  (0010 (ліві праві)
    (110
      ((0101 ліві) (010 (001 ())))
      ((значення-у-списку? (100 ліві) праві)
       (підмножина? (011 ліві) праві))
      ((010 (001 ())) (010 (111 (001 ()) (001 ())))))))

; D8:00111010 SET-DIFFERENCE — recursion without legacy LAMBDA carrier.
(0011 різниця-множин
  (0010 (ліві праві)
    (110
      ((0101 ліві) (001 ()))
      ((значення-у-списку? (100 ліві) праві)
       (різниця-множин (011 ліві) праві))
      ((010 (001 ()))
       (111 (100 ліві) (різниця-множин (011 ліві) праві))))))

; D8:00110110 ADJOIN — add a missing element at the front.
(0011 приєднати-якщо-нема
  (0010 (елемент список)
    (110
      ((значення-у-списку? елемент список) список)
      ((010 (001 ())) (111 елемент список)))))
; D8:01101000 CDADAAAR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-п-п-п
  (0010 (значення)
    (011 (100 (011 (100 (100 (100 значення))))))))

; D8:01101001 CDADAADR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-п-п-р
  (0010 (значення)
    (011 (100 (011 (100 (100 (011 значення))))))))

; D8:01101010 CDADADAR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-п-р-п
  (0010 (значення)
    (011 (100 (011 (100 (011 (100 значення))))))))

; D8:01101011 CDADADDR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-п-р-р
  (0010 (значення)
    (011 (100 (011 (100 (011 (011 значення))))))))

; D8:01101100 CDADDAAR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-р-п-п
  (0010 (значення)
    (011 (100 (011 (011 (100 (100 значення))))))))

; D8:01101101 CDADDADR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-р-п-р
  (0010 (значення)
    (011 (100 (011 (011 (100 (011 значення))))))))

; D8:01101110 CDADDDAR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-р-р-п
  (0010 (значення)
    (011 (100 (011 (011 (011 (100 значення))))))))

; D8:01101111 CDADDDDR: тільки точна композиція D3:100 CAR / D3:011 CDR.
(0011 р-п-р-р-р-р
  (0010 (значення)
    (011 (100 (011 (011 (011 (011 значення))))))))

; D8:00111001 ASSQ — пошук за EQ ключа, рівно атоми D3:101.
(0011 асоціація-тотожна
  (0010 (ключ асоціації)
    (110
      ((0101 асоціації) (001 ()))
      ((101 ключ (100 (100 асоціації))) (100 асоціації))
      ((010 (001 ())) (асоціація-тотожна ключ (011 асоціації))))))

; D8:00101010 ASSOC-IF — чинний закон застосовує предикат до CDR/значення.
; Не прирівнювати до історичної ASSOC-IF поверхні, яка тестує CAR/ключ.
(0011 знайти-асоціацію-якщо
  (0010 (предикат асоціації)
    (110
      ((0101 асоціації) (001 ()))
      ((предикат (011 (100 асоціації))) (100 асоціації))
      ((010 (001 ())) (знайти-асоціацію-якщо предикат (011 асоціації))))))
; D8:11011010 NTHCDR = D6:110001 DROP (lower-domain composition).
; D8:11100100 EVERY = D6:111101 ALL (strict D1 predicate result).
; Це мовні поверхні доведених нижчих законів, не нові незалежні примітиви.
(0011 n-та-решта відкинути)
(0011 усі-задовольняють? усі?)

; D8:10100000 COPY-LIST — поверхнева копія належного списку.
; D3:111 CONS будує тільки зовнішні клітинки; CAR зберігає вкладені об'єкти.
; D4:0101 NULL встановлює базовий випадок, без нової семантики в host.
(0011 копіювати-список
  (0010 (значення)
    (110
      ((0101 значення) (001 ()))
      ((0100 (0101 значення))
       (111 (100 значення) (копіювати-список (011 значення)))))))

; D8:01110000 CDDAAAAR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-п-п-п
  (0010 (значення)
    (011 (011 (100 (100 (100 (100 значення))))))))

; D8:01110001 CDDAAADR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-п-п-р
  (0010 (значення)
    (011 (011 (100 (100 (100 (011 значення))))))))

; D8:01110010 CDDAADAR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-п-р-п
  (0010 (значення)
    (011 (011 (100 (100 (011 (100 значення))))))))

; D8:01110011 CDDAADDR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-п-р-р
  (0010 (значення)
    (011 (011 (100 (100 (011 (011 значення))))))))

; D8:01110100 CDDADAAR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-р-п-п
  (0010 (значення)
    (011 (011 (100 (011 (100 (100 значення))))))))

; D8:01110101 CDDADADR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-р-п-р
  (0010 (значення)
    (011 (011 (100 (011 (100 (011 значення))))))))

; D8:01110110 CDDADDAR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-р-р-п
  (0010 (значення)
    (011 (011 (100 (011 (011 (100 значення))))))))

; D8:01110111 CDDADDDR — похідний шестикроковий CAR/CDR селектор.
(0011 р-р-п-р-р-р
  (0010 (значення)
    (011 (011 (100 (011 (011 (011 значення))))))))

; D8:01111000 CDDDAAAR — композиція D3 CAR/CDR.
(0011 р-р-р-п-п-п
  (0010 (значення)
    (011 (011 (011 (100 (100 (100 значення))))))))

; D8:01111001 CDDDAADR — композиція D3 CAR/CDR.
(0011 р-р-р-п-п-р
  (0010 (значення)
    (011 (011 (011 (100 (100 (011 значення))))))))

; D8:01111010 CDDDADAR — композиція D3 CAR/CDR.
(0011 р-р-р-п-р-п
  (0010 (значення)
    (011 (011 (011 (100 (011 (100 значення))))))))

; D8:01111011 CDDDADDR — композиція D3 CAR/CDR.
(0011 р-р-р-п-р-р
  (0010 (значення)
    (011 (011 (011 (100 (011 (011 значення))))))))

; D8:01111100 CDDDDAAR — композиція D3 CAR/CDR.
(0011 р-р-р-р-п-п
  (0010 (значення)
    (011 (011 (011 (011 (100 (100 значення))))))))

; D8:01111101 CDDDDADR — композиція D3 CAR/CDR.
(0011 р-р-р-р-п-р
  (0010 (значення)
    (011 (011 (011 (011 (100 (011 значення))))))))

; D8:01111110 CDDDDDAR — композиція D3 CAR/CDR.
(0011 р-р-р-р-р-п
  (0010 (значення)
    (011 (011 (011 (011 (011 (100 значення))))))))

; D8:01111111 CDDDDDDR — композиція D3 CAR/CDR.
(0011 р-р-р-р-р-р
  (0010 (значення)
    (011 (011 (011 (011 (011 (011 значення))))))))

; D8:10000000 CAAAAAAR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-п-п-п
  (0010 (значення)
    (100 (100 (100 (100 (100 (100 значення))))))))

; D8:10000001 CAAAAADR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-п-п-р
  (0010 (значення)
    (100 (100 (100 (100 (100 (011 значення))))))))

; D8:10000010 CAAAADAR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-п-р-п
  (0010 (значення)
    (100 (100 (100 (100 (011 (100 значення))))))))

; D8:10000011 CAAAADDR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-п-р-р
  (0010 (значення)
    (100 (100 (100 (100 (011 (011 значення))))))))

; D8:10000100 CAAADAAR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-р-п-п
  (0010 (значення)
    (100 (100 (100 (011 (100 (100 значення))))))))

; D8:10000101 CAAADADR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-р-п-р
  (0010 (значення)
    (100 (100 (100 (011 (100 (011 значення))))))))

; D8:10000110 CAAADDAR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-р-р-п
  (0010 (значення)
    (100 (100 (100 (011 (011 (100 значення))))))))

; D8:10000111 CAAADDDR: рівно шість D3 CAR/CDR операцій.
(0011 п-п-п-р-р-р
  (0010 (значення)
    (100 (100 (100 (011 (011 (011 значення))))))))

; D8:10101001 MAPCAN — застосувати дію до елементів і склеїти списки.
; D8:10111000 MAPCON — та сама композиція над послідовними хвостами.
; Виведення лише через чинні D3/D4 і D5 REVERSE/REVERSE-ONTO.
; Зворот-до(зворот(left), right) = APPEND(left,right); нових законів немає.
(0011 відобразити-й-склеїти
  (0010 (дія елементи)
    (110
      ((0101 елементи) (001 ()))
      ((0100 (0101 елементи))
       (зворот-до
         (зворот (дія (100 елементи)))
         (відобразити-й-склеїти дія (011 елементи)))))))

(0011 залишки+склеїти
  (0010 (дія елементи)
    (110
      ((0101 елементи) (001 ()))
      ((0100 (0101 елементи))
       (зворот-до
         (зворот (дія елементи))
         (залишки+склеїти дія (011 елементи)))))))

; D8:10001000 CAADAAAR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-п-п-п
  (0010 (значення)
    (100 (100 (011 (100 (100 (100 значення))))))))

; D8:10001001 CAADAADR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-п-п-р
  (0010 (значення)
    (100 (100 (011 (100 (100 (011 значення))))))))

; D8:10001010 CAADADAR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-п-р-п
  (0010 (значення)
    (100 (100 (011 (100 (011 (100 значення))))))))

; D8:10001011 CAADADDR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-п-р-р
  (0010 (значення)
    (100 (100 (011 (100 (011 (011 значення))))))))

; D8:10001100 CAADDAAR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-р-п-п
  (0010 (значення)
    (100 (100 (011 (011 (100 (100 значення))))))))

; D8:10001101 CAADDADR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-р-п-р
  (0010 (значення)
    (100 (100 (011 (011 (100 (011 значення))))))))

; D8:10001110 CAADDDAR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-р-р-п
  (0010 (значення)
    (100 (100 (011 (011 (011 (100 значення))))))))

; D8:10001111 CAADDDDR — точна композиція D3:100/D3:011, без нового opcode.
(0011 п-п-р-р-р-р
  (0010 (значення)
    (100 (100 (011 (011 (011 (011 значення))))))))

; D8:10010000 CADAAAAR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-п-п-п
  (0010 (значення)
    (100 (011 (100 (100 (100 (100 значення))))))))

; D8:10010001 CADAAADR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-п-п-р
  (0010 (значення)
    (100 (011 (100 (100 (100 (011 значення))))))))

; D8:10010010 CADAADAR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-п-р-п
  (0010 (значення)
    (100 (011 (100 (100 (011 (100 значення))))))))

; D8:10010011 CADAADDR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-п-р-р
  (0010 (значення)
    (100 (011 (100 (100 (011 (011 значення))))))))

; D8:10010100 CADADAAR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-р-п-п
  (0010 (значення)
    (100 (011 (100 (011 (100 (100 значення))))))))

; D8:10010101 CADADADR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-р-п-р
  (0010 (значення)
    (100 (011 (100 (011 (100 (011 значення))))))))

; D8:10010110 CADADDAR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-р-р-п
  (0010 (значення)
    (100 (011 (100 (011 (011 (100 значення))))))))

; D8:10010111 CADADDDR — D3 CAR/CDR без нового семантичного коду.
(0011 п-р-п-р-р-р
  (0010 (значення)
    (100 (011 (100 (011 (011 (011 значення))))))))

; D8:10011000 CADDAAAR — шість точних D3 CAR/CDR.
(0011 п-р-р-п-п-п
  (0010 (значення)
    (100 (011 (011 (100 (100 (100 значення))))))))

; D8:10011001 CADDAADR — шість точних D3 CAR/CDR.
(0011 п-р-р-п-п-р
  (0010 (значення)
    (100 (011 (011 (100 (100 (011 значення))))))))

; D8:10011010 CADDADAR — шість точних D3 CAR/CDR.
(0011 п-р-р-п-р-п
  (0010 (значення)
    (100 (011 (011 (100 (011 (100 значення))))))))

; D8:10011011 CADDADDR — шість точних D3 CAR/CDR.
(0011 п-р-р-п-р-р
  (0010 (значення)
    (100 (011 (011 (100 (011 (011 значення))))))))

; D8:10011100 CADDDAAR — шість точних D3 CAR/CDR.
(0011 п-р-р-р-п-п
  (0010 (значення)
    (100 (011 (011 (011 (100 (100 значення))))))))

; D8:10011101 CADDDADR — шість точних D3 CAR/CDR.
(0011 п-р-р-р-п-р
  (0010 (значення)
    (100 (011 (011 (011 (100 (011 значення))))))))

; D8:10011110 CADDDDAR — шість точних D3 CAR/CDR.
(0011 п-р-р-р-р-п
  (0010 (значення)
    (100 (011 (011 (011 (011 (100 значення))))))))

; D8:10011111 CADDDDDR — шість точних D3 CAR/CDR.
(0011 п-р-р-р-р-р
  (0010 (значення)
    (100 (011 (011 (011 (011 (011 значення))))))))

; D8:00010011 MAPLIST-right — чинна D8 координата (#3960).
; Закон #3744: MAPLIST(REVERSE(xs), lambda tail: f(REVERSE(tail))).
; Похідна SENS-функція на D5:10100 REVERSE і D6:000101 MAPLIST.
; Прямої D8 callability не надаємо, усі біти збережено.
(0011 залишки-справа
  (0010 (значення дія)
    (відобразити-залишки
      (зворот значення)
      (функція (хвіст) (дія (зворот хвіст))))))

; D8:00011101 LIST* — останній аргумент є точним хвостом CONS.
; Допоміжний рекурсивний код не отримує самостійної доменної координати.
(0011 неправильний-список-далі
  (0010 (частини)
    (110
      ((0101 (011 частини)) (100 частини))
      ((0100 (0101 (011 частини)))
       (111 (100 частини) (неправильний-список-далі (011 частини)))))))

(0011 неправильний-список
  (0010 (перший . додаткові-частини)
    (110
      ((0101 додаткові-частини) перший)
      ((0100 (0101 додаткові-частини))
       (111 перший (неправильний-список-далі додаткові-частини))))))

; D8:00111110 LENGTH-LIST та D8:01001111 LIST-LENGTH — дві
; ратифіковані історичні поверхні, похідні від D6:000000 LENGTH.
; Зберігається точний числовий результат D24 і вимога proper-list.
(0011 довжина-списку
  (0010 (значення)
    (довжина значення)))

(0011 список-довжина
  (0010 (значення)
    (довжина значення)))

; D8:00010001 NTH-right — ратифікована координата #3960.
; Закон #3744: NTH-right(i,xs) = D6:000100 NTH(i,D5:10100 REVERSE(xs)).
; Чиста похідна SENS-функція; D24+ індекс лишається явно кваліфікованим.
(0011 елемент-справа
  (0010 (індекс значення)
    (nth індекс (зворот значення))))

; D9:011000000 CDAAAAAAR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-п-п-п
  (0010 (значення)
    (011 (100 (100 (100 (100 (100 (100 значення)))))))))

; D9:011000001 CDAAAAADR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-п-п-р
  (0010 (значення)
    (011 (100 (100 (100 (100 (100 (011 значення)))))))))

; D9:011000010 CDAAAADAR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-п-р-п
  (0010 (значення)
    (011 (100 (100 (100 (100 (011 (100 значення)))))))))

; D9:011000011 CDAAAADDR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-п-р-р
  (0010 (значення)
    (011 (100 (100 (100 (100 (011 (011 значення)))))))))

; D9:011000100 CDAAADAAR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-р-п-п
  (0010 (значення)
    (011 (100 (100 (100 (011 (100 (100 значення)))))))))

; D9:011000101 CDAAADADR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-р-п-р
  (0010 (значення)
    (011 (100 (100 (100 (011 (100 (011 значення)))))))))

; D9:011000110 CDAAADDAR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-р-р-п
  (0010 (значення)
    (011 (100 (100 (100 (011 (011 (100 значення)))))))))

; D9:011000111 CDAAADDDR: 7 кроків D3:100 CAR та D3:011 CDR.
(0011 р-п-п-п-р-р-р
  (0010 (значення)
    (011 (100 (100 (100 (011 (011 (011 значення)))))))))

; D8:00010111 PLUSP / D8:11111010 MINUSP: strict signs on D24+ values.
; Numeric zero is derived as D5:01011 DIFFERENCE(x,x), never an unqualified literal.
; These are SENS-owned derived definitions, not direct D8 call-head admission.
(0011 додатне?
  (0010 (x) (менше? (відняти x x) x)))
(0011 від'ємне?
  (0010 (x) (менше? x (відняти x x))))

; D9:011001000 CDAADAAAR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-п-п-п
  (0010 (значення)
    (011 (100 (100 (011 (100 (100 (100 значення)))))))))

; D9:011001001 CDAADAADR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-п-п-р
  (0010 (значення)
    (011 (100 (100 (011 (100 (100 (011 значення)))))))))

; D9:011001010 CDAADADAR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-п-р-п
  (0010 (значення)
    (011 (100 (100 (011 (100 (011 (100 значення)))))))))

; D9:011001011 CDAADADDR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-п-р-р
  (0010 (значення)
    (011 (100 (100 (011 (100 (011 (011 значення)))))))))

; D9:011001100 CDAADDAAR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-р-п-п
  (0010 (значення)
    (011 (100 (100 (011 (011 (100 (100 значення)))))))))

; D9:011001101 CDAADDADR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-р-п-р
  (0010 (значення)
    (011 (100 (100 (011 (011 (100 (011 значення)))))))))

; D9:011001110 CDAADDDAR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-р-р-п
  (0010 (значення)
    (011 (100 (100 (011 (011 (011 (100 значення)))))))))

; D9:011001111 CDAADDDDR — D3 CAR/CDR, точна семикрокова композиція.
(0011 р-п-п-р-р-р-р
  (0010 (значення)
    (011 (100 (100 (011 (011 (011 (011 значення)))))))))

; D8:01000111 MAP-ANY — похідна D6:111100 ANY за ратифікованим
; законом короткого замикання D1; жодного нового D8 primitive.
(0011 відобразити-доки-істина
  (0010 (умова елементи)
    (будь-яке? умова елементи)))

; D8:00000110 POSITION — перший індекс предиката D1:1, donor #2934.
; Немає збігу -> D3:000, позиції тільки D24+. Мовна композиція.
(0011 позиція-першого-збігу-із
  (0010 (умова елементи індекс)
    (110
      ((0101 елементи) (001 ()))
      ((умова (100 елементи)) індекс)
      ((010 (001 ()))
       (позиція-першого-збігу-із
         умова (011 елементи)
         (01010 індекс #d24:000000000000000000000001))))))

(0011 позиція-першого-збігу
  (0010 (умова елементи)
    (позиція-першого-збігу-із
      умова елементи #d24:000000000000000000000000)))

; D8:11000100 TREE-EQU — структурна рівність, D8:11110111 EQUAL.
; Статус DERIVED/DUPLICATE, не нова примітивна семантика.
(0011 дерева-рівні?
  (0010 (ліве праве)
    (equal? ліве праве)))

; D8:10110100 MAPC — застосувати дію до кожного елемента зліва направо.
; Донор Common Lisp (#2934): результати дії відкидаються, вихідний список
; повертається незмінним. Мовна композиція з D6:101000 MAP і D4 LAMBDA.
; Семантика ефекту належить SENS, прямий D8 opcode не відкриваємо.
(0011 застосувати-до-всіх
  (0010 (дія елементи)
    ((0010 (обчислено) елементи)
     (відобразити дія елементи))))

; D9:010011100 CANON-LAW-CAR-CONS — D3 projection of pair head.
; For an atomic witness, EQ(CAR(CONS(a,b)), a) = D1:1.
; D9:001000110 CANON-LAW-CDR-CONS — D3 projection of pair tail.
; D9:010000111 CANON-LAW-ATOM-CONS — NOT(ATOM(CONS(a,b))) = D1:1.
; Owner-ratified names in D9 (#4008); these are derived SENS witnesses,
; not independent primitive laws and not direct D9 code-call admission.
(0011 канон-закон-перше-пара
  (0010 (ліве праве)
    (тотожне? (перше (сполучити ліве праве)) ліве)))

(0011 канон-закон-решта-пара
  (0010 (ліве праве)
    (тотожне? (решта (сполучити ліве праве)) праве)))

(0011 канон-закон-атом-пара
  (0010 (ліве праве)
    (хибне? (атом? (сполучити ліве праве)))))

; D9:001110010 CANON-LAW-EQ-REFLEXIVE-ATOM — owner #4008.
; Atom(x) => EQ(x,x)=D1:1. Pair carrier rejected via CAR(D3:000).
; Lower D3 laws only; no new D9 call mechanism or independent primitive.
(0011 канон-закон-рівність-рефлексивний-атом
  (0010 (значення)
    (за-умовою
      ((атом? значення) (тотожне? значення значення))
      ((атом? (як-є ())) (перше (як-є ()))))))

; string-length/string-empty?/string-prefix?/string-contains? (PLAN.md
; item 14, item 20's G5 audit test applied live) — none of these need a
; new Rust primitive: string-first/string-rest already expose a string
; one character at a time, and eq already compares Value::String by
; value, so "" is a real, checkable base case — the same shape as any
; other recursive list walk in this file, just walking a string instead
; of a pair chain. string-append (genuinely un-expressible this way,
; since nothing here can build a new combined string) stays in Rust —
; see its own comment in special_forms.rs for why.
;
; string-length/string-empty?/string-prefix?/string-contains? (PLAN.md,
; пункт 14, живо застосований тест G5 з пункту 20) — жодна з них не
; потребує нового Rust-примітива: string-first/string-rest уже дають
; рядок по одному символу, а eq вже порівнює Value::String за
; значенням, тож "" — реальний, перевірюваний базовий випадок — та сама
; форма, що й будь-який інший рекурсивний обхід списку в цьому файлі,
; лише по рядку, не по ланцюжку пар. string-append (справді невиразний
; так само — нічого тут не може побудувати новий об'єднаний рядок)
; лишається в Rust — див. власний коментар у special_forms.rs, чому.
(0011 string-membership-helper
  (0010 (value)
    (110
      ((0100 (010 value))
       (001 (class-membership string nonmember)))
      ((010 value) 
       (110
         ((101 (110101011 (write-to-string value))
              (110101011 (write-to-string "")))
          
          (001 (class-membership string member)))
         ((101 (110101011 (write-to-string value))
              (110101011 (write-to-string "")))
          
          (001 (class-membership string nonmember)))))
      ((010 value) 
       (001 (class-membership string nonmember))))))

(0011 string-order-helper
  (0010 (left right)
    (110
      ((110011100 left) 
       (110
         ((110011100 right) 
          (001 (text-order same)))
         ((0100 (110011100 right))
          (001 (text-order before)))))
      ((0100 (110011100 left))
       (001 (text-order after)))
      ((101 (110101011 left) (110101011 right))
       
       (string-order-helper (110011101 left) (110011101 right)))
      ((11010 (11100000 (110101011 left))
          (11100000 (110101011 right)))
       
       (001 (text-order before)))
      ((0100 (11010 (11100000 (110101011 left)) (11100000 (110101011 right))))
       (001 (text-order after))))))

(0011 nonempty-string-membership-helper
  (0010 (value)
    (110
      ((string-membership-helper value)
       
       (110
         ((0100 (110011100 value))
          (001 (class-membership string nonempty-member)))
         ((110011100 value)
          
          (001 (class-membership string member)))))
      ((string-membership-helper value)
       
       (001 (class-membership string nonmember))))))

; string<? — лексикографічний порядок за кодовими точками, як `<` для &str
; у Rust (UTF-8 зберігає порядок кодових точок). Переведено з Rust у мову
; (власник, 2026-09-26): рядок розбирають лише примітиви string-first
; через точні D9 STRING-FIRST/STRING-REST і D8 CHAR-CODE. Не-рядок
; дає природну помилку Type від string-first; неправильна кількість
; аргументів — Arity від прив'язки лямбди.
(0011 string<?
  (0010 (a b)
    (110
      ; D9 STRING-EMPTY? always returns exact D1; empty < nonempty only.
      ((110011100 a)
       (110
         ((110011100 b) #d1:0)
         (#d1:1 #d1:1)))
      ((110011100 b) #d1:0)
      ; D8 CHAR-CODE gives exact D24 for D5 LESSP. No EQ/NIL truthiness.
      ((11010 (11100000 (110101011 a))
              (11100000 (110101011 b)))
       #d1:1)
      ((11010 (11100000 (110101011 b))
              (11100000 (110101011 a)))
       #d1:0)
      ; Equal Unicode scalar; continue over both D9 STRING-REST tails.
      (#d1:1 (string<? (110011101 a) (110011101 b))))))



; D8:10110001 STRING< — ратифікована українська поверхня того ж мовного закону.
; Історичний SID8:00100101 не є доменним кодом; жодного host route.
(0011 текст-передує? string<?)

; D8:00100011 STRING> — похідний закон текстового порядку з D8:10110001 STRING<.
; STRING>(a,b) = STRING<(b,a); координата і ширина не змінюються.
; Власна мовна функція SENS; без прямої D8 callability чи нового host-закону.
(0011 текст-більший?
  (0010 (ліве праве)
    (string<? праве ліве)))

; D8:00000100 PROG1 і D8:11001001 PROG2 — звичайні функції SENS.
; Виклик обчислює всі аргументи в стандартному порядку перед входом у тіло;
; далі повертаємо відповідно перший або другий уже обчислений результат.
; Жодного host-примітива чи нового доменного коду.
(0011 повернути-перше
  (0010 (a . tail)
    a))
(0011 prog1 повернути-перше)

(0011 повернути-друге
  (0010 (a b . tail)
    b))
(0011 prog2 повернути-друге)

; `symbol?` moved out of Rust after `write-to-string` made the distinction
; expressible without exceptions: among atoms, exactly a Symbol is identical
; to the Symbol reconstructed from its canonical text. The atom guard keeps
; primitive `eq` away from pairs. This works for arbitrary symbol names, not
; only reader-friendly identifiers, because `string->symbol` takes raw text.
; `symbol?` перенесено з Rust: серед атомів лише Symbol тотожний символу,
; відновленому з його канонічного тексту. `atom` не допускає пари до `eq`.
; `symbol?` wurde aus Rust verschoben: Unter Atomen ist nur ein Symbol mit dem
; aus seinem kanonischen Text rekonstruierten Symbol identisch; `atom` schützt `eq`.
(0011 symbol?
  (0010 (value)
    (110
      ((010 value)
       (110
         ((101 value (string->symbol (write-to-string value)))
          (010 (001 ())))
         ((010 ()) #d1:0)))
      ((010 ()) #d1:0))))


; quotient/mod (G5 test: already expressible via existing means?) — yes.
; Unlike bitwise operations (AND/OR/XOR/shift — no primitive exposes a
; number's binary representation at all, so those would genuinely need a
; new Rust primitive), integer division and remainder for non-negative
; integers fall straight out of arithmetic and comparison primitives
; already here — no new Rust code, same class of gap as string-length
; before it. Surfaced from the fpga-lisp session's assembler.lisp
; (2026-08-10), which flagged the *absence* of bitwise/mod but found it
; non-load-bearing for its own current needs; added here anyway since
; it's genuinely useful independent of that one caller and costs
; nothing new in Rust. Scope: non-negative `a`, positive `b` only — no
; attempt at negative-number semantics (floor vs. truncate division is
; a real, unresolved design choice for negatives, deliberately left
; open rather than guessed at).
;
; First version (same-day, since replaced) recursed via repeated
; subtraction — recursion depth equal to the *quotient itself*, not
; its digit count. Fine for small examples (17/5, 100/10) but a real
; correctness bug: `(number->string 9999999999999)` (below) needs
; `(quotient 9999999999999 10)` — a quotient near 10^12 — which blew
; the Rust host's stack outright. `my-lisp` has arbitrary-precision
; exact integers (`bignum.rs`); a division whose cost scales with the
; *value* rather than its *size* was never actually general-purpose.
; Fixed here via doubling (`largest-chunk`: find the largest `b * 2^k`
; that still fits `a`, subtract it, repeat) — the standard
; binary-long-division trick, recursion depth O(log(a/b)) in both
; `largest-chunk` and `quotient` itself, tested against a 13-digit
; dividend without incident.
; quotient/mod (G5-тест: уже виразне через наявне?) — так. На відміну
; від бітових операцій (AND/OR/XOR/зсув — жоден примітив узагалі не
; відкриває бінарне представлення числа, тож ті справді потребували б
; нового Rust-примітива), цілочисельне ділення й остача для
; невід'ємних чисел випливають напряму з наявних арифметичних і
; порівняльних примітивів — без нового Rust-коду, той самий клас
; прогалини, що й string-length раніше. Знахідка з сесії fpga-lisp,
; assembler.lisp (2026-08-10), яка позначила ВІДСУТНІСТЬ bitwise/mod, але
; визнала це не критичним для власних поточних потреб; додано тут усе
; одно, бо це реально корисне незалежно від того одного викликача й не
; коштує нічого нового в Rust. Обсяг: лише невід'ємне `a`, додатне `b`
; — без спроби вгадати семантику для від'ємних чисел.
;
; Перша версія (того самого дня, відтоді замінена) рекурсувала через
; повторюване віднімання — глибина рекурсії дорівнювала САМІЙ ЧАСТЦІ,
; не кількості її розрядів. Прийнятно для малих прикладів (17/5,
; 100/10), але справжній баг коректності: `(number->string
; 9999999999999)` (нижче) вимагав `(quotient 9999999999999 10)` —
; частку близько 10^12 — що переповнило Rust-стек хоста напряму.
; `my-lisp` має цілі числа довільної точності (`bignum.rs`); ділення,
; вартість якого масштабується зі ЗНАЧЕННЯМ, а не РОЗМІРОМ, ніколи не
; було справді загальноцільовим. Виправлено через подвоєння
; (`largest-chunk`: знайти найбільше `b * 2^k`, що вміщується в `a`,
; відняти, повторити) — стандартний трюк бінарного довгого ділення,
; глибина рекурсії O(log(a/b)) як у `largest-chunk`, так і в самому
; `quotient`, перевірено на 13-розрядному діленому без проблем.
(0011 largest-chunk
  (0010 (a b chunk mult)
    (110
      ((11010 a (01010 chunk chunk))  (111 chunk mult))
      ((0100 (11010 a (01010 chunk chunk)))
       (largest-chunk a b (01010 chunk chunk) (01010 mult mult))))))

; `b = 0` used to hang forever: `largest-chunk` starts doubling from
; `chunk = b`, and `0 + 0 = 0` never grows, so its "does chunk still
; fit" check never flips — an infinite tail-recursive loop, not a
; crash, silent unless you're specifically watching for it. Found the
; same way as the earlier stack-overflow bug: tested an edge case the
; first version never considered. `/` (the Rust primitive) already
; fails named on division by zero (`ErrorKind::InvalidForm`) — routing
; through it here reuses that real, already-tested error instead of
; inventing a second, different one for the same condition.
; `b = 0` раніше зависав назавжди: `largest-chunk` починає подвоювати
; від `chunk = b`, а `0 + 0 = 0` ніколи не росте, тож перевірка "чи
; chunk усе ще вміщується" ніколи не переверталась — нескінченний
; хвостово-рекурсивний цикл, не крах, непомітний, якщо спеціально не
; шукати. `/` (Rust-примітив) уже провалюється названо на діленні на
; нуль (`ErrorKind::InvalidForm`) — маршрутизація через нього тут
; перевикористовує цю реальну, вже перевірену помилку замість
; вигадування другої, іншої для того самого стану.
; Integer quotient recurses in Lisp; D5 QUOTIENT is exact rational division.
(0011 quotient
  (0010 (a b)
    (110
      ((101 b 0)  (11110110 a b))
      ((0100 (101 b 0))
       (110
         ((11010 a b)  0)
         ((0100 (11010 a b))
          (let ((chunk+mult (largest-chunk a b b 1)))
            (01010 (011 chunk+mult)
               (quotient (01011 a (100 chunk+mult)) b)))))))))

; Integer remainder uses the Lisp-owned floor quotient: a - b * floor(a / b).
(0011 mod
  (0010 (a b)
    (01011 a (10110 b (quotient a b)))))

; `<=` and `>=` stay Lisp-derived, but #216 now requires the derived
; operators to preserve the same exact-Q answer algebra as `<`, `>` and `=`:
; exact YES -> 1/1, exact NO -> 0/1, and any inexact operand -> Canon 0 `()`.
; Canonical three-part `cond` distinguishes exact NO (0) from no-answer `()`
; without routing either through generic truthiness.
(0011 nondecreasing-from?
  (0010 (current remaining)
    (110
      ((0100 (010 remaining)) 1)
      ((11010 current (100 remaining)) 
       (nondecreasing-from? (100 remaining) (011 remaining)))
      ((equal? current (100 remaining)) 
       (nondecreasing-from? (100 remaining) (011 remaining)))
      ((0100 (equal? current (100 remaining))) 0))))

(0011 nonincreasing-from?
  (0010 (current remaining)
    (110
      ((0100 (010 remaining)) 1)
      ((11011 current (100 remaining)) 
       (nonincreasing-from? (100 remaining) (011 remaining)))
      ((equal? current (100 remaining)) 
       (nonincreasing-from? (100 remaining) (011 remaining)))
      ((0100 (equal? current (100 remaining))) 0))))

(0011 <=
  (0010 (first . remaining)
    (nondecreasing-from? first remaining)))

(0011 >=
  (0010 (first . remaining)
    (nonincreasing-from? first remaining)))

; number->string (G5 test: already expressible via existing means?) —
; yes, now that quotient/mod exist. Surfaced from the fpga-lisp
; session's assembler.lisp, which had its own version built on a fixed
; DECIMAL-POWERS lookup table (limited to ~10 digits by construction —
; the table itself has a fixed length). This one recurses via
; quotient/mod instead, the same -onto accumulator shape as
; length-onto/reverse-onto above, so it has no digit-count ceiling of
; its own (bounded only by however large an exact integer this
; implementation can represent at all). Scope: non-negative integers
; only, same as quotient/mod themselves.
; number->string (G5-тест: уже виразне через наявне?) — так, тепер,
; коли є quotient/mod. Знахідка з сесії fpga-lisp, assembler.lisp, яка
; мала власну версію на фіксованій таблиці DECIMAL-POWERS (обмежена
; ~10 розрядами самою побудовою таблиці). Ця рекурсує через
; quotient/mod, та сама -onto-форма акумулятора, що й length-onto/
; reverse-onto вище, тож не має власної стелі розрядності. Обсяг:
; лише невід'ємні цілі, як і самі quotient/mod.
(0011 digit->string
  ; Superseded by number->string's canonical delegation to write-to-string
  ; (FIX-NUMBER-TO-STRING-RATIONAL). Retained because racket/boot/core.lisp
  ; mirrors this file and fpga-lisp's assembler.lisp carries its own local
  ; variant — removal is a separate mirrored-surface decision, not a
  ; silent one.
  (0010 (d)
    (000100 d (001 ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(0011 number->string-onto
  (0010 (n acc)
    (110
      ((101 n 0)  acc)
      ((101 n 0) 
       (number->string-onto
         (10111 n #d10)
         (110011110 (digit->string (00101100 n #d10)) acc))))))

(0011 number->string
  (0010 (n)
    ; Canonical serialization for every number (FIX-NUMBER-TO-STRING-
    ; RATIONAL, docs/BUG-number-to-string-rational.md): integers render
    ; as themselves, non-integer rationals render REDUCED exactly —
    ; "1/3", never a decimal approximation, per the same G6 law that
    ; makes 10/20 serialize as "1/2". The previous quotient/mod descent
    ; crashed on fractional digit indices ((nth 1/3 <digit-table>)) and
    ; its misleading error surfaced as an apparent memory corruption.
    ; Delegation, not re-implementation: write-to-string is already the
    ; contract-tested renderer (G6 fixtures), so this cannot drift from it.
    (write-to-string n)))

; -> / ->> (thread-first / thread-last macros) — express transformation pipelines
; without deep nesting (PLAN.md item / clean-code policy).
; `(-> x (f y) g)` expands to `(g (f x y))`.
; `(->> x (f y) g)` expands to `(g (f y x))`.
; Both take advantage of the variadic lambda parameter support (a bare symbol `forms`
; binds the whole list of arguments) available since 2026-08-09.
;
; -> / ->> (макроси прокидання) — виражають пайплайни перетворень без
; глибокої вкладеності (політика clean-code).
; `(-> x (f y) g)` розгортається в `(g (f x y))`.
;
; -> / ->> (Threading-Makros) — drücken Transformations-Pipelines ohne tiefe
; Verschachtelung aus.
(0011 ->
  (make-macro
    (0010 forms
  (110
    
    ((010 forms) 
     (110
       ((0100 (010 (011 forms))) (100 forms))
       ((010 (011 forms)) 
        (001001 ((x (100 forms))
               (next (100 (011 forms)))
               (rest (011 (011 forms)))
               (step
                 (110
                   ((0100 (010 next)) (1110 next x))
                   ((010 next)  (1110 next x))
                   ((010 next) 
                    (111 (100 next) (111 x (011 next)))))))
          (110
            ((0100 (010 rest)) step)
            ((010 rest) 
             (111 (001 ->) (111 step rest))))))))))))

(0011 ->>
  (make-macro
    (0010 forms
  (110
    
    ((010 forms) 
     (110
       ((0100 (010 (011 forms))) (100 forms))
       ((010 (011 forms)) 
        (001001 ((x (100 forms))
               (next (100 (011 forms)))
               (rest (011 (011 forms)))
               (step
                 (110
                   ((0100 (010 next)) (1110 next x))
                   ((010 next)  (1110 next x))
                   ((010 next) 
                    (1111 next (1110 x))))))
          (110
            ((0100 (010 rest)) step)
            ((010 rest) 
             (111 (001 ->>) (111 step rest))))))))))))

;; ── Numeric library additions (M0, 2026-08-22) ─────────────────────
;; Додано для реальних задач (WSM-24 shape comparison): abs/min/max/
;; sqrt. Усе — бібліотечні функції над наявними примітивами; жодного
 ;; нового коду в Rust-ядрі (doctrine: library before core primitive).
;;
;; Конвенції:
;;   (abs x) / (min a b ...) / (max a b ...) — Rust builtins (builtins.rs);
;;   (min-list lst)/(max-list lst) — Rust builtins для списків;
;;   (sqrt x)         — Ньютон, 40 ітерацій; точний вхід дає раціональне
;;                      наближення, дробове — дробовий результат
;;                      (S1 inexact promotion). Відʼємний вхід → nil.

(0011 sqrt-iter
  (0010 (guess x n)
    (110
      ((equal? n 0)  guess)
      ((0100 (equal? n 0))
       (sqrt-iter (11110110 (01010 guess (11110110 x guess)) 2) x (01011 n 1))))))

;; integer sqrt: Newton on quotients — provably terminating
(0011 isqrt
  (0010 (n)
    (110
      ((11010 n 2)  n)
      ((0100 (11010 n 2))
       (isqrt-step n (10111 n 2))))))

(0011 isqrt-step
  (0010 (n g)
    (let ((next (10111 (01010 g (10111 n g)) 2)))
      (110
        ((11010 next g)  (isqrt-step n next))
        ((0100 (11010 next g)) g)))))

(0011 sqrt
  (0010 (x)
    (110
      ((11010 x 0)  (001 ()))
      ((equal? x 0)  0)
      ((equal? x (10111 x 1)) 
       (let ((r (110111010 x)))
         (110
           ((equal? (10110 r r) x)  r)
           ((010 ())  (sqrt-iter (11110110 x 2) x 8)))))
      ((010 ())  (sqrt-iter (11110110 x 2.0) x 5)))))

; abs/min/max/min-list/max-list — migrated from Rust builtins.rs to
; lib/core.lisp (owner directive 2026-09-11: "Lisp owns meaning, Rust owns
; only irreducible mechanism" — these five touch no OS/host capability,
; just arithmetic comparison and cons-list traversal already expressible
; in the language itself, so keeping them in Rust was Rust-authority
; with no substrate reason, not a necessity). Real numeric semantic IDs
; already existed for all five in lib/surface/semantic-registry.lisp
; (abs=1004, min=1005, max=1006, min-list=1011, max-list=1012, some with
; real Sanskrit spellings already ratified) — the Rust implementation
; simply never consulted them (plain `define!`, not the registry-aware
; `define_peer_builtin` path other builtins use), a second real gap this
; migration closes alongside moving the implementation itself. First
; nearly overwrote these real entries with a duplicate 1147-1151 block
; before checking the registry directly — caught before committing, not
; after.
; Behavior verified identical to the removed Rust implementation via
; crates/my-lisp/tests/builtin_to_lisp_migration.rs before deletion, not
; assumed from reading the old Rust source.
; abs/min/max/min-list/max-list — perenesheni z Rust builtins.rs u
; lib/core.lisp (nastanova vlasnyka 2026-09-11: "Lisp volodiie sensom, Rust
; volodiie lyshe nezvidnym mekhanizmom") — ni odyn iz piaty ne torkaietsia
; OS/host-mozhlyvosti, lyshe aryfmetychne porivniannia ta obkhid cons-spysku,
; vzhe vyrazhuvani samoiu movoiu.
; D6:010011 ABS / модуль — exact D24+ arithmetic, exact D1 condition.
; LESSP returns an exact numeric result; EQUAL? projects its 1/0 value to D1.
(0011 модуль
  (0010 (x)
    (110
      ((менше? x #d24:000000000000000000000000)
       (відняти #d24:000000000000000000000000 x))
      (#d1:1 x))))
(0011 abs модуль)

; Required first parameter (dotted lambda-list, same pattern as
; `<=`/`>=` above) keeps zero arguments an Arity error via the
; evaluator's own lambda-binding check -- matching the removed Rust
; builtin's explicit "min/max expects at least one argument" error --
; without this Lisp definition needing to raise a custom error itself.
(0011 min
  (0010 (first . rest)
    (000010 (111 first rest))))

(0011 max
  (0010 (first . rest)
    (000011 (111 first rest))))

; Two real bugs found live via oracle testing before this landed, not
; assumed from reading the removed Rust source:
; 1. `eq`, not `equal?`, requires both operands to be atoms and errors
;    on a non-empty list -- the first draft used `(eq items (quote ()))`
;    and crashed on every non-base recursive call.
; 2. `atom` is *not* a safe "is this the empty-list sentinel" check for
;    the RECURSIVE RESULT specifically: numbers are atoms too, so
;    `(atom rest-min)` was true both for the real empty-list case and
;    for an ordinary numeric answer, collapsing them and always taking
;    the base-case branch. `items` itself is safe to test with `atom`
;    (it's always a list or (), never itself a bare number), but the
;    accumulator tests exact structural EMPTY with D4:0101 NULL.
; D6:000010 та D6:000011: власні SENS-композиції D3/D4/D5.
; Числова область D24+, для порожнього списку повертаємо ().
(0011 найменше-залишки
  (0010 (залишки обране)
    (110
      ((0101 залишки) обране)
      ((0100 (0101 залишки))
       (110
         ((11010 (100 залишки) обране)
          (найменше-залишки (011 залишки) (100 залишки)))
         ((0100 (11010 (100 залишки) обране))
          (найменше-залишки (011 залишки) обране)))))))

(0011 найбільше-залишки
  (0010 (залишки обране)
    (110
      ((0101 залишки) обране)
      ((0100 (0101 залишки))
       (110
         ((11011 (100 залишки) обране)
          (найбільше-залишки (011 залишки) (100 залишки)))
         ((0100 (11011 (100 залишки) обране))
          (найбільше-залишки (011 залишки) обране)))))))

(0011 найменше-у-списку
  (0010 (елементи)
    (110
      ((0101 елементи) (001 ()))
      ((0100 (0101 елементи))
       (найменше-залишки (011 елементи) (100 елементи))))))

(0011 найбільше-у-списку
  (0010 (елементи)
    (110
      ((0101 елементи) (001 ()))
      ((0100 (0101 елементи))
       (найбільше-залишки (011 елементи) (100 елементи))))))

(0011 min-list найменше-у-списку)
(0011 max-list найбільше-у-списку)

; #469 — post-core stable peer materialization.
;
; Numeric semantic ID remains the authority. This table is only the runtime
; projection needed by Lisp libraries loaded after the ordinary core bootstrap:
; a library names the numeric ID and the binding it just defined; peer spellings
; are never implemented as UK->EN or EN->UK aliases in that library.
;
; Keep only unique stable spellings from lib/surface/semantic-registry.lisp.
; Candidate spellings are deliberately absent and therefore cannot become
; executable merely by appearing in documentation.
(0011 my-postcore-stable-peer-projection
  (001 (
    (1079 utc-now поточний-всч)
    (1080 utc-from-unix всч-із-юнікс)
    (1081 unix-time-observation->utc юнікс-спостереження-у-всч)
    (1082 milliseconds-from-nanoseconds мілісекунди-із-наносекунд)
    (1083 mono-ms монотонний-мс)
    (1084 timezone-name назва-часового-поясу)
    (1085 timezone-detect визначити-часовий-пояс)
    (1086 timezone-offset-seconds зміщення-часового-поясу-в-секундах)
    (1087 deadline-reached? дедлайн-досягнуто?)
    (1088 deadline-reached-at? дедлайн-досягнуто-на-момент?)
    (1089 elapsed-ns минуло-нс)
    (1090 deadline-from дедлайн-від)
    (1091 deadline-after-ns дедлайн-через-нс)
    (1092 internet-time-sync запитати-інтернет-час)
    (162 process-run запустити-процес)
    (163 tcp-read прочитати-текст-з-з'єднання-протоколу-керування-передаванням)
    (164 tcp-write записати-текст-у-з'єднання-протоколу-керування-передаванням)
    (165 tcp-listen слухати-порт-протоколу-керування-передаванням)
    (166 read-file прочитати-файл)
    (167 write-file записати-файл)
  )))

(0011 my-postcore-peer-group
  (0010 (semantic-id groups)
    (110
      ((010 groups) (001 ()))
      ((010 (001 ()))
       (let ((group (100 groups)))
         (110
           ((101 semantic-id (100 group)) group)
           ((010 (001 ()))
            (my-postcore-peer-group semantic-id (011 groups)))))))))

(0011 my-postcore-binding-status
  (0010 (surface bindings)
    (110
      ((010 bindings) (001 absent))
      ((010 (001 ()))
       (let ((binding (100 bindings)))
         (110
           ((101 (11101110 surface) (100 binding))
            (001 present))
           ((010 (001 ()))
            (my-postcore-binding-status surface (011 bindings)))))))))

(0011 my-postcore-missing-peers
  (0010 (source peers bindings)
    (110
      ((010 peers) (001 ()))
      ((010 (001 ()))
       (let ((peer (100 peers)))
         (110
           ((101 source peer)
            (my-postcore-missing-peers source (011 peers) bindings))
           ((010 (001 ()))
            (110
              ((101 (my-postcore-binding-status peer bindings)
                         (001 present))
               (my-postcore-missing-peers source (011 peers) bindings))
              ((101 (my-postcore-binding-status peer bindings)
                         (001 absent))
               (111 peer
                 (my-postcore-missing-peers
                   source (011 peers) bindings)))))))))))

; Build one expression whose nested DEFINE forms all execute in the caller's
; environment. This is why materialization is a macro rather than a function:
; an ordinary function would define peers only in its temporary child frame.
(0011 my-postcore-build-definitions
  (0010 (source peers)
    (110
      ((010 peers) source)
      ((010 (001 ()))
       (1110 (001 define)
         (100 peers)
         (my-postcore-build-definitions source (011 peers)))))))

(0011 my-postcore-materialize-stable-peers
  (make-macro
    (0010 args
  (001001 ((semantic-id (100 args))
             (source (1001 args))
             (group (my-postcore-peer-group
                       semantic-id my-postcore-stable-peer-projection)))
    (110
      ((010 group) source)
      ((010 (001 ()))
       (my-postcore-build-definitions source
         (my-postcore-missing-peers source (011 group) (11100111)))))))))

; Ділення з остачою (Lisp 1.5 DIVIDE): повертає список (частка остача).
(0011 divmod
  (0010 (dividend divisor)
    (1110 (10111 dividend divisor) (00101100 dividend divisor))))

; McCarthy 1960, §3d: null, subst, sublis, maplist, apply — закон Core4, коди СЕНС.
(0011 null?
  (0010 (x)
    (0101 x)))

; D5:11111 SUBST. Обидві гілки D3:110 точні, рекурсія SENS.
; На атомі лише D3:101 EQ; на парі D3:111 CONS дочірніх результатів.
(0011 замінити
  (0010 (нове старе дерево)
    (110
      ((010 дерево)
       (110
         ((101 дерево старе) нове)
         ((0100 (101 дерево старе)) дерево)))
      ((0100 (010 дерево))
       (111 (замінити нове старе (100 дерево))
            (замінити нове старе (011 дерево)))))))
(0011 subst замінити)

(0011 sublis-pair
  (0010 (x z)
    (110
      ((0100 (010 x)) z)
      ((010 x) 
       (110
         ((101 (100 (100 x)) z) 
          (100 (011 (100 x))))
         ((101 (100 (100 x)) z) 
          (sublis-pair (011 x) z)))))))

(0011 sublis
  (0010 (x y)
    (110
      ((010 y) 
       (111 (001010 x (100 y)) (001010 x (011 y))))
      ((0100 (010 y)) (sublis-pair x y))
      ((010 y)  (sublis-pair x y)))))

; Партія D6 · похідні власні закони, точні коди без прямого D6 opcode.
; D6:000101 MAPLIST — дія над усіма непорожніми хвостами.
; D6:000101 MAPLIST(list, function) — successive suffix observations.
; Exact D6 law: knowledge/d6-v2-binary-law-families.json and #3744.
(0011 відобразити-залишки
  (0010 (хвости дія)
    (110
      ((0101 хвости) (001 ()))
      ((010 (001 ()))
       (111 (дія хвости)
            (відобразити-залишки (011 хвости) дія))))))

; D6:110010 DO — explicit-state tail recursion, #3370.
(0011 робити
  (0010 (крок готово? результат стан)
    (110
      ((готово? стан) (результат стан))
      ((010 (001 ())) (робити крок готово? результат (крок стан))))))

; D6:110011 WHILE — цикл через явний стан і D1-предикат, #3370.
(0011 поки
  (0010 (умова крок стан)
    (110
      ((умова стан) (поки умова крок (крок стан)))
      ((010 (001 ())) стан))))

; D8:10111001 REDUCE-right: ратифікований похідний закон #3674.
; Правий згорток = D6:101110 REDUCE після D6:101101 FLIP і D5:10100 REVERSE.
; Порядок аргументів не змінюється; D8:bits не дістає прямої викличності.
(0011 згорнути-справа
  (0010 (дія початок елементи)
    (згорнути (поміняти-аргументи дія)
             початок (зворот елементи))))

; D8:10111011 SCAN-right: FOLD-right prefixes у порядку обчислення.
; #3674: last(SCAN-right(f,z,xs)) = REDUCE-right(f,z,xs), для xs != ().
; Empty-list presentation лишається () згідно з чинним D6 SCAN.
(0011 накопичувати-справа
  (0010 (дія стан елементи)
    (110
      ((0101 елементи) (001 ()))
      ((010 (001 ()))
       (накопичувати (поміняти-аргументи дія)
                      стан (зворот елементи))))))


; D8:01000010 COPY-SEQ — мовна реалізація для proper-list.
; Делегує ратифікований D8:10100000 COPY-LIST; не заявляє
; підтримку векторів/рядків чи нову пряму викличність D8 коду.
(0011 копіювати-послідовність
  (0010 (список)
    (копіювати-список список)))

; D8:01001010 MAPQN — кожний наступний (CAR tail, CDR tail)
; подається двоаргументній дії; значення дій збираються у список.
; Donor: scripts/build-d8-historical-full-map.py (MAPQN, MacLisp).
; Область: належний список; D6:000101 MAPLIST задає хвости.
(0011 голови-залишків
  (0010 (дія елементи)
    (110
      ((0101 елементи) (001 ()))
      ((010 елементи) (100 (001 ())))
      (#d1:1
       (111 (дія (100 елементи) (011 елементи))
            (голови-залишків дія (011 елементи)))))))

(0011 maplist відобразити-залишки)

; D8:00110000 MAPL — exact ratified D8 historical capability.
; Run the callback over successive nonempty tails for effects; return original list.
; A Lisp-owned D6:000101 MAPLIST derivation; no direct D8 binary admission.
(0011 застосувати-до-залишків
  (0010 (елементи дія)
    ((0010 (непотрібні-результати) елементи)
     (відобразити-залишки елементи дія))))

; D8:00001011 MAPLIST* — ratified historical capability, exact 8-bit identity.
; Law: knowledge/d8-ratified.json: map successive proper-list tails, including final ().
; D6:000101 MAPLIST omits final (); this is a derived SENS definition,
; not a new direct D8 machine-call admission or a legacy W8 slot.
(0011 залишки+порожнє
  (0010 (елементи дія)
    (110
      ((0101 елементи)
       (111 (дія (001 ())) (001 ())))
      ((010 (001 ()))
       (111 (дія елементи)
            (залишки+порожнє (011 елементи) дія))))))


(0011 apply-quote-args
  (0010 (m)
    (110
      
      ((010 m) 
       (111 (111 (001 001) (111 (100 m) (001 ())))
                 (apply-quote-args (011 m)))))))

(0011 apply
  (0010 (f args)
    (0001 (111 f (apply-quote-args args)))))

; #1391: логіка відповідей Core4 — закон contracts/core4-predicate-answer-scale.lisp /3.
; Відповідь — список двійкових бітів: (1)…(1 1 1 1 1 1 1) «так»,
; (0)…(0 0 0 0 0 0 0) «ні», () «невідомо». Лінія істинності:
;   0 < 00 < … < 0000000 < () < 1111111 < … < 11 < 1
; Виконуваний свідок законів — experiments/core4-logic15-algebra.lisp.

; NOT: інвертувати кожен біт, ширина та сама; () лишається ().
(0011 answer-not
  (0010 (a)
    (110
      
      ((010 a) 
       (111
         (110
           ((101 (100 a) 0)  1)
           ((0100 (101 (100 a) 0)) 0))
         (110111011 (011 a)))))))

; AND: мінімум на лінії. «Ні» перемагає; з двох «ні» — коротше (сильніше);
; з двох «так» — довше (слабше); () поглинає «так».
; Для двох відповідей одного напряму крок іде по обох списках разом.
(0011 answer-and
  (0010 (a b)
    (110
      ((0100 (010 a))
       (110
         
         ((010 b) 
          (110
            ((101 (100 b) 0)  b)
            ((101 (100 b) 0)  (001 ()))))))
      ((010 a) 
       (110
         ((0100 (010 b))
          (110
            ((101 (100 a) 0)  a)
            ((101 (100 a) 0)  (001 ()))))
         ((010 b) 
          (110
            ((101 (100 a) (100 b)) 
             (110
               ((101 (100 a) 0)  a)
               ((0100 (101 (100 a) 0)) b)))
            ((101 (100 a) (100 b)) 
             (110
               ((0100 (010 (011 a)))
                (110
                  ((101 (100 a) 0)  a)
                  ((0100 (101 (100 a) 0)) b)))
               ((0100 (010 (011 b)))
                (110
                  ((101 (100 b) 0)  b)
                  ((0100 (101 (100 b) 0)) a)))
               ((010 (011 b)) 
                (111 (100 a)
                          (110110100 (011 a) (011 b)))))))))))))

; OR: максимум на лінії = NOT(AND(NOT a, NOT b)).
(0011 answer-or
  (0010 (a b)
    (110111011 (110110100 (110111011 a) (110111011 b)))))

; Послаблення: дописати той самий біт; восьмий біт належить 256 функціям,
; тож із семи бітів шкала сходиться в ().
(0011 answer-weaken
  (0010 (a)
    (110
      
      ((010 a) 
       (110
         ((101 (000000 a) 7)  (001 ()))
         ((101 (000000 a) 7) 
          (111 (100 a) a)))))))

; atom? відповіддю шкали: атом (1), пара (0), () — невідомо, бо () стоїть
; вище розрізнення атом/пара.
(0011 answer-atom
  (0010 (x)
    (110
      ((010 x)  (001 (1)))
      ((010 x)  (001 (0)))
      )))

; eq? відповіддю шкали: same (1), distinct (0). Область та сама, що в eq?: атоми.
(0011 answer-eq
  (0010 (a b)
    (110
      ((101 a b)  (001 (1)))
      ((101 a b)  (001 (0))))))

; D8:00010000 LIST-DIFFERENCE — збереження порядку й повторів лівого списку.
(0011 різниця-списків
  (0010 (ліві праві)
    (110
      ((0101 ліві) (001 ()))
      ((010 (001 ()))
       (110
         ((значення-у-списку? (100 ліві) праві)
          (різниця-списків (011 ліві) праві))
         ((010 (001 ()))
          (111 (100 ліві)
               (різниця-списків (011 ліві) праві))))))))

; D8:00101101 ADJOIN — наявне значення не дублюється й не копіюється.
(0011 додати-якщо-нема
  (0010 (елемент множина)
    (110
      ((значення-у-списку? елемент множина) множина)
      ((010 (001 ())) (111 елемент множина)))))


; D8:01001101 MEMBER-IF: повертає перший елемент, який задовольняє D1-предикат.
; Відсутній елемент — структурне (); жодної нової callability.
(0011 знайти-елемент-якщо
  (0010 (умова елементи)
    (110
      ((0101 елементи) (001 ()))
      ((умова (100 елементи)) (100 елементи))
      (#d1:1 (знайти-елемент-якщо умова (011 елементи))))))


; D8:00001000 EQL — похідна поверхня точного D3:101 EQ допущених атомів.
; Не створювати нової (структурної) семантики рівності.
(0011 тотожне-значення?
  (0010 (ліве праве) (101 ліве праве)))


; D8:01011010 BUTLAST: усі елементи proper-list, крім останнього.
; Лише D3 CAR/CDR/CONS, D4 NULL та структурне (), без D24+ лічильника.
(0011 без-останнього
  (0010 (елементи)
    (110
      ((0101 елементи) (001 ()))
      ((0101 (011 елементи)) (001 ()))
      (#d1:1 (111 (100 елементи) (без-останнього (011 елементи)))))))
; D8:10100010: видалити попередні дублі, залишити останнє входження.
(0011 прибрати-дублікати (0010 (список) (110 ((0101 список) (001 ())) ((010 (001 ())) (110 ((значення-у-списку? (100 список) (011 список)) (прибрати-дублікати (011 список))) ((010 (001 ())) (111 (100 список) (прибрати-дублікати (011 список)))))))))

; D8:01011111: LAST повертає останній cons-хвіст, не атом.
(0011 останній-хвіст (0010 (список) (110 ((0101 список) (001 ())) ((010 (001 ())) (110 ((0101 (011 список)) список) ((010 (001 ())) (останній-хвіст (011 список))))))))

; D8:11011111 FIND — SENS lower-composition через MEMBER-IF/EQUAL.
; Зберігає порядок вхідного proper list, не створює direct D8 callability.
(0011 знайти-перший-збіг
  (0010 (шукане елементи)
    (знайти-елемент-якщо
      (0010 (кандидат) (equal? шукане кандидат))
      елементи)))

; D8:10100101 SOME — похідний D1 предикат від D6:111100 ANY.
(0011 існує-збіг? будь-яке?)


; D8:11011100 RASSQ — пошук значення лише за точним D3:101 EQ над CDR.
; Відмінність від D6 RASSOC: жодного структурного EQUAL? і ніякого D8 direct-call.
(0011 асоціація-решта
  (0010 (значення асоціації)
    (110
      ((0101 асоціації) (001 ()))
      ((101 значення (011 (100 асоціації))) (100 асоціації))
      (#d1:1 (асоціація-решта значення (011 асоціації))))))


; D8:11011101 UNTIL — дуальність до D6:110011 WHILE за D4:0100 NOT.
; Лише перетворення предиката стану, без окремого ефектного примітива.
(0011 поки-не
  (0010 (умова крок стан)
    (поки (0010 (поточний) (хибне? (умова поточний)))
          крок стан)))


; D8:10101110 ALWAYS — універсальність над послідовністю саме D1-бітів.
; D6:111101 ALL застосовує тотожний D4 LAMBDA; не host truthiness.
(0011 усі-істинні?
  (0010 (відповіді)
    (усі? (0010 (відповідь) відповідь) відповіді)))


; D8:11001010 NEVER — жодний точний D1-біт у списку не є YES.
; D4 NOT від D6 ANY; порожній список дає YES.
(0011 жодне-істинне?
  (0010 (відповіді)
    (хибне? (будь-яке? (0010 (відповідь) відповідь) відповіді))))


; D8:01011001 1+ — рівно один математичний D24, не текстова D7 цифра.
; Нижній D5:01010 PLUS єдина арифметична операція.
(0011 збільшити-на-1
  (0010 (число)
    (додати число #d24:000000000000000000000001)))


; D8:00001100 1- — рівно один математичний D24, не текстова D7 цифра.
; Нижній D5:01011 DIFFERENCE єдина арифметична операція.
(0011 зменшити-на-1
  (0010 (число)
    (відняти число #d24:000000000000000000000001)))


; D6:001010 SUBLIS — canonical ratified Ukrainian SENS tree substitution.
; Search whole-subtree association first; a matching node is replaced without
; descending into its descendants. Without a match, atoms stay unchanged
; and every CONS child is traversed by D3 CAR/CDR, retaining dotted tails.
; Search uses the existing structural D5 ASSOC/EQUAL law, not a D6 call-head.
(0011 підставити-пари
  (0010 (відповідності дерево)
    ((0010 (пара)
       (110
         ((0101 пара)
          (110
            ((010 дерево) дерево)
            (#d1:1
             (111 (підставити-пари відповідності (100 дерево))
                  (підставити-пари відповідності (011 дерево))))))
         (#d1:1 (011 пара))))
     (знайти-за-ключем дерево відповідності))))


; D8:00100010 SIGNUM: exact D24+ sign, result negative-one / zero / one.
; Only D5 LESSP, D6 NEG, and exact D1 COND; no D7 digit promotion.
(0011 знак-числа
  (0010 (число)
    (110
      ((менше? число #d24:000000000000000000000000)
       (змінити-знак #d24:000000000000000000000001))
      ((менше? #d24:000000000000000000000000 число)
       #d24:000000000000000000000001)
      (#d1:1 #d24:000000000000000000000000))))


; D8:01001001 NEG∘RECIP: exact lower D6 composition, no new arithmetic.
(0011 мінус-обернене
  (0010 (число)
    (змінити-знак (обернене число))))


; D8:01001011 ABS∘RECIP: true composition order is ABS(RECIP(x)).
(0011 модуль-після-обернення
  (0010 (число)
    (модуль (обернене число))))

; D8:00000101 ELT — для proper-list використовує D6:000100 NTH.
; Для інших sequence carriers потрібне окреме допущення механізму.
(0011 елемент-за-індексом
  (0010 (індекс елементи)
    (елемент-списку індекс елементи)))

; D8:11000101 MAP — лише спискова композиція над D6:101000 MAP.
; Атомарний ключ D8 тут не оголошений прямим callable opcode.
(0011 відобразити-елементи
  (0010 (дія елементи)
    (відобразити дія елементи)))

; D8:11111011 ONEP — кваліфікований D24+ числовий предикат.
; D5:01010 забезпечує numeric-domain check, D3:101 повертає D1.
; D7 цифри не конвертуються в числа.
(0011 одиниця?
  (0010 (число)
    (101 (01010 число #d24:000000000000000000000000)
         #d24:000000000000000000000001)))


; D8:10100110 1/ — точно той самий числовий закон, що D6:010110 RECIP.
; Це нова ратифікована поверхня, не нова машинна арифметика та не D8 direct call.
(0011 обернене-число
  (0010 (число)
    (обернене число)))
