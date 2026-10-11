; my-lisp bootstrap library: derived behavior belongs in the language itself.
; Bootstrap-бібліотека my-lisp: похідна поведінка належить самій мові.
; my-lisp-Bootstrap-Bibliothek: Abgeleitetes Verhalten gehört in die Sprache selbst.

(def identity (lambda (value) value))

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
(def list (lambda args args))

(def not
  (lambda (value)
    (cond
      (value (quote ()))
      (t t))))

; and/or — раніше були відсутні і в цьому файлі, і як Rust-білтіни
; (перевірено: обидва grep дають нуль збігів), тож кожен, хто підключав
; my-lisp, мусив бутстрапити власні (знайдено живцем 2026-08-27 у
; chess-lisp-zero/lib/chess.lisp). Макроси, не функції — інакше "and"/"or"
; втратили б коротке замикання, обчислюючи всі аргументи наперед. Мусять
; бути variadic (rest-параметр як голий символ, як `list` вище), не
; фіксованої арності — саме так їх і використовує реальний код, що вже
; існує. Порожній `(and)` -> t, порожній `(or)` -> () — той самий вибір,
; що й у Common Lisp/Scheme, узгоджений з G8 (нейтральний елемент
; логічного "і"/"або"). Перевірено живцем: коротке замикання (другий
; аргумент дійсно не обчислюється), варіативність на 3+ аргументах,
; передача самого значення, не лише t/() (напр. (and t 42) -> 42).
(defmacro and rest
  (cond
    ((atom rest) t)
    ((atom (cdr rest)) (car rest))
    (t
     ; Build the short-circuit cond AST from the primitive tree substrate.
     ; AND remains Lisp-owned; generic macro frontends need no private LIST
     ; semantic just to execute this law.
     (cons (quote cond)
           (cons (cons (car rest)
                       (cons (cons (quote and) (cdr rest))
                             (quote ())))
                 (cons (cons t
                             (cons (quote ())
                                   (quote ())))
                       (quote ())))))))

(defmacro or rest
  (cond
    ((atom rest) (quote ()))
    ((atom (cdr rest)) (car rest))
    (t
     ; Same primitive constructor discipline as AND above: preserve lazy
     ; short-circuit expansion without importing LIST into compiler authority.
     (cons (quote cond)
           (cons (cons (car rest)
                       (cons t (quote ())))
                 (cons (cons t
                             (cons (cons (quote or) (cdr rest))
                                   (quote ())))
                       (quote ())))))))

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
(def gensym
  (lambda (prefix)
    (string->symbol (string-append prefix (write-to-string (mono-ns))))))

(def pair
  (lambda (left right)
    (cons left (cons right (quote ())))))

(def second
  (lambda (values)
    (car (cdr values))))

(def third
  (lambda (values)
    (car (cdr (cdr values)))))

(def fourth
  (lambda (values)
    (car (cdr (cdr (cdr values))))))

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
(def cadddr fourth)

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
(def fifth
  (lambda (values)
    (car (cdr (cdr (cdr (cdr values)))))))

(def caar
  (lambda (values)
    (car (car values))))

(def cadr
  (lambda (values)
    (car (cdr values))))

(def cddr
  (lambda (values)
    (cdr (cdr values))))

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
(def length-onto
  (lambda (values acc)
    (cond
      ((atom values) (structural-kind empty-list) acc)
      ((atom values) (structural-kind pair)
       (length-onto (cdr values) (+ acc 1))))))


(def length
  (lambda (values)
    (length-onto values 0)))

(def reverse-onto
  (lambda (values acc)
    (cond
      ((atom values) (structural-kind empty-list) acc)
      ((atom values) (structural-kind pair)
       (reverse-onto (cdr values) (cons (car values) acc))))))

(def reverse
  (lambda (values)
    (reverse-onto values (quote ()))))

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
(def append
  (lambda (left right)
    (reverse-onto (reverse left) right)))

