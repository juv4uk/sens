
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
(00001010 and rest
  (110
    ((010 rest) (010 ()))
    ((010 (011 rest)) (100 rest))
    ((010 ())
     (111 (001 00000111)
       (111
         (111 (100 rest)
           (111
             (111 (001 and) (011 rest))
             (001 ())))
         (111
           (111
             (111 (001 00000010)
               (111 (001 ()) (001 ())))
             (111
               (001 00000010)
               (111
                 (111 (001 00000100)
                   (111 (001 ())
                     (111 (001 ()) (001 ()))))
                 (001 ())))
           (001 ()))))))))

(00001010 or rest
  (110
    ((010 rest) (010 (111 () ())))
    ((010 (011 rest)) (100 rest))
    ((010 ())
     (111 (001 00000111)
       (111
         (111 (100 rest)
           (111
             (111 (001 00000010)
               (111 (001 ()) (001 ())))
             (001 ())))
         (111
           (111
             (111 (001 00000010)
               (111 (001 ()) (001 ())))
             (111
               (111 (001 or) (011 rest))
               (001 ())))
           (001 ())))))))

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
    (11101101 (110011110 prefix (11110100 (01011010))))))

(0011 pair
  (0010 (left right)
    (111 left (111 right (001 ())))))

; Ratified exact selectors: D4:1000 CAAR, D4:1001 CADR,
; D4:0111 CDDR, D5:10011 CADDR, D6:100111 CADDDR.
; Selector law is compiled from domain+bit width, never from English aliases.
; D7 is text data and is NOT used for fifth (four CDR steps).

(0011 second
  (0010 (values)
    (1001 values)))

(0011 third
  (0010 (values)
    (10011 values)))

(0011 fourth
  (0010 (values)
    (100111 values)))

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
    (100 (011 (011 (011 (011 values)))))))

