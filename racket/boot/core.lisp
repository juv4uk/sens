; Початкова бібліотека Ліспу: похідна поведінка належить самій мові.
; Основні функції мають українські імена; старі назви нижче — сумісні зв'язування.
; Історичні двійкові виклики збережено як дані первісної реалізації.

(0011 тотожність (0010 (значення) значення))
(0011 identity тотожність)

; Мовний описувач історичної восьмибітної двійкової форми.
; Читач трактує наступні джерельні форми як двійкові дані до наступної
; форми верхнього рівня. Десяткові цілі залишаються звичайними числами.
; Цей архівний опис не надає сучасним доменам нової семантики.
(0011 binary
  (0010 (ширина)
    (1110 (001 binary) ширина)))

; «список» раніше був спеціальною формою виконавця Rust.
; Від 09.08.2026 змінна-список параметрів функції приймає всі аргументи
; у порядку зліва направо; тому список визначається всередині Lisp.
; Це похідна мовна операція, а не окремий закон зовнішнього виконавця.
; Розміщена до макросів «let» і «let*», які потребують побудови списків.
; Історичний псевдонім «list» залишений для сумісності споживачів.
(0011 список (0010 аргументи аргументи))
(0011 list список)

; Основне ім'я заперечення — українська проєкція D4.
; Сумісне ім'я вказує на те саме замикання без дублювання реалізації.
(0011 хибне?
  (0010 (значення)
    (110
      (значення (001 ()))
      (t t))))
(0011 not хибне?)

(0011 пара
  (0010 (лівий правий)
    (111 лівий (111 правий (001 ())))))
(0011 pair пара)

(0011 друге
  (0010 (значення)
    (100 (011 значення))))
(0011 second друге)

(0011 третє
  (0010 (значення)
    (100 (011 (011 значення)))))
(0011 third третє)

(0011 четверте
  (0010 (значення)
    (100 (011 (011 (011 значення))))))
(0011 fourth четверте)