(def map-onto
  (lambda (f values acc)
    (cond
      ((atom values) (structural-kind empty-list) (reverse acc))
      ((atom values) (structural-kind pair)
       (map-onto f (cdr values) (cons (f (car values)) acc))))))

(def map
  (lambda (f values)
    (map-onto f values (quote ()))))

(def filter-onto
  (lambda (predicate values acc)
    (cond
      ((atom values) (reverse acc))
      ((predicate (car values)) (filter-onto predicate (cdr values) (cons (car values) acc)))
      (t (filter-onto predicate (cdr values) acc)))))

(def filter
  (lambda (predicate values)
    (filter-onto predicate values (quote ()))))

(def reduce
  (lambda (f acc values)
    (cond
      ((atom values) (structural-kind empty-list) acc)
      ((atom values) (structural-kind pair)
       (reduce f (f acc (car values)) (cdr values))))))

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
(defmacro let (bindings body)
  (cons (list (quote lambda) (map (lambda (binding) (car binding)) bindings) body)
        (map (lambda (binding) (second binding)) bindings)))

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
; on top of `eq` and `atom` rather than replacing them. Its answer belongs
; to the structural domain: `(structural-relation same|distinct)`, never a
; universal truth sentinel. Canonical three-part `cond` consumes the domain
; results explicitly; the historical two-part bridge exists only for callers
; not yet migrated.
(def equal?
  (lambda (a b)
    (cond
      ((atom a) (structural-kind pair)
       (cond
         ((atom b) (structural-kind pair)
          (cond
            ((equal? (car a) (car b)) (structural-relation same)
             (equal? (cdr a) (cdr b)))
            ((equal? (car a) (car b)) (structural-relation distinct)
             (quote (structural-relation distinct)))))
         ((atom b) (structural-kind empty-list)
          (quote (structural-relation distinct)))
         ((atom b) (structural-kind atom)
          (quote (structural-relation distinct)))))
      ((atom b) (structural-kind pair)
       (quote (structural-relation distinct)))
      ((eq a b) (identity-relation same)
       (quote (structural-relation same)))
      ((eq a b) (identity-relation distinct)
       (quote (structural-relation distinct))))))

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
(def nth
  (lambda (i lst)
    (cond
      ((eq i 0) (identity-relation same) (car lst))
      ((eq i 0) (identity-relation distinct)
       (nth (- i 1) (cdr lst))))))

(def member?
  (lambda (item lst)
    (cond
      ((atom lst) (structural-kind empty-list) (quote ()))
      ((atom lst) (structural-kind pair)
       (cond
         ((equal? item (car lst)) (structural-relation same) t)
         ((equal? item (car lst)) (structural-relation distinct)
          (member? item (cdr lst))))))))

(def assoc
  (lambda (key alist)
    (cond
      ((atom alist) (structural-kind empty-list) (quote ()))
      ((atom alist) (structural-kind pair)
       (cond
         ((equal? key (car (car alist))) (structural-relation same) (car alist))
         ((equal? key (car (car alist))) (structural-relation distinct)
          (assoc key (cdr alist))))))))

(defmacro let* (bindings body)
  (cond
    ((atom bindings) (structural-kind empty-list) body)
    ((atom bindings) (structural-kind pair)
     ; Build the recursive expansion from the primitive tree substrate only.
     ; This keeps let* semantics in Lisp while allowing generic macro
     ; frontends to execute the law without importing the higher-level list
     ; helper as host/compiler semantic authority.
     (cons (quote let)
           (cons (cons (car bindings) (quote ()))
                 (cons (cons (quote let*)
                             (cons (cdr bindings)
                                   (cons body (quote ()))))
                       (quote ())))))))

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
(def string-empty?
  (lambda (s) (eq s "")))

(def string-length
  (lambda (s)
    (cond
      ((string-empty? s) (identity-relation same) 0)
      (t t (+ 1 (string-length (string-rest s)))))))