(0011 caar
  (0010 (values)
    (1000 values))

(0011 cadr second)

(0011 cddr
  (0010 (values)
    (0111 values))

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
(0011 length-onto
  (0010 (values acc)
    (110
      ; D4 NULL checks exactly the end of a proper list. NOT(ATOM) would
      ; terminate nonempty lists immediately and report every length as 0.
      ((0101 values) acc)
      ; Only a cons cell advances the accumulator. An improper nonempty
      ; tail is not silently counted as an empty list.
      ((0100 (010 values))
       (length-onto (011 values) (01010 acc 1))))))


(0011 length
  (0010 (values)
    (length-onto values 0)))

; D5:10101 REVERSE-ONTO: canonical ratified surface owns the exact-domain
; binding. The historical English spelling below is compatibility-only.
; D1-controlled reverse: empty ends the fold; a pair advances it.
; Structural (0) and historical truth coercion are not valid D3 predicates.
(0011 зворот-до
  (0010 (values acc)
    (110
      ((0101 values) acc)
      ((0100 (010 values))
       (зворот-до (011 values) (111 (100 values) acc))))))

; Internal derived closure for D6:000000 LENGTH when no admitted D6
; evaluator mechanism exists. This is a Lisp binding, not D6 dispatch.
(0011 внутрішня-довжина length)

(0011 reverse-onto зворот-до)

(0011 reverse
  (0010 (values)
    (зворот-до values (001 ()))))

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

; MAP is derived in Lisp: D4 NULL detects exactly the empty list,
; while D3 ATOM excludes improper non-pair tails. Both produce D1 control
; bits; structural (0) / equal? must never act as a COND predicate.
(0011 map-onto
  (0010 (f values acc)
    (110
      ((0101 values) (10100 acc))
      ((0100 (010 values))
       (map-onto f (011 values) (111 (f (100 values)) acc))))))

(0011 map
  (0010 (f values)
    (map-onto f values (001 ()))))

(0011 filter-onto
  (0010 (predicate values acc)
    (110
      ((0100 (010 values)) (10100 acc))
      ((010 values)  (10100 acc))
      ((010 values) 
       (let ((decision (predicate (100 values))))
         (110
           (decision
            (filter-onto predicate (011 values) (111 (100 values) acc)))
           ((010 predicate)
            (filter-onto predicate (011 values) acc))))))))

(0011 filter
  (0010 (predicate values)
    (filter-onto predicate values (001 ()))))

(0011 reduce
  (0010 (f acc values)
    (110
      ((0100 (010 values)) acc)
      ((010 values) 
       (reduce f (f acc (100 values)) (011 values))))))

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
; D6:101000 MAP is a ratified coordinate, but currently has no
; admitted evaluator call mechanism. Until that mechanism is proved, the
; existing Lisp-owned map closure is the executable derivation for let.
; No invented D6 runtime dispatch or numeric/legacy fallback is introduced.
(0011 внутрішнє-відображення map)
; ЛІХТАР: a bounded macro bridge for legacy Lisp source modules.
; A ratified D6 LET identity without an admitted evaluator mechanism is NOT
; silently callable. This macro expands a surface call into a fresh lambda
; application through the already proved Lisp-owned LET macro. The binding
; list and body are syntax, not values or fabricated D6 residents.
; (нехай-похідне ((x 7) (y 9)) (00100111 x y)) => (let ((x 7) (y 9)) ...).
(00001010 нехай-похідне (bindings body)
  (111 (001 let)
    (111 bindings (111 body (001 ())))))

(00001010 let (bindings body)
  (111 (1110 (001 00001000) (внутрішнє-відображення (0010 (binding) (100 binding)) bindings) body)
        (внутрішнє-відображення (0010 (binding) (1001 binding)) bindings)))

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
      ((0100 (010 a))
       (110
         ((0100 (010 b))
          (001 (1)))
         ((010 b) 
          (001 (0)))
         ((010 b) 
          (001 (0)))))
      ((010 a) 
       (110
         ((0100 (010 b))
          (001 (0)))
         ((010 b) 
          (110
            ((101 a b) 
             (001 (1)))
            ((101 a b) 
             (001 (0)))))
         ((010 b) 
          (001 (0)))))
      ((010 a) 
       (110
         ((0100 (010 b))
          (001 (0)))
         ((010 b) 
          (001 (0)))
         ((010 b) 
          (110
            ((11110111 (100 a) (100 b)) 
             (11110111 (011 a) (011 b)))
            ((0100 (11110111 (100 a) (100 b)))
             (001 (0))))))))))

; Exact-Q uses 1 for YES and 0 for NO.  Structural and identity relations
; retain their own result domains, so predicate consumers normalize them here.
(0011 truthy?
  (0010 (value)
    (110
      
      ((010 value) 
       (110
         ((101 value 0)  (001 ()))
         ((0100 (101 value 0)) t)))
      ((010 value) 
       (110
         ((11110111 value (001 (0)))  (001 ()))
         ((11110111 value (001 (0)))  (001 ()))
         ((11110111 value (001 (0)))  (001 ()))
         ((010 ())  t))))))

(0011 not?
  (0010 (value)
    (110
      ((truthy? value)  (001 ()))
      ((0100 (truthy? value)) t))))


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
(0011 nth
  (0010 (i lst)
    (110
      ((101 i 0)  (100 lst))
      ((101 i 0) 
       (000100 (01011 i 1) (011 lst))))))

(0011 member?
  (0010 (item lst)
    (110
      
      ((010 lst) 
       (110
         ((11110111 item (100 lst))  t)
         ((0100 (11110111 item (100 lst)))
          (11101 item (011 lst))))))))

(0011 assoc
  (0010 (key alist)
    (110
      
      ((010 alist) 
       (110
         ((11110111 key (100 (100 alist)))  (100 alist))
         ((0100 (11110111 key (100 (100 alist))))
          (11100 key (011 alist))))))))


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