; cadddr — the classical car/cdr-composition name for the exact same
; operation fourth already performs; kept as an alias (same closure
; object, not a second definition) since real callers already spell it
; this way (lib/reason.my had its own local (def cadddr ...) before
; this, character-for-character identical to fourth's body).
; cadddr — класична car/cdr-композиційна назва для тієї самої операції,
; що вже виконує fourth; лишено як псевдонім (той самий об'єкт-closure,
; не друге визначення), бо реальні виклики вже пишуть саме так
; (lib/reason.my мав власний локальний (def cadddr ...) до цього,
; посимвольно ідентичний тілу fourth).
(0011 cadddr четверте)

; fifth — same single-parameter primitive-chain pattern as second/third/
; fourth, one step deeper. Found duplicated in two places at once:
; lib/narrate.my's own local (def fifth ...), character-for-character
; identical, and lib/persistent-map.my's node-right, same operation
; spelled out by hand rather than named.
; fifth — той самий однопараметричний ланцюжок примітивів, що й
; second/third/fourth, ще на крок глибший. Знайдено дубльованим одразу
; у двох місцях: власний локальний (def fifth ...) у lib/narrate.my,
; посимвольно ідентичний, і node-right у lib/persistent-map.my — та
; сама операція, виписана вручну замість названа.
(0011 п'ятий
  (0010 (значення)
    (100 (011 (011 (011 (011 значення)))))))
(0011 fifth п'ятий)

; D4:1000 — перше від першого складника пари.
(0011 перше-першого
  (0010 (значення)
    (100 (100 значення))))
(0011 caar перше-першого)

; D4:1001 уже визначено як «друге»; не дублюємо замикання.
(0011 cadr друге)

; D4:0111 — решта від решти.
(0011 решта-решти
  (0010 (значення)
    (011 (011 значення))))
(0011 cddr решта-решти)

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
  (0010 (значення накопичувач)
    (110
      ((010 значення) накопичувач)
      (t (довжина-до (011 значення) (01010 накопичувач 1))))))
(0011 length-onto довжина-до)

(0011 довжина
  (0010 (значення)
    (довжина-до значення 0)))
(0011 length довжина)

(0011 зворот-до
  (0010 (значення накопичувач)
    (110
      ((010 значення) накопичувач)
      (t (зворот-до (011 значення) (111 (100 значення) накопичувач))))))
(0011 reverse-onto зворот-до)

(0011 зворот
  (0010 (значення)
    (зворот-до значення (001 ()))))
(0011 reverse зворот)

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
(0011 приєднати
  (0010 (лівий правий)
    (зворот-до (зворот лівий) правий)))
(0011 append приєднати)

(0011 відобразити-до
  (0010 (перетворення значення накопичувач)
    (110
      ((010 значення) (зворот накопичувач))
      (t (відобразити-до перетворення (011 значення) (111 (перетворення (100 значення)) накопичувач))))))
(0011 map-onto відобразити-до)

(0011 відобразити
  (0010 (перетворення значення)
    (відобразити-до перетворення значення (001 ()))))
(0011 map відобразити)

(0011 відсіяти-до
  (0010 (предикат значення накопичувач)
    (110
      ((010 значення) (зворот накопичувач))
      ((предикат (100 значення)) (відсіяти-до предикат (011 значення) (111 (100 значення) накопичувач)))
      (t (відсіяти-до предикат (011 значення) накопичувач)))))
(0011 filter-onto відсіяти-до)

(0011 відсіяти
  (0010 (предикат значення)
    (відсіяти-до предикат значення (001 ()))))
(0011 filter відсіяти)

(0011 згорнути
  (0010 (операція накопичувач значення)
    (110
      ((010 значення) накопичувач)
      (t (згорнути операція (операція накопичувач (100 значення)) (011 значення))))))
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
(00001010 let (зв'язування тіло)
  (111 (список (001 lambda) (відобразити (0010 (зв'язування-елемент) (100 зв'язування-елемент)) зв'язування) тіло)
        (відобразити (0010 (зв'язування-елемент) (друге зв'язування-елемент)) зв'язування)))

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
; on top of `eq` and `atom` rather than replacing them: two atoms compare
; via `eq` (always safe — both sides are already known atoms in that
; branch); two pairs compare by recursing into `car`/`cdr`; an atom against
; a pair is unconditionally false, checked before ever reaching `eq` so it
; can't be handed a non-atom the way `var?` and `unify` in lib/unify.my
; originally were (see that file's header comment for the bug that caught).
; `eq` навмисно приймає лише атоми, за оригінальним примітивом Маккарті
; (див. docs/language-core.md) — `(eq '(1 2) '(1 2))` падає замість
; структурного порівняння. `equal?` — структурний/глибокий відповідник,
; побудований поверх `eq` і `atom`, не замість них: два атоми порівнюються
; через `eq` (завжди безпечно — обидві сторони вже точно атоми в цій
; гілці); дві пари порівнюються рекурсією в `car`/`cdr`; атом проти пари —
; безумовно хиба, перевіряється до того, як дійде до `eq`, тож йому не
; можна підсунути не-атом так, як спершу можна було `var?` і `unify` в
; lib/unify.my (баг, який це зловив, описано в header-коментарі того файлу).
; `eq` akzeptiert nach McCarthys ursprünglichem Primitiv bewusst nur Atome
; (siehe docs/language-core.md) — `(eq '(1 2) '(1 2))` löst einen Fehler
; aus statt strukturell zu vergleichen. `equal?` ist das
; strukturelle/tiefe Gegenstück, aufgebaut auf `eq` und `atom`, statt sie
; zu ersetzen: zwei Atome vergleichen sich über `eq` (immer sicher — beide
; Seiten sind in diesem Zweig bereits bekanntermaßen Atome); zwei Paare
; vergleichen sich durch Rekursion in `car`/`cdr`; ein Atom gegen ein Paar
; ist unbedingt falsch, geprüft bevor es je zu `eq` kommt, sodass ihm nie
; ein Nicht-Atom untergeschoben werden kann, wie es `var?` und `unify` in
; lib/unify.my anfangs passieren konnte (der dabei gefangene Bug steht im
; Header-Kommentar dieser Datei).
(0011 однакові?
  (0010 (ліве праве)
    (110
      ((010 ліве) (110 ((010 праве) (101 ліве праве)) (t (001 ()))))
      ((010 праве) (001 ()))
      (t (110
           ((однакові? (100 ліве) (100 праве)) (однакові? (011 ліве) (011 праве)))
           (t (001 ())))))))
(0011 equal? однакові?)

; nth/member?/assoc (G5 test: already expressible via existing means?)
; — yes, same recursive-list-walk shape as length/reverse above.
; Surfaced from the fpga-lisp session's assembler.my (2026-08-10), which
; had independently reimplemented all three locally (as nth, contains?/
; any-eq?, and assoc-str) because lib/core.my didn't have them — real,
; evidenced duplication, not a speculative gap. A generalized assoc here
; also matches the shape lib/meta-eval.my's own env-lookup already hand-
; rolls for its specific (symbol . value) alist case.
; nth/member?/assoc (G5-тест: уже виразне через наявне?) — так, та сама
; форма рекурсивного обходу списку, що й length/reverse вище. Знахідка
; з сесії fpga-lisp, assembler.my (2026-08-10), яка незалежно
; перевинайшла всі три локально (як nth, contains?/any-eq? і assoc-str),
; бо lib/core.my їх не мав — реальне, доказове дублювання, не
; спекулятивна прогалина. Узагальнений assoc тут також збігається з
; формою, яку lib/meta-eval.my's власний env-lookup уже вручну пише для
; свого специфічного випадку asoc-списку (symbol . value).
(0011 елемент-списку-за-індексом
  (0010 (індекс список)
    (110
      ((101 індекс 0) (100 список))
      (t (елемент-списку-за-індексом (01011 індекс 1) (011 список))))))
(0011 nth елемент-списку-за-індексом)

(0011 значення-у-списку?
  (0010 (елемент список)
    (110
      ((010 список) (001 ()))
      ((однакові? елемент (100 список)) t)
      (t (значення-у-списку? елемент (011 список))))))
(0011 member? значення-у-списку?)

(0011 знайти-за-ключем
  (0010 (ключ список-пар)
    (110
      ((010 список-пар) (001 ()))
      ((однакові? ключ (100 (100 список-пар))) (100 список-пар))
      (t (знайти-за-ключем ключ (011 список-пар))))))
(0011 assoc знайти-за-ключем)

(00001010 let* (зв'язування тіло)
  (110
    ((010 зв'язування) тіло)
    (t
     ; Build the recursive expansion from the primitive tree substrate only.
     ; This keeps let* semantics in Lisp while allowing generic macro
     ; frontends to execute the law without importing the higher-level list
     ; helper as host/compiler semantic authority.
     (111 (001 let)
           (111 (111 (100 зв'язування) (001 ()))
                 (111 (111 (001 let*)
                             (111 (011 зв'язування)
                                   (111 тіло (001 ()))))
                       (001 ())))))))

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
(0011 рядок-порожній?
  (0010 (рядок) (101 рядок "")))
(0011 string-empty? рядок-порожній?)

(0011 рядок-довжина
  (0010 (рядок)
    (110
      ((рядок-порожній? рядок) 0)
      (t (01010 1 (рядок-довжина (110011101 рядок)))))))
(0011 string-length рядок-довжина)

(0011 рядок-префікс?
  (0010 (префікс рядок)
    (110
      ((рядок-порожній? префікс) t)
      ((рядок-порожній? рядок) (001 ()))
      ((101 (110101011 префікс) (110101011 рядок))
       (рядок-префікс? (110011101 префікс) (110011101 рядок)))
      (t (001 ())))))
(0011 string-prefix? рядок-префікс?)

(0011 рядок-містить?
  (0010 (зразок рядок)
    (110
      ((рядок-префікс? зразок рядок) t)
      ((рядок-порожній? рядок) (001 ()))
      (t (рядок-містить? зразок (110011101 рядок))))))
(0011 string-contains? рядок-містить?)

; `symbol?` moved out of Rust after `write-to-string` made the distinction
; expressible without exceptions: among atoms, exactly a Symbol is identical
; to the Symbol reconstructed from its canonical text. The atom guard keeps
; primitive `eq` away from pairs. This works for arbitrary symbol names, not
; only reader-friendly identifiers, because `string->symbol` takes raw text.
; `symbol?` перенесено з Rust: серед атомів лише Symbol тотожний символу,
; відновленому з його канонічного тексту. `atom` не допускає пари до `eq`.
; `symbol?` wurde aus Rust verschoben: Unter Atomen ist nur ein Symbol mit dem
; aus seinem kanonischen Text rekonstruierten Symbol identisch; `atom` schützt `eq`.
(0011 символ?
  (0010 (значення)
    (110
      ((010 значення)
       (110
         ((101 значення (11101101 (11110100 значення))) t)
         (t (001 ()))))
      (t (001 ())))))
(0011 symbol? символ?)

; quotient/mod (G5 test: already expressible via existing means?) — yes.
; Unlike bitwise operations (AND/OR/XOR/shift — no primitive exposes a
; number's binary representation at all, so those would genuinely need a
; new Rust primitive), integer division and remainder for non-negative
; integers fall straight out of arithmetic and comparison primitives
; already here — no new Rust code, same class of gap as string-length
; before it. Surfaced from the fpga-lisp session's assembler.my
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
; нового Rust-примітиву), цілочисельне ділення й остача для
; невід'ємних чисел випливають напряму з наявних арифметичних і
; порівняльних примітивів — без нового Rust-коду, той самий клас
; прогалини, що й string-length раніше. Знахідка з сесії fpga-lisp,
; assembler.my (2026-08-10), яка позначила ВІДСУТНІСТЬ bitwise/mod, але
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
; Допоміжна функція двійкового ділення з українським основним ім'ям.
(0011 знайти-найбільший-блок-частки
  (0010 (ділене дільник частина кратність)
    (110
      ((11010 ділене (01010 частина частина)) (111 частина кратність))
      (t (знайти-найбільший-блок-частки ділене дільник (01010 частина частина) (01010 кратність кратність))))))
(0011 largest-chunk знайти-найбільший-блок-частки)

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
; D5:10111 — первинне визначення частки.
(0011 частка
  (0010 (ділене дільник)
    (110
      ((101 дільник 0) (11110110 ділене дільник))
      ((11010 ділене дільник) 0)
      (t (let ((частина-і-кратність (знайти-найбільший-блок-частки ділене дільник дільник 1)))
           (01010 (011 частина-і-кратність) (частка (01011 ділене (100 частина-і-кратність)) дільник)))))))
(0011 quotient частка)

; D8:00101100 — первинне визначення модульної остачі.
(0011 модульна-остача
  (0010 (ділене дільник)
    (01011 ділене (10110 дільник (частка ділене дільник)))))
(0011 mod модульна-остача)

; `<=` and `>=` need no Rust dispatch: the strict comparisons plus equality
; already preserve exact/inexact numeric semantics, while ordinary recursion
; supplies variadic chaining. A required first parameter keeps zero arguments
; an Arity error; one argument is vacuously ordered, matching the old builtin.
; `<=` і `>=` не потребують Rust-dispatch: строгих порівнянь і рівності вже
; досить, а ланцюжок дає звичайна рекурсія. Обов'язковий перший параметр
; зберігає Arity для нуля аргументів; один аргумент тривіально впорядкований.
; `<=` und `>=` brauchen keinen Rust-Dispatch: strikte Vergleiche und Gleichheit
; reichen, gewöhnliche Rekursion liefert die Verkettung. Der Pflichtparameter
; erhält den Arity-Fehler bei null Argumenten; ein Argument ist trivial geordnet.
; Внутрішня перевірка неспадання списку.
(0011 перевірити-неспадання-значень?
  (0010 (поточне решта-значень)
    (110
      ((010 решта-значень) t)
      ((11010 поточне (100 решта-значень))
       (перевірити-неспадання-значень? (100 решта-значень) (011 решта-значень)))
      ((11110111 поточне (100 решта-значень))
       (перевірити-неспадання-значень? (100 решта-значень) (011 решта-значень)))
      (t (001 ())))))
(0011 nondecreasing-from? перевірити-неспадання-значень?)

; Внутрішня перевірка незростання списку.
(0011 перевірити-незростання-значень?
  (0010 (поточне решта-значень)
    (110
      ((010 решта-значень) t)
      ((11011 поточне (100 решта-значень))
       (перевірити-незростання-значень? (100 решта-значень) (011 решта-значень)))
      ((11110111 поточне (100 решта-значень))
       (перевірити-незростання-значень? (100 решта-значень) (011 решта-значень)))
      (t (001 ())))))
(0011 nonincreasing-from? перевірити-незростання-значень?)

(0011 <=
  (0010 (перший . решта-значень)
    (перевірити-неспадання-значень? перший решта-значень)))

(0011 >=
  (0010 (перший . решта-значень)
    (перевірити-незростання-значень? перший решта-значень)))

; Числовий друк має один канонічний закон — ратифікований D9.
; Точне подання цілих чисел і скорочених дробів визначає значення-у-текст.
; Окремий рекурсивний акумулятор дублював цей закон і більше не потрібний.
(визначити число-рядок
  (функція (число-аргумент)
    (значення-у-текст число-аргумент)))
; Сумісні англомовні назви залишаються псевдонімами тих самих Lisp-значень.
(визначити number->string число-рядок)

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
(00001010 -> форми
  (110
    ((010 форми) (001 ()))
    ((010 (011 форми)) (100 форми))
    (t (let* ((початок (100 форми))
              (наступна-форма (100 (011 форми)))
              (залишок-форм (011 (011 форми)))
              (поточний-крок (110 ((010 наступна-форма) (список наступна-форма початок))
                          (t (111 (100 наступна-форма) (111 початок (011 наступна-форма)))))))
         (110
           ((010 залишок-форм) поточний-крок)
           (t (111 (001 ->) (111 поточний-крок залишок-форм))))))))

(00001010 ->> форми
  (110
    ((010 форми) (001 ()))
    ((010 (011 форми)) (100 форми))
    (t (let* ((початок (100 форми))
              (наступна-форма (100 (011 форми)))
              (залишок-форм (011 (011 форми)))
              (поточний-крок (110 ((010 наступна-форма) (список наступна-форма початок))
                          (t (приєднати наступна-форма (список початок))))))
         (110
           ((010 залишок-форм) поточний-крок)
           (t (111 (001 ->>) (111 поточний-крок залишок-форм))))))))