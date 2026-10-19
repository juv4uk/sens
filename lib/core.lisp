
; my-lisp bootstrap library: derived behavior belongs in the language itself.
; Bootstrap-бібліотека my-lisp: похідна поведінка належить самій мові.
; my-lisp-Bootstrap-Bibliothek: Abgeleitetes Verhalten gehört in die Sprache selbst.

(визначити тотожність (функція (значення) значення))

; D4:0101 NULL `порожній?`: Lisp-owned механізм, D3:101 EQ до порожнього списку.
; Не перейменовувати історичний SID8 і не вводити машинних літералів.
(визначити порожній?
  (функція (значення)
    (за-умовою
      ((атом? значення) (тотожне? значення (як-є ())))
      (так ні))))


; Lisp-owned binary format descriptor for the canonical 8-bit bit syntax.
; The reader treats the following source forms as binary data until the next
; top-level source is read; decimal integers remain ordinary decimal values.
(визначити binary
  (функція (ширина)
    (список (як-є binary) ширина)))
(визначити бінарний binary)

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
(визначити список (функція аргументи аргументи))
(визначити list список)

; Exact D4:0011 DEFINE + D4:0010 LAMBDA: macro laws from lib/core4.lisp.
; D8:00001010 is ratified REPEAT, not legacy SID8 DEFMACRO.
; No widening, implicit byte alias or new macro mechanism.
; and/or are Lisp-owned short-circuit macros. A tested operand must return
; an exact D1 PredicateBit; 0 is not () and neither result is host T/NIL.
; Each COND clause below has exactly two fields: (test expression). The last
; operand is still returned as a value without being reinterpreted as a test.
(визначити та
  (make-macro
    (функція rest
  (за-умовою
    ((атом? rest) (атом? ()))
    ((атом? (решта rest)) (перше rest))
    ((атом? ())
     (список (як-є 110)
       (сполучити
         (сполучити (перше rest)
           (сполучити
             (сполучити (як-є and) (решта rest))
             (як-є ())))
         (сполучити
           (сполучити (як-є 010)
             (сполучити (як-є ()) (як-є ())))
           (сполучити
             (сполучити
               (як-є 010)
               (сполучити
                 (сполучити (як-є 111)
                   (сполучити (як-є ())
                     (сполучити (як-є ()) (як-є ()))))
                 (як-є ())))
             (як-є ()))))))))))

(визначити або
  (make-macro
    (функція rest
  (за-умовою
    ((атом? rest) (атом? (сполучити () ())))
    ((атом? (решта rest)) (перше rest))
    ((атом? ())
     (список (як-є 110)
       (сполучити
         (сполучити (перше rest)
           (сполучити
             (сполучити (як-є 010)
               (сполучити (як-є ()) (як-є ())))
             (як-є ())))
         (сполучити
           (сполучити
             (сполучити (як-є 010)
               (сполучити (як-є ()) (як-є ())))
             (сполучити
               (сполучити (як-є or) (решта rest))
               (як-є ())))
           (як-є ())))))))))

; Сумісні англійські імена не є первинними D8 визначеннями.
(визначити and та)
(визначити or або)

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
(визначити створити-символ
  (функція (префікс)
    (текст-у-символ (рядок-додати префікс (значення-у-текст (монотонний-наносекунди))))))

(визначити пара
  (функція (лівий-операнд правий-операнд)
    (сполучити лівий-операнд (сполучити правий-операнд (як-є ())))))
(визначити pair пара)

; Ratified exact selectors: D4:1000 CAAR, D4:1001 CADR,
; D4:0111 CDDR, D5:10011 CADDR, D6:100111 CADDDR.
; Selector law is compiled from domain+bit width, never from English aliases.
; D7 is text data and is NOT used for fifth (four CDR steps).

(визначити second
  (функція (значення-функції)
    (друге значення-функції)))

(визначити third
  (функція (значення-функції)
    (третє значення-функції)))

(визначити fourth
  (функція (значення-функції)
    (третє (решта значення-функції))))

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
(визначити cadddr fourth)

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
(визначити п'ятий
  (функція (значення-функції)
    (перше (решта (решта (решта (решта значення-функції)))))))
(визначити fifth п'ятий)

(визначити caar
  (функція (значення-функції)
    (перше-першого значення-функції)))

(визначити cadr second)

(визначити cddr
  (функція (значення-функції)
    (решта-решти значення-функції)))

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
(визначити довжина-до
  (функція (значення накопичувач)
    (за-умовою
      ; D4 NULL checks exactly the end of a proper list. NOT(ATOM) would
      ; terminate nonempty lists immediately and report every length as 0.
      ((порожній? значення) накопичувач)
      ; Only a cons cell advances the accumulator. An improper nonempty
      ; tail is not silently counted as an empty list.
      ; D5 PLUS accepts qualified D24 values, never an unqualified 1.
      ((хибне? (атом? значення))
       (довжина-до (решта значення)
         (додати накопичувач 1))))))
(визначити length-onto довжина-до)


(визначити довжина
  (функція (значення)
    (довжина-до значення 0)))
(визначити length довжина)

; D5:10101 REVERSE-ONTO: canonical ratified surface owns the exact-domain
; binding. The historical English spelling below is compatibility-only.
; D1-controlled reverse: empty ends the fold; a pair advances it.
; Structural (0) and historical truth coercion are not valid D3 predicates.
(визначити зворот-до
  (функція (значення-функції накопичувач-функції)
    (за-умовою
      ((порожній? значення-функції) накопичувач-функції)
      ((хибне? (атом? значення-функції))
       (зворот-до (решта значення-функції) (сполучити (перше значення-функції) накопичувач-функції))))))

; Internal derived closure for D6:000000 LENGTH when no admitted D6
; evaluator mechanism exists. This is a Lisp binding, not D6 dispatch.
(визначити внутрішня-довжина довжина)

(визначити reverse-onto зворот-до)

(визначити зворот
  (функція (значення-функції)
    (зворот-до значення-функції (як-є ()))))
(визначити reverse зворот)

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
(визначити append
  (функція (лівий-операнд правий-операнд)
    (зворот-до (зворот лівий-операнд) правий-операнд)))

; MAP is derived in Lisp: D4 NULL detects exactly the empty list,
; while D3 ATOM excludes improper non-pair tails. Both produce D1 control
; bits; structural (0) / equal? must never act as a COND predicate.
(визначити відобразити-до
  (функція (дія значення накопичувач)
    (за-умовою
      ((порожній? значення) (зворот накопичувач))
      ((хибне? (атом? значення))
       (відобразити-до дія (решта значення) (сполучити (дія (перше значення)) накопичувач))))))
(визначити map-onto відобразити-до)

(визначити map
  (функція (дія значення)
    (відобразити-до дія значення (як-є ()))))

(визначити відсіяти-до
  (функція (перевірка значення накопичувач)
    (за-умовою
      ((хибне? (атом? значення)) (зворот накопичувач))
      ((атом? значення)  (зворот накопичувач))
      ((атом? значення) 
       (нехай ((рішення (перевірка (перше значення))))
         (за-умовою
           (рішення
            (відсіяти-до перевірка (решта значення) (сполучити (перше значення) накопичувач)))
           ((атом? перевірка)
            (відсіяти-до перевірка (решта значення) накопичувач))))))))
(визначити filter-onto відсіяти-до)

(визначити відсіяти
  (функція (перевірка значення)
    (відсіяти-до перевірка значення (як-є ()))))
(визначити filter відсіяти)

; REDUCE: D4:0101 NULL terminates only the empty list.
; Previous NOT(ATOM(values)) returned acc on nonempty pairs and CAR'd NIL.
; For any improper nonempty atom the ordinary D3 CAR rejects the data.
(визначити згорнути
  (функція (дія накопичувач значення)
    (за-умовою
      ((порожній? значення) накопичувач)
      (так
       (згорнути дія (дія накопичувач (перше значення)) (решта значення))))))
(визначити reduce згорнути)

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
(визначити внутрішнє-відображення map)
; ЛІХТАР: a bounded macro bridge for legacy Lisp source modules.
; A ratified D6 LET identity without an admitted evaluator mechanism is NOT
; silently callable. This macro expands a surface call into a fresh lambda
; application through the already proved Lisp-owned LET macro. The binding
; list and body are syntax, not values or fabricated D6 residents.
; (нехай-похідне ((x 7) (y 9)) (00100111 x y)) => (let ((x 7) (y 9)) ...).
; Legacy DEFMACRO is a projection: D4 DEFINE + make-macro + D4 LAMBDA.
(визначити нехай-похідне
  (make-macro
    (функція (привязки-функції тіло-розгортання)
  (сполучити (як-є let)
    (сполучити привязки-функції (сполучити тіло-розгортання (як-є ())))))))

(визначити let
  (make-macro
    (функція (привязки-функції тіло-розгортання)
  (сполучити (список (як-є 0010) (внутрішнє-відображення (функція (привязка-імені) (перше привязка-імені)) привязки-функції) тіло-розгортання)
        (внутрішнє-відображення (функція (привязка-імені) (друге привязка-імені)) привязки-функції)))))

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
; Returns exact PredicateBit D1 `так` or `ні`, never a quoted list.
; Canonical three-part `cond` consumes the answer explicitly; a two-part
; clause selects only on a «yes» answer.
(визначити equal?
  (функція (лівий правий)
    (за-умовою
      ((порожній? лівий) (порожній? правий))
      ((порожній? правий) ні)
      ((атом? лівий)
       (за-умовою
         ((атом? правий) (тотожне? лівий правий))
         (так ні)))
      ((атом? правий) ні)
      ((однакові? (перше лівий) (перше правий))
       (однакові? (решта лівий) (решта правий)))
      (так ні))))

; D8:11110111 ratified укр surface; mechanism is the existing Lisp-owned equal?.
; Guard's standalone core bootstrap must bind it without loading all of core4.
; D8-поверхня «однакові?» повертає точний D1 результат, не список (так)/(ні).
; Закон реалізовано мовою SENS через ратифіковані структурні операції.
(визначити однакові?
  (функція (ліве праве)
    (за-умовою
      ((порожній? ліве) (порожній? праве))
      ((порожній? праве) ні)
      ((атом? ліве)
       (за-умовою
         ((атом? праве) (тотожне? ліве праве))
         (так ні)))
      ((атом? праве) ні)
      ((однакові? (перше ліве) (перше праве))
       (однакові? (решта ліве) (решта праве)))
      (так ні))))

; Exact-Q uses 1 for YES and 0 for NO.  Structural and identity relations
; retain their own result domains, so predicate consumers normalize them here.
(визначити truthy?
  (функція (значення-виклику)
    (за-умовою
      
      ((атом? значення-виклику) 
       (за-умовою
         ((тотожне? значення-виклику 0)  (як-є ()))
         ((хибне? (тотожне? значення-виклику 0)) t)))
      ((атом? значення-виклику) 
       (за-умовою
         ((однакові? значення-виклику (як-є (ні)))  (як-є ()))
         ((однакові? значення-виклику (як-є (ні)))  (як-є ()))
         ((однакові? значення-виклику (як-є (ні)))  (як-є ()))
         ((атом? ())  t))))))

(визначити not?
  (функція (значення-виклику)
    (за-умовою
      ((truthy? значення-виклику)  (як-є ()))
      ((хибне? (truthy? значення-виклику)) t))))


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
(визначити елемент-списку-за-індексом
  (функція (індекс список-значень)
    (за-умовою
      ((тотожне? індекс 0)  (перше список-значень))
      ((тотожне? індекс 0) 
       (елемент-списку-за-індексом (відняти індекс 1) (решта список-значень))))))
(визначити nth елемент-списку-за-індексом)

(визначити значення-у-списку?
  (функція (елемент-списку lst)
    (за-умовою
      
      ((атом? lst) 
       (за-умовою
         ((однакові? елемент-списку (перше lst))  t)
         ((хибне? (однакові? елемент-списку (перше lst)))
          (значення-у-списку? елемент-списку (решта lst))))))))
(визначити member? значення-у-списку?)

; ASSOC: D4 NULL recognizes only the empty association list.
; Unlike D3 ATOM, it must not silently accept an improper atom tail.
; Only a nonempty pair may supply the first association and recursive CDR.
(визначити знайти-за-ключем
  (функція (ключ-елемента список-пар)
    (за-умовою
      ((порожній? список-пар) (як-є ()))
      (так
       (за-умовою
         ((однакові? ключ-елемента (перше (перше список-пар))) (перше список-пар))
         ((хибне? (однакові? ключ-елемента (перше (перше список-пар))))
          (знайти-за-ключем ключ-елемента (решта список-пар))))))))
(визначити assoc знайти-за-ключем)


; D5:11110 PAIRLIS: Lisp-owned structural law. Canonical Ukrainian surface
; owns the exact-domain binding; English spelling is compatibility-only.
(визначити спарувати
  (функція (ключі-списку значення-функції хвіст-форм)
    (за-умовою
      ((хибне? (атом? ключі-списку)) хвіст-форм)
      ((атом? ключі-списку) 
       (сполучити
         (сполучити (перше ключі-списку) (перше значення-функції))
         (спарувати (решта ключі-списку) (решта значення-функції) хвіст-форм))))))

(визначити pairlis спарувати)

(визначити let*
  (make-macro
    (функція (привязки-функції тіло-розгортання)
  (за-умовою
    ((атом? привязки-функції) тіло-розгортання)
    ((атом? (як-є ()))
     ; Expand directly to ((lambda (name) (let* tail body)) value).
     ; This avoids the unadmitted D6:001000 LET execution path while
     ; retaining the language-owned sequential-binding law.
     (сполучити
       (сполучити (як-є 0010)
         (сполучити
           (сполучити (перше (перше привязки-функції)) (як-є ()))
           (сполучити
             (сполучити (як-є let*)
               (сполучити (решта привязки-функції)
                 (сполучити тіло-розгортання (як-є ()))))
             (як-є ()))))
       (сполучити (друге (перше привязки-функції)) (як-є ()))))))))

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
(визначити string-membership-helper
  (функція (значення-виклику)
    (за-умовою
      ((хибне? (атом? значення-виклику))
       (як-є (class-membership string nonmember)))
      ((атом? значення-виклику) 
       (за-умовою
         ((тотожне? (рядок-перший (значення-у-текст значення-виклику))
              (рядок-перший (значення-у-текст "")))
          
          (як-є (class-membership string member)))
         ((тотожне? (рядок-перший (значення-у-текст значення-виклику))
              (рядок-перший (значення-у-текст "")))
          
          (як-є (class-membership string nonmember)))))
      ((атом? значення-виклику) 
       (як-є (class-membership string nonmember))))))

(визначити string-order-helper
  (функція (лівий-операнд правий-операнд)
    (за-умовою
      ((рядок-порожній? лівий-операнд) 
       (за-умовою
         ((рядок-порожній? правий-операнд) 
          (як-є (text-order same)))
         ((хибне? (рядок-порожній? правий-операнд))
          (як-є (text-order before)))))
      ((хибне? (рядок-порожній? лівий-операнд))
       (як-є (text-order after)))
      ((тотожне? (рядок-перший лівий-операнд) (рядок-перший правий-операнд))
       
       (string-order-helper (рядок-решта лівий-операнд) (рядок-решта правий-операнд)))
      ((менше? (код-символу (рядок-перший лівий-операнд))
          (код-символу (рядок-перший правий-операнд)))
       
       (як-є (text-order before)))
      ((хибне? (менше? (код-символу (рядок-перший лівий-операнд)) (код-символу (рядок-перший правий-операнд))))
       (як-є (text-order after))))))

(визначити nonempty-string-membership-helper
  (функція (значення-виклику)
    (за-умовою
      ((string-membership-helper значення-виклику)
       
       (за-умовою
         ((хибне? (рядок-порожній? значення-виклику))
          (як-є (class-membership string nonempty-member)))
         ((рядок-порожній? значення-виклику)
          
          (як-є (class-membership string member)))))
      ((string-membership-helper значення-виклику)
       
       (як-є (class-membership string nonmember))))))

; string<? — лексикографічний порядок за кодовими точками, як `<` для &str
; у Rust (UTF-8 зберігає порядок кодових точок). Переведено з Rust у мову
; (власник, 2026-09-26): рядок розбирають лише примітиви string-first
; (00111111), string-rest (01000000) і string->codepoint (01000101). Не-рядок
; дає природну помилку Type від string-first; неправильна кількість
; аргументів — Arity від прив'язки лямбди.
(визначити string<?
  (функція (a b)
    (за-умовою
      ; Порожній бік: інший перевіряється як рядок (string-append дає Type).
      ((рядок-порожній? b) 
       (друге (список (рядок-додати a "") (як-є ()))))
      ((рядок-порожній? a) 
       (друге (список (рядок-додати b "") t)))
      ((менше? (код-символу (рядок-перший a)) (код-символу (рядок-перший b)))  t)
      ((тотожне? (рядок-перший a) (рядок-перший b)) 
       (текст-передує? (рядок-решта a) (рядок-решта b)))
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
(визначити символ?
  (функція (значення-виклику)
    (за-умовою
      ((атом? значення-виклику)
       (за-умовою
         ((тотожне? значення-виклику (текст-у-символ (значення-у-текст значення-виклику)))
          (атом? (як-є ())))
         ((атом? ()) ні)))
      ((атом? ()) ні))))
(визначити symbol? символ?)


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
(визначити largest-chunk
  (функція (a b частина-числа mult)
    (за-умовою
      ((менше? a (додати частина-числа частина-числа))  (сполучити частина-числа mult))
      ((хибне? (менше? a (додати частина-числа частина-числа)))
       (largest-chunk a b (додати частина-числа частина-числа) (додати mult mult))))))

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
(визначити частка
  (функція (ділене дільник)
    (за-умовою
      ((тотожне? дільник 0)  (поділити ділене дільник))
      ((атом? (як-є ())) 
       (за-умовою
         ((менше? ділене дільник)  0)
         ((хибне? (менше? ділене дільник))
          (нехай ((chunk+mult (largest-chunk ділене дільник дільник 1)))
            (додати (решта chunk+mult)
               (частка (відняти ділене (перше chunk+mult)) дільник)))))))))
(визначити quotient частка)

; The remainder uses the same Lisp-owned integer quotient: a - b * floor(a / b).
(визначити модульна-остача
  (функція (ділене дільник)
    (відняти ділене (помножити дільник (частка ділене дільник)))))
(визначити mod модульна-остача)

; `<=` and `>=` stay Lisp-derived, but #216 now requires the derived
; operators to preserve the same exact-Q answer algebra as `<`, `>` and `=`:
; exact YES -> 1/1, exact NO -> 0/1, and any inexact operand -> Canon 0 `()`.
; Canonical three-part `cond` distinguishes exact NO (0) from no-answer `()`
; without routing either through generic truthiness.
(визначити nondecreasing-from?
  (функція (поточна-форма залишені-форми)
    (за-умовою
      ((хибне? (атом? залишені-форми)) 1)
      ((менше? поточна-форма (перше залишені-форми)) 
       (nondecreasing-from? (перше залишені-форми) (решта залишені-форми)))
      ((однакові? поточна-форма (перше залишені-форми)) 
       (nondecreasing-from? (перше залишені-форми) (решта залишені-форми)))
      ((хибне? (однакові? поточна-форма (перше залишені-форми))) 0))))

(визначити nonincreasing-from?
  (функція (поточна-форма залишені-форми)
    (за-умовою
      ((хибне? (атом? залишені-форми)) 1)
      ((більше? поточна-форма (перше залишені-форми)) 
       (nonincreasing-from? (перше залишені-форми) (решта залишені-форми)))
      ((однакові? поточна-форма (перше залишені-форми)) 
       (nonincreasing-from? (перше залишені-форми) (решта залишені-форми)))
      ((хибне? (однакові? поточна-форма (перше залишені-форми))) 0))))

(визначити <=
  (функція (перший-аргумент . решта-аргументів)
    (nondecreasing-from? перший-аргумент решта-аргументів)))

(визначити >=
  (функція (перший-аргумент . решта-аргументів)
    (nonincreasing-from? перший-аргумент решта-аргументів)))

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
(визначити digit->string
  ; Superseded by number->string's canonical delegation to write-to-string
  ; (FIX-NUMBER-TO-STRING-RATIONAL). Retained because racket/boot/core.lisp
  ; mirrors this file and fpga-lisp's assembler.lisp carries its own local
  ; variant — removal is a separate mirrored-surface decision, not a
  ; silent one.
  (функція (d)
    (елемент-списку-за-індексом d (як-є ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9")))))

(визначити number->string-onto
  (функція (n накопичувач-функції)
    (за-умовою
      ((тотожне? n 0)  накопичувач-функції)
      ((тотожне? n 0) 
       (number->string-onto
         (частка n 10)
         (рядок-додати (відобразити-доки-істина (модульна-остача n 10)) накопичувач-функції))))))

(визначити число-рядок
  (функція (n)
    ; Canonical serialization for every number (FIX-NUMBER-TO-STRING-
    ; RATIONAL, docs/BUG-number-to-string-rational.md): integers render
    ; as themselves, non-integer rationals render REDUCED exactly —
    ; "1/3", never a decimal approximation, per the same G6 law that
    ; makes 10/20 serialize as "1/2". The previous quotient/mod descent
    ; crashed on fractional digit indices ((nth 1/3 <digit-table>)) and
    ; its misleading error surfaced as an apparent memory corruption.
    ; Delegation, not re-implementation: write-to-string is already the
    ; contract-tested renderer (G6 fixtures), so this cannot drift from it.
    (значення-у-текст n)))

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
(визначити ->
  (make-macro
    (функція форми-розгортання
  (за-умовою
    
    ((атом? форми-розгортання) 
     (за-умовою
       ((хибне? (атом? (решта форми-розгортання))) (перше форми-розгортання))
       ((атом? (решта форми-розгортання)) 
        (нехай-послідовно ((x (перше форми-розгортання))
               (next (перше (решта форми-розгортання)))
               (rest (решта (решта форми-розгортання)))
               (step
                 (за-умовою
                   ((хибне? (атом? next)) (список next x))
                   ((атом? next)  (список next x))
                   ((атом? next) 
                    (сполучити (перше next) (сполучити x (решта next)))))))
          (за-умовою
            ((хибне? (атом? rest)) step)
            ((атом? rest) 
             (сполучити (як-є ->) (сполучити step rest))))))))))))

(визначити ->>
  (make-macro
    (функція форми-розгортання
  (за-умовою
    
    ((атом? форми-розгортання) 
     (за-умовою
       ((хибне? (атом? (решта форми-розгортання))) (перше форми-розгортання))
       ((атом? (решта форми-розгортання)) 
        (нехай-послідовно ((x (перше форми-розгортання))
               (next (перше (решта форми-розгортання)))
               (rest (решта (решта форми-розгортання)))
               (step
                 (за-умовою
                   ((хибне? (атом? next)) (список next x))
                   ((атом? next)  (список next x))
                   ((атом? next) 
                    (приєднати next (список x))))))
          (за-умовою
            ((хибне? (атом? rest)) step)
            ((атом? rest) 
             (сполучити (як-є ->>) (сполучити step rest))))))))))))

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

(визначити sqrt-iter
  (функція (наближення x n)
    (за-умовою
      ((однакові? n 0)  наближення)
      ((хибне? (однакові? n 0))
       (sqrt-iter (поділити (додати наближення (поділити x наближення)) 2) x (відняти n 1))))))

;; integer sqrt: Newton on quotients — provably terminating
(визначити цілий-корінь
  (функція (n)
    (за-умовою
      ((менше? n 2)  n)
      ((хибне? (менше? n 2))
       (isqrt-step n (частка n 2))))))

(визначити isqrt-step
  (функція (n g)
    (нехай ((next (частка (додати g (частка n g)) 2)))
      (за-умовою
        ((менше? next g)  (isqrt-step n next))
        ((хибне? (менше? next g)) g)))))

(визначити корінь
  (функція (x)
    (за-умовою
      ((менше? x 0)  (як-є ()))
      ((однакові? x 0)  0)
      ((однакові? x (частка x 1)) 
       (нехай ((r (цілий-корінь x)))
         (за-умовою
           ((однакові? (помножити r r) x)  r)
           ((атом? ())  (sqrt-iter (поділити x 2) x 8)))))
      ((атом? ())  (sqrt-iter (поділити x 2.0) x 5)))))

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
(визначити модуль
  (функція (x)
    (за-умовою
      ((менше? x 0)  (відняти 0 x))
      ((хибне? (менше? x 0)) x))))
(визначити abs модуль)

; Required first parameter (dotted lambda-list, same pattern as
; `<=`/`>=` above) keeps zero arguments an Arity error via the
; evaluator's own lambda-binding check -- matching the removed Rust
; builtin's explicit "min/max expects at least one argument" error --
; without this Lisp definition needing to raise a custom error itself.
(визначити найменше
  (функція (перший-аргумент . решта-аргументів)
    (найменше-у-списку (сполучити перший-аргумент решта-аргументів))))
(визначити min найменше)

(визначити найбільше
  (функція (перший-аргумент . решта-аргументів)
    (найбільше-у-списку (сполучити перший-аргумент решта-аргументів))))
(визначити max найбільше)

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
(визначити найменше-у-списку
  (функція (елементи-списку)
    (за-умовою
      
      ((атом? елементи-списку) 
       (нехай ((rest-min (найменше-у-списку (решта елементи-списку))))
         (за-умовою
           ((порожній? rest-min) 
            (перше елементи-списку))
           ((хибне? (порожній? rest-min))
            (за-умовою
              ((менше? (перше елементи-списку) rest-min)  (перше елементи-списку))
              ((хибне? (менше? (перше елементи-списку) rest-min)) rest-min)))))))))
(визначити min-list найменше-у-списку)

(визначити найбільше-у-списку
  (функція (елементи-списку)
    (за-умовою
      
      ((атом? елементи-списку) 
       (нехай ((rest-max (найбільше-у-списку (решта елементи-списку))))
         (за-умовою
           ((порожній? rest-max) 
            (перше елементи-списку))
           ((хибне? (порожній? rest-max))
            (за-умовою
              ((більше? (перше елементи-списку) rest-max)  (перше елементи-списку))
              ((хибне? (більше? (перше елементи-списку) rest-max)) rest-max)))))))))
(визначити max-list найбільше-у-списку)

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
(визначити my-postcore-stable-peer-projection
  (як-є (
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

(визначити my-postcore-peer-group
  (функція (semantic-id групи-визначень)
    (за-умовою
      
      ((атом? групи-визначень) 
       (нехай ((група-відповідників (перше групи-визначень)))
         (за-умовою
           ((тотожне? semantic-id (перше група-відповідників)) 
            група-відповідників)
           ((тотожне? semantic-id (перше група-відповідників)) 
            (my-postcore-peer-group semantic-id (решта групи-визначень)))))))))

(визначити my-postcore-binding-status
  (функція (поверхня-виклику привязки-функції)
    (за-умовою
      ((хибне? (атом? привязки-функції))
       (як-є absent))
      ((атом? привязки-функції) 
       (нехай ((привязка-імені (перше привязки-функції)))
         (за-умовою
           ((тотожне? (символ-у-текст поверхня-виклику) (перше привязка-імені)) 
            (як-є present))
           ((тотожне? (символ-у-текст поверхня-виклику) (перше привязка-імені)) 
            (my-postcore-binding-status поверхня-виклику (решта привязки-функції)))))))))

(визначити my-postcore-missing-peers
  (функція (джерело-проєкції поверхневі-відповідники привязки-функції)
    (за-умовою
      
      ((атом? поверхневі-відповідники) 
       (нехай ((peer (перше поверхневі-відповідники)))
         (за-умовою
           ((тотожне? джерело-проєкції peer) 
            (my-postcore-missing-peers джерело-проєкції (решта поверхневі-відповідники) привязки-функції))
           ((тотожне? джерело-проєкції peer) 
            (за-умовою
              ((тотожне? (my-postcore-binding-status peer привязки-функції) (як-є present))
               
               (my-postcore-missing-peers джерело-проєкції (решта поверхневі-відповідники) привязки-функції))
              ((тотожне? (my-postcore-binding-status peer привязки-функції) (як-є absent))
               
               (сполучити peer
                     (my-postcore-missing-peers
                       джерело-проєкції
                       (решта поверхневі-відповідники)
                       привязки-функції)))))))))))

; Build one expression whose nested DEFINE forms all execute in the caller's
; environment. This is why materialization is a macro rather than a function:
; an ordinary function would define peers only in its temporary child frame.
(визначити my-postcore-build-definitions
  (функція (джерело-проєкції поверхневі-відповідники)
    (за-умовою
      ((хибне? (атом? поверхневі-відповідники))
       джерело-проєкції)
      ((атом? поверхневі-відповідники) 
       (список (як-є define)
             (перше поверхневі-відповідники)
             (my-postcore-build-definitions джерело-проєкції (решта поверхневі-відповідники)))))))

(визначити my-postcore-materialize-stable-peers
  (make-macro
    (функція args
  (нехай-послідовно ((semantic-id (перше args))
         (джерело-проєкції (друге args))
         (група-відповідників
           (my-postcore-peer-group
             semantic-id
             my-postcore-stable-peer-projection)))
    (за-умовою
      ((хибне? (атом? група-відповідників))
       джерело-проєкції)
      ((атом? група-відповідників) 
       (my-postcore-build-definitions
         джерело-проєкції
         (my-postcore-missing-peers джерело-проєкції (решта група-відповідників) (відобразити-середовище)))))))))

; Ділення з остачою (Lisp 1.5 DIVIDE): повертає список (частка остача).
(визначити divmod
  (функція (ділене-значення дільник-значення)
    (список (частка ділене-значення дільник-значення) (модульна-остача ділене-значення дільник-значення))))

; McCarthy 1960, §3d: null, subst, sublis, maplist, apply — закон Core4, коди СЕНС.
(визначити null?
  (функція (x)
    (за-умовою
      ((хибне? (атом? x)) t)
      ((атом? x)  (як-є ()))
      ((атом? x)  (як-є ())))))

(визначити subst
  (функція (x y z)
    (за-умовою
      ((атом? z) 
       (сполучити (замінити x y (перше z)) (замінити x y (решта z))))
      ((хибне? (атом? z))
       (за-умовою
         ((тотожне? z y)  x)
         ((хибне? (тотожне? z y)) z)))
      ((атом? z) 
       (за-умовою
         ((тотожне? z y)  x)
         ((хибне? (тотожне? z y)) z))))))

(визначити sublis-pair
  (функція (x z)
    (за-умовою
      ((хибне? (атом? x)) z)
      ((атом? x) 
       (за-умовою
         ((тотожне? (перше (перше x)) z) 
          (перше (решта (перше x))))
         ((тотожне? (перше (перше x)) z) 
          (sublis-pair (решта x) z)))))))

(визначити sublis
  (функція (x y)
    (за-умовою
      ((атом? y) 
       (сполучити (підставити-пари x (перше y)) (підставити-пари x (решта y))))
      ((хибне? (атом? y)) (sublis-pair x y))
      ((атом? y)  (sublis-pair x y)))))

(визначити maplist
  (функція (x f)
    (за-умовою
      
      ((атом? x) 
       (сполучити (f x) (відобразити-залишки (решта x) f))))))

(визначити apply-quote-args
  (функція (m)
    (за-умовою
      
      ((атом? m) 
       (сполучити (сполучити (як-є 001) (сполучити (перше m) (як-є ())))
                 (apply-quote-args (решта m)))))))

(визначити apply
  (функція (f args)
    (обчислити (сполучити f (apply-quote-args args)))))

; #1391: логіка відповідей Core4 — закон contracts/core4-predicate-answer-scale.lisp /3.
; Відповідь — список двійкових бітів: (1)…(1 1 1 1 1 1 1) «так»,
; (0)…(0 0 0 0 0 0 0) «ні», () «невідомо». Лінія істинності:
;   0 < 00 < … < 0000000 < () < 1111111 < … < 11 < 1
; Виконуваний свідок законів — experiments/core4-logic15-algebra.lisp.

; NOT: інвертувати кожен біт, ширина та сама; () лишається ().
(визначити відповідь-не
  (функція (a)
    (за-умовою
      
      ((атом? a) 
       (сполучити
         (за-умовою
           ((тотожне? (перше a) 0)  1)
           ((хибне? (тотожне? (перше a) 0)) 0))
         (відповідь-не (решта a)))))))

; AND: мінімум на лінії. «Ні» перемагає; з двох «ні» — коротше (сильніше);
; з двох «так» — довше (слабше); () поглинає «так».
; Для двох відповідей одного напряму крок іде по обох списках разом.
(визначити відповідь-і
  (функція (a b)
    (за-умовою
      ((хибне? (атом? a))
       (за-умовою
         
         ((атом? b) 
          (за-умовою
            ((тотожне? (перше b) 0)  b)
            ((тотожне? (перше b) 0)  (як-є ()))))))
      ((атом? a) 
       (за-умовою
         ((хибне? (атом? b))
          (за-умовою
            ((тотожне? (перше a) 0)  a)
            ((тотожне? (перше a) 0)  (як-є ()))))
         ((атом? b) 
          (за-умовою
            ((тотожне? (перше a) (перше b)) 
             (за-умовою
               ((тотожне? (перше a) 0)  a)
               ((хибне? (тотожне? (перше a) 0)) b)))
            ((тотожне? (перше a) (перше b)) 
             (за-умовою
               ((хибне? (атом? (решта a)))
                (за-умовою
                  ((тотожне? (перше a) 0)  a)
                  ((хибне? (тотожне? (перше a) 0)) b)))
               ((хибне? (атом? (решта b)))
                (за-умовою
                  ((тотожне? (перше b) 0)  b)
                  ((хибне? (тотожне? (перше b) 0)) a)))
               ((атом? (решта b)) 
                (сполучити (перше a)
                          (відповідь-і (решта a) (решта b)))))))))))))

; OR: максимум на лінії = NOT(AND(NOT a, NOT b)).
(визначити відповідь-або
  (функція (a b)
    (відповідь-не (відповідь-і (відповідь-не a) (відповідь-не b)))))

; Послаблення: дописати той самий біт; восьмий біт належить 256 функціям,
; тож із семи бітів шкала сходиться в ().
(визначити відповідь-послабити
  (функція (a)
    (за-умовою
      
      ((атом? a) 
       (за-умовою
         ((тотожне? (довжина a) 7)  (як-є ()))
         ((тотожне? (довжина a) 7) 
          (сполучити (перше a) a)))))))

; atom? відповіддю шкали: атом (1), пара (0), () — невідомо, бо () стоїть
; вище розрізнення атом/пара.
(визначити відповідь-атом
  (функція (x)
    (за-умовою
      ((атом? x)  (як-є (так)))
      ((атом? x)  (як-є (ні)))
      )))

; eq? відповіддю шкали: same (1), distinct (0). Область та сама, що в eq?: атоми.
(визначити відповідь-рівність
  (функція (a b)
    (за-умовою
      ((тотожне? a b)  (як-є (так)))
      ((тотожне? a b)  (як-є (ні))))))

; Зворотні сумісні англійські імена; основні DEFINE вже ратифікованою укр.

; Історичні англійські виклики зберігають ті самі Lisp-значення.
(визначити answer-not відповідь-не)
(визначити answer-and відповідь-і)
(визначити answer-or відповідь-або)
(визначити answer-weaken відповідь-послабити)
(визначити answer-atom відповідь-атом)
(визначити answer-eq відповідь-рівність)

; Історичні зовнішні імена збережено тільки як посилання на ті самі D8/D9 Lisp-значення.
(визначити identity тотожність)
(визначити gensym створити-символ)
(визначити number->string число-рядок)
(визначити isqrt цілий-корінь)
(визначити sqrt корінь)