(00001010 let* (bindings body)
  (110
    ((010 bindings) body)
    ((010 (001 ()))
     ; Expand directly to ((lambda (name) (let* tail body)) value).
     ; This avoids the unadmitted D6:001000 LET execution path while
     ; retaining the language-owned sequential-binding law.
     (111
       (111 (001 00001000)
         (111
           (111 (100 (100 bindings)) (001 ()))
           (111
             (111 (001 let*)
               (111 (011 bindings)
                 (111 body (001 ()))))
             (001 ()))))
       (111 (1001 (100 bindings)) (001 ()))))))

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
         ((101 (110101011 (11110100 value))
              (110101011 (11110100 "")))
          
          (001 (class-membership string member)))
         ((101 (110101011 (11110100 value))
              (110101011 (11110100 "")))
          
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
; (00111111), string-rest (01000000) і string->codepoint (01000101). Не-рядок
; дає природну помилку Type від string-first; неправильна кількість
; аргументів — Arity від прив'язки лямбди.
(0011 string<?
  (0010 (a b)
    (110
      ; Порожній бік: інший перевіряється як рядок (string-append дає Type).
      ((110011100 b) 
       (1001 (1110 (110011110 a "") (001 ()))))
      ((110011100 a) 
       (1001 (1110 (110011110 b "") t)))
      ((11010 (11100000 (110101011 a)) (11100000 (110101011 b)))  t)
      ((101 (110101011 a) (110101011 b)) 
       (10110001 (110011101 a) (110011101 b)))
      )))



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
         ((101 value (11101101 (11110100 value)))
           (010 (001 ())))
         ))
      ((010 value)  (001 ())))))


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
; Recurse through this Lisp-owned integer quotient; D5:10111 is exact division, not floor division.
(0011 quotient
  (0010 (a b)
    (110
      ((101 b 0)  (11110110 a b))
      ((010 (001 ())) 
       (110
         ((11010 a b)  0)
         ((0100 (11010 a b))
          (let ((chunk+mult (largest-chunk a b b 1)))
            (01010 (011 chunk+mult)
               (quotient (01011 a (100 chunk+mult)) b)))))))))

; The remainder uses the same Lisp-owned integer quotient: a - b * floor(a / b).
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
      ((11110111 current (100 remaining)) 
       (nondecreasing-from? (100 remaining) (011 remaining)))
      ((0100 (11110111 current (100 remaining))) 0))))

(0011 nonincreasing-from?
  (0010 (current remaining)
    (110
      ((0100 (010 remaining)) 1)
      ((11011 current (100 remaining)) 
       (nonincreasing-from? (100 remaining) (011 remaining)))
      ((11110111 current (100 remaining)) 
       (nonincreasing-from? (100 remaining) (011 remaining)))
      ((0100 (11110111 current (100 remaining))) 0))))

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
         (110011110 (01000111 (00101100 n #d10)) acc))))))

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
    (11110100 n)))

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
(00001010 -> forms
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
             (111 (001 ->) (111 step rest))))))))))