(def string-prefix?
  (lambda (prefix s)
    (cond
      ((string-empty? prefix) (identity-relation same) t)
      ((string-empty? s) (identity-relation same) (quote ()))
      ((eq (string-first prefix) (string-first s))
       (identity-relation same)
       (string-prefix? (string-rest prefix) (string-rest s)))
      (t t (quote ())))))


(def string-contains?
  (lambda (needle s)
    (cond
      ((string-prefix? needle s) t t)
      ((string-empty? s) (identity-relation same) (quote ()))
      (t t (string-contains? needle (string-rest s))))))


; `symbol?` moved out of Rust after `write-to-string` made the distinction
; expressible without exceptions: among atoms, exactly a Symbol is identical
; to the Symbol reconstructed from its canonical text. The atom guard keeps
; primitive `eq` away from pairs. This works for arbitrary symbol names, not
; only reader-friendly identifiers, because `string->symbol` takes raw text.
; `symbol?` перенесено з Rust: серед атомів лише Symbol тотожний символу,
; відновленому з його канонічного тексту. `atom` не допускає пари до `eq`.
; `symbol?` wurde aus Rust verschoben: Unter Atomen ist nur ein Symbol mit dem
; aus seinem kanonischen Text rekonstruierten Symbol identisch; `atom` schützt `eq`.
(def symbol?
  (lambda (value)
    (cond
      ((atom value) (structural-kind empty-list) (quote ()))
      ((atom value) (structural-kind atom)
       (cond
         ((eq value (string->symbol (write-to-string value)))
          (identity-relation same) t)
         (t t (quote ()))))
      ((atom value) (structural-kind pair) (quote ())))))


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
(def largest-chunk
  (lambda (a b chunk mult)
    (cond
      ((< a (+ chunk chunk)) 1 (cons chunk mult))
      ((< a (+ chunk chunk)) 0
       (largest-chunk a b (+ chunk chunk) (+ mult mult))))))

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
(def quotient
  (lambda (a b)
    (cond
      ((eq b 0) (identity-relation same) (/ a b))
      ((eq b 0) (identity-relation distinct)
       (cond
         ((< a b) 1 0)
         ((< a b) 0
          (let ((chunk+mult (largest-chunk a b b 1)))
            (+ (cdr chunk+mult)
               (quotient (- a (car chunk+mult)) b)))))))))

(def mod
  (lambda (a b)
    (- a (* b (quotient a b)))))

; `<=` and `>=` stay Lisp-derived, but #216 now requires the derived
; operators to preserve the same exact-Q answer algebra as `<`, `>` and `=`:
; exact YES -> 1/1, exact NO -> 0/1, and any inexact operand -> Canon 0 `()`.
; Canonical three-part `cond` distinguishes exact NO (0) from no-answer `()`
; without routing either through generic truthiness.
(def nondecreasing-from?
  (lambda (current remaining)
    (cond
      ((atom remaining) (structural-kind empty-list) 1)
      ((< current (car remaining)) 1
       (nondecreasing-from? (car remaining) (cdr remaining)))
      ((= current (car remaining)) 1
       (nondecreasing-from? (car remaining) (cdr remaining)))
      ((= current (car remaining)) 0 0))))

(def nonincreasing-from?
  (lambda (current remaining)
    (cond
      ((atom remaining) (structural-kind empty-list) 1)
      ((> current (car remaining)) 1
       (nonincreasing-from? (car remaining) (cdr remaining)))
      ((= current (car remaining)) 1
       (nonincreasing-from? (car remaining) (cdr remaining)))
      ((= current (car remaining)) 0 0))))

(def <=
  (lambda (first . remaining)
    (nondecreasing-from? first remaining)))

(def >=
  (lambda (first . remaining)
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
(def digit->string
  ; Superseded by number->string's canonical delegation to write-to-string
  ; (FIX-NUMBER-TO-STRING-RATIONAL). Retained because racket/boot/core.lisp
  ; mirrors this file and fpga-lisp's assembler.lisp carries its own local
  ; variant — removal is a separate mirrored-surface decision, not a
  ; silent one.
  (lambda (d)
    (nth d (quote ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(def number->string-onto
  (lambda (n acc)
    (cond
      ((eq n 0) (identity-relation same) acc)
      ((eq n 0) (identity-relation distinct)
       (number->string-onto
         (quotient n 10)
         (string-append (digit->string (mod n 10)) acc))))))

(def number->string
  (lambda (n)
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
(defmacro -> forms
  (cond
    ((atom forms) (structural-kind empty-list) (quote ()))
    ((atom forms) (structural-kind pair)
     (cond
       ((atom (cdr forms)) (structural-kind empty-list) (car forms))
       ((atom (cdr forms)) (structural-kind pair)
        (let* ((x (car forms))
               (next (car (cdr forms)))
               (rest (cdr (cdr forms)))
               (step
                 (cond
                   ((atom next) (structural-kind empty-list) (list next x))
                   ((atom next) (structural-kind atom) (list next x))
                   ((atom next) (structural-kind pair)
                    (cons (car next) (cons x (cdr next)))))))
          (cond
            ((atom rest) (structural-kind empty-list) step)
            ((atom rest) (structural-kind pair)
             (cons (quote ->) (cons step rest))))))))))

(defmacro ->> forms
  (cond
    ((atom forms) (structural-kind empty-list) (quote ()))
    ((atom forms) (structural-kind pair)
     (cond
       ((atom (cdr forms)) (structural-kind empty-list) (car forms))
       ((atom (cdr forms)) (structural-kind pair)
        (let* ((x (car forms))
               (next (car (cdr forms)))
               (rest (cdr (cdr forms)))
               (step
                 (cond
                   ((atom next) (structural-kind empty-list) (list next x))
                   ((atom next) (structural-kind atom) (list next x))
                   ((atom next) (structural-kind pair)
                    (append next (list x))))))
          (cond
            ((atom rest) (structural-kind empty-list) step)
            ((atom rest) (structural-kind pair)
             (cons (quote ->>) (cons step rest))))))))))

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

(def sqrt-iter
  (lambda (guess x n)
    (cond
      ((= n 0) 1 guess)
      ((= n 0) 0
       (sqrt-iter (/ (+ guess (/ x guess)) 2) x (- n 1))))))

;; integer sqrt: Newton on quotients — provably terminating
(def isqrt
  (lambda (n)
    (cond
      ((< n 2) 1 n)
      ((< n 2) 0
       (isqrt-step n (quotient n 2))))))

(def isqrt-step
  (lambda (n g)
    (let ((next (quotient (+ g (quotient n g)) 2)))
      (cond
        ((< next g) 1 (isqrt-step n next))
        ((< next g) 0 g)))))

(def sqrt
  (lambda (x)
    (cond
      ((< x 0) 1 (quote ()))
      ((= x 0) 1 0)
      ((= x (quotient x 1)) 1
       (let ((r (isqrt x)))
         (cond
           ((= (* r r) x) t r)
           (t t (sqrt-iter (/ x 2) x 8)))))
      (t t (sqrt-iter (/ x 2.0) x 5)))))

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
(def abs
  (lambda (x)
    (cond
      ((< x 0) 1 (- x))
      ((< x 0) 0 x))))

; Required first parameter (dotted lambda-list, same pattern as
; `<=`/`>=` above) keeps zero arguments an Arity error via the
; evaluator's own lambda-binding check -- matching the removed Rust
; builtin's explicit "min/max expects at least one argument" error --
; without this Lisp definition needing to raise a custom error itself.
(def min
  (lambda (first . rest)
    (min-list (cons first rest))))

(def max
  (lambda (first . rest)
    (max-list (cons first rest))))

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
;    accumulator must use structural `equal?` against `(quote ())`.
(def min-list
  (lambda (items)
    (cond
      ((atom items) (structural-kind empty-list) (quote ()))
      ((atom items) (structural-kind pair)
       (let ((rest-min (min-list (cdr items))))
         (cond
           ((equal? rest-min (quote ())) (structural-relation same)
            (car items))
           ((equal? rest-min (quote ())) (structural-relation distinct)
            (cond
              ((< (car items) rest-min) 1 (car items))
              ((< (car items) rest-min) 0 rest-min)))))))))

(def max-list
  (lambda (items)
    (cond
      ((atom items) (structural-kind empty-list) (quote ()))
      ((atom items) (structural-kind pair)
       (let ((rest-max (max-list (cdr items))))
         (cond
           ((equal? rest-max (quote ())) (structural-relation same)
            (car items))
           ((equal? rest-max (quote ())) (structural-relation distinct)
            (cond
              ((> (car items) rest-max) 1 (car items))
              ((> (car items) rest-max) 0 rest-max)))))))))

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
(def my-postcore-stable-peer-projection
  (quote (
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
  )))

(def my-postcore-peer-group
  (lambda (semantic-id groups)
    (cond
      ((atom groups) (structural-kind empty-list)
       (quote ()))
      ((atom groups) (structural-kind pair)
       (let ((group (car groups)))
         (cond
           ((eq semantic-id (car group)) (identity-relation same)
            group)
           ((eq semantic-id (car group)) (identity-relation distinct)
            (my-postcore-peer-group semantic-id (cdr groups)))))))))

(def my-postcore-binding-status
  (lambda (surface bindings)
    (cond
      ((atom bindings) (structural-kind empty-list)
       (quote absent))
      ((atom bindings) (structural-kind pair)
       (let ((binding (car bindings)))
         (cond
           ((eq (symbol->string surface) (car binding)) (identity-relation same)
            (quote present))
           ((eq (symbol->string surface) (car binding)) (identity-relation distinct)
            (my-postcore-binding-status surface (cdr bindings)))))))))

(def my-postcore-missing-peers
  (lambda (source peers bindings)
    (cond
      ((atom peers) (structural-kind empty-list)
       (quote ()))
      ((atom peers) (structural-kind pair)
       (let ((peer (car peers)))
         (cond
           ((eq source peer) (identity-relation same)
            (my-postcore-missing-peers source (cdr peers) bindings))
           ((eq source peer) (identity-relation distinct)
            (cond
              ((eq (my-postcore-binding-status peer bindings) (quote present))
               (identity-relation same)
               (my-postcore-missing-peers source (cdr peers) bindings))
              ((eq (my-postcore-binding-status peer bindings) (quote absent))
               (identity-relation same)
               (cons peer
                     (my-postcore-missing-peers
                       source
                       (cdr peers)
                       bindings)))))))))))

; Build one expression whose nested DEFINE forms all execute in the caller's
; environment. This is why materialization is a macro rather than a function:
; an ordinary function would define peers only in its temporary child frame.
(def my-postcore-build-definitions
  (lambda (source peers)
    (cond
      ((atom peers) (structural-kind empty-list)
       source)
      ((atom peers) (structural-kind pair)
       (list (quote define)
             (car peers)
             (my-postcore-build-definitions source (cdr peers)))))))

(defmacro my-postcore-materialize-stable-peers args
  (let* ((semantic-id (car args))
         (source (second args))
         (group
           (my-postcore-peer-group
             semantic-id
             my-postcore-stable-peer-projection)))
    (cond
      ((atom group) (structural-kind empty-list)
       source)
      ((atom group) (structural-kind pair)
       (my-postcore-build-definitions
         source
         (my-postcore-missing-peers source (cdr group) (env)))))))