(00001010 ->> forms
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
             (111 (001 ->>) (111 step rest))))))))))

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
      ((11110111 n 0)  guess)
      ((0100 (11110111 n 0))
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
      ((11110111 x 0)  0)
      ((11110111 x (10111 x 1)) 
       (let ((r (110111010 x)))
         (110
           ((11110111 (10110 r r) x)  r)
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
(0011 abs
  (0010 (x)
    (110
      ((11010 x 0)  (01011 0 x))
      ((0100 (11010 x 0)) x))))

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
;    accumulator must use structural `equal?` against `(quote ())`.
(0011 min-list
  (0010 (items)
    (110
      
      ((010 items) 
       (let ((rest-min (000010 (011 items))))
         (110
           ((11110111 rest-min (001 ())) 
            (100 items))
           ((0100 (11110111 rest-min (001 ())))
            (110
              ((11010 (100 items) rest-min)  (100 items))
              ((0100 (11010 (100 items) rest-min)) rest-min)))))))))

(0011 max-list
  (0010 (items)
    (110
      
      ((010 items) 
       (let ((rest-max (000011 (011 items))))
         (110
           ((11110111 rest-max (001 ())) 
            (100 items))
           ((0100 (11110111 rest-max (001 ())))
            (110
              ((11011 (100 items) rest-max)  (100 items))
              ((0100 (11011 (100 items) rest-max)) rest-max)))))))))

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
      
      ((010 groups) 
       (let ((group (100 groups)))
         (110
           ((101 semantic-id (100 group)) 
            group)
           ((101 semantic-id (100 group)) 
            (my-postcore-peer-group semantic-id (011 groups)))))))))

(0011 my-postcore-binding-status
  (0010 (surface bindings)
    (110
      ((0100 (010 bindings))
       (001 absent))
      ((010 bindings) 
       (let ((binding (100 bindings)))
         (110
           ((101 (11101110 surface) (100 binding)) 
            (001 present))
           ((101 (11101110 surface) (100 binding)) 
            (my-postcore-binding-status surface (011 bindings)))))))))

(0011 my-postcore-missing-peers
  (0010 (source peers bindings)
    (110
      
      ((010 peers) 
       (let ((peer (100 peers)))
         (110
           ((101 source peer) 
            (my-postcore-missing-peers source (011 peers) bindings))
           ((101 source peer) 
            (110
              ((101 (my-postcore-binding-status peer bindings) (001 present))
               
               (my-postcore-missing-peers source (011 peers) bindings))
              ((101 (my-postcore-binding-status peer bindings) (001 absent))
               
               (111 peer
                     (my-postcore-missing-peers
                       source
                       (011 peers)
                       bindings)))))))))))

; Build one expression whose nested DEFINE forms all execute in the caller's
; environment. This is why materialization is a macro rather than a function:
; an ordinary function would define peers only in its temporary child frame.
(0011 my-postcore-build-definitions
  (0010 (source peers)
    (110
      ((0100 (010 peers))
       source)
      ((010 peers) 
       (1110 (001 define)
             (100 peers)
             (my-postcore-build-definitions source (011 peers)))))))

(00001010 my-postcore-materialize-stable-peers args
  (001001 ((semantic-id (100 args))
         (source (1001 args))
         (group
           (my-postcore-peer-group
             semantic-id
             my-postcore-stable-peer-projection)))
    (110
      ((0100 (010 group))
       source)
      ((010 group) 
       (my-postcore-build-definitions
         source
         (my-postcore-missing-peers source (011 group) (11100111)))))))

; Ділення з остачою (Lisp 1.5 DIVIDE): повертає список (частка остача).
(0011 divmod
  (0010 (dividend divisor)
    (1110 (10111 dividend divisor) (00101100 dividend divisor))))

; McCarthy 1960, §3d: null, subst, sublis, maplist, apply — закон Core4, коди СЕНС.
(0011 null?
  (0010 (x)
    (110
      ((0100 (010 x)) t)
      ((010 x)  (001 ()))
      ((010 x)  (001 ())))))

(0011 subst
  (0010 (x y z)
    (110
      ((010 z) 
       (111 (11111 x y (100 z)) (11111 x y (011 z))))
      ((0100 (010 z))
       (110
         ((101 z y)  x)
         ((0100 (101 z y)) z)))
      ((010 z) 
       (110
         ((101 z y)  x)
         ((0100 (101 z y)) z))))))

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

(0011 maplist
  (0010 (x f)
    (110
      
      ((010 x) 
       (111 (f x) (000101 (011 x) f))))))

(0011 apply-quote-args
  (0010 (m)
    (110
      
      ((010 m) 
       (111 (111 (001 00000001) (111 (100 m) (001 ())))
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
