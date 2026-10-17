
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

; Канонічні D8:01100000..01100111 aliases до вже визначених точних D3 CAR/CDR композицій.
(0011 решта-від-перше-від-перше-від-перше-від-перше-від-перше р-п-п-п-п-п)
(0011 cdaaaaar р-п-п-п-п-п)
(0011 решта-від-перше-від-перше-від-перше-від-перше-від-решта р-п-п-п-п-р)
(0011 cdaaaadr р-п-п-п-п-р)
(0011 решта-від-перше-від-перше-від-перше-від-решта-від-перше р-п-п-п-р-п)
(0011 cdaaadar р-п-п-п-р-п)
(0011 решта-від-перше-від-перше-від-перше-від-решта-від-решта р-п-п-п-р-р)
(0011 cdaaaddr р-п-п-п-р-р)
(0011 решта-від-перше-від-перше-від-решта-від-перше-від-перше р-п-п-р-п-п)
(0011 cdaadaar р-п-п-р-п-п)
(0011 решта-від-перше-від-перше-від-решта-від-перше-від-решта р-п-п-р-п-р)
(0011 cdaadadr р-п-п-р-п-р)
(0011 решта-від-перше-від-перше-від-решта-від-решта-від-перше р-п-п-р-р-п)
(0011 cdaaddar р-п-п-р-р-п)
(0011 решта-від-перше-від-перше-від-решта-від-решта-від-решта р-п-п-р-р-р)
(0011 cdaadddr р-п-п-р-р-р)

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

; Канонічні D5:01100..01111/10000..10011 aliases до наявних D3 CAR/CDR композицій.
(0011 решта-п-п р-п-п)
(0011 решта-двох-перших р-п-п)
(0011 cdaar р-п-п)
(0011 решта-п-р р-п-р)
(0011 решта-після-першого р-п-р)
(0011 cdadr р-п-р)
(0011 решта-р-п р-р-п)
(0011 решта-решти-першого р-р-п)
(0011 cddar р-р-п)
(0011 решта-р-р р-р-р)
(0011 решта-трьох р-р-р)
(0011 cdddr р-р-р)
(0011 перше-п-п п-п-п)
(0011 перше-двох-перших п-п-п)
(0011 caaar п-п-п)
(0011 перше-п-р п-п-р)
(0011 перше-після-першого п-п-р)
(0011 caadr п-п-р)
(0011 перше-р-п п-р-п)
(0011 перше-решти-першого п-р-п)
(0011 cadar п-р-п)
(0011 третє п-р-р)
(0011 caddr п-р-р)

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

; Порядкові доступи належать канонічним D3–D6, а не Core4 DEFINE.
; D3:100 перше/CAR, D4:1001 друге/CADR, D5:10011 третє/CADDR,
; D6:100111 четверте/CADDDR. Не затінювати незмінні бітові ідентичності.

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
; D5 ZEROP: явна числова D24+ операція та D3-еквівалентність;
; не викликати історичні двійкові координати як Lisp-числа.
(0011 нуль?
  (0010 (значення)
    (тотожне? значення (відняти значення значення))))
; Та сама closure для явно типізованого зовнішнього написання тесту.
(0011 нуль-д24?
  (0010 (значення)
    (101 значення (01010 значення значення))))



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

; D10 research / PAIP list family: owner codebook coordinates, not F1-F4
; machine admission. Each definition is native SENS over already-ratified
; D3 CONS/CAR/CDR, D4 NULL/COND and D5 APPEND. Archive:
; knowledge/d10-crossrepo-paip-v1.json and lib/domains/d10.lisp.
; D10:0011010111 MKLIST: () remains (); an atom becomes a singleton;
; an existing nonempty list is returned unchanged.
(0011 утворити-список
  (0010 (значення)
    (110
      ((0101 значення) (001 ()))
      ((010 значення) (111 значення (001 ())))
      (#d1:1 значення))))

; D10:0011001010 MAPPEND: concatenate callback-produced proper lists
; in original input order. No destructive append or implicit coercions.
(0011 відобразити-й-додати
  (0010 (дія елементи)
    (110
      ((0101 елементи) (001 ()))
      ((010 елементи) (100 (001 ())))
      (#d1:1
       (append (дія (100 елементи))
               (відобразити-й-додати дія (011 елементи)))))))

; D10:0011001110 FLATTEN: PAIP donor specifies exactly ONE level,
; not an arbitrary recursive tree flatten.
(0011 сплющити
  (0010 (елементи)
    (відобразити-й-додати
      (0010 (елемент) (утворити-список елемент))
      елементи)))

; D10 PAIP/MAL follow-on, language-derived only (no D10 F1-F4 admission).
; D10:0011001101 LAST1: CAR(last cons) for a nonempty proper list,
; not the final cons cell. Donor knowledge/d10-crossrepo-paip-v1.json.
(0011 останній
  (0010 (елементи)
    (100 (останній-хвіст елементи))))

; D10:0100001100 LISTP: both NIL and any CONS cell are list-shaped;
; distinct from PROPER-LIST? and from D3:010 ATOM.
; Donor knowledge/d10-crossrepo-mal-v1.json.
(0011 список?
  (0010 (значення)
    (110
      ((0101 значення) #d1:1)
      ((010 значення) #d1:0)
      (#d1:1 #d1:1))))


; D10 PAIP FIND-IF-ANYWHERE: derive a tree search from the pinned PAIP law.
; PAIP checks ATOM first and applies the predicate to every atom, including ().
; Traversal is left-to-right; a successful CAR search short-circuits the CDR.
; The D10 codebook row remains research-only: this is not direct D10 callability.
(0011 дерево-має-збіг?
  (0010 (предикат дерево)
    (110
      ((010 дерево)
       (110
         ((предикат дерево) #d1:1)
         (#d1:1 #d1:0)))
      ((дерево-має-збіг? предикат (100 дерево)) #d1:1)
      (#d1:1 (дерево-має-збіг? предикат (011 дерево))))))
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
      (001 0010)
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
      ((0101 a) (0101 b))
      ((0101 b) #d1:0)
      ((010 a)
       (110
         ((010 b) (101 a b))
         (#d1:1 #d1:0)))
      ((010 b) #d1:0)
      ((equal? (100 a) (100 b))
       (equal? (011 a) (011 b)))
      (#d1:1 #d1:0))))

; D8:11110111 EQUAL — ratified Ukrainian surface for SENS-owned structural equality.
; The identity is already admitted; this is a name projection, not a new opcode.
(0011 однакові? equal?)

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

; Lifted verbatim from research/d9-map-vec-list-batch-2026-10-17.lisp — ratified D9 identity, SENS-owned alist semantics.
; D9:101100011 MAP-EMPTY
(0011 мапа-порожній
  (0010 () (quote ())))
(0011 map-empty мапа-порожній)

; D9:101100101 MAP-GET — value of assoc pair (cdr)
(0011 мапа-отримати
  (0010 (ключ мапа)
    (110
      ((0101 (знайти-за-ключем ключ мапа)) (quote ()))
      ((0100 (0101 (знайти-за-ключем ключ мапа)))
       (011 (знайти-за-ключем ключ мапа))))))
(0011 map-get мапа-отримати)

; D9:101100010 MAP-CONTAINS?
(0011 мапа-містить?
  (0010 (ключ мапа)
    (not? (0101 (знайти-за-ключем ключ мапа)))))
(0011 map-contains? мапа-містить?)

; D9:101001100 MAP->LIST — alist already a list
(0011 мапа-список
  (0010 (мапа) мапа))
(0011 map->list мапа-список)

; Друга партія D9 — дослівний перенос із ратифікованого research/d9-map-vec-list-batch-2026-10-17.lisp.
; D9:101101101 VEC-EMPTY
(0011 вектор-порожній
  (0010 () (quote ())))
(0011 vec-empty вектор-порожній)

; D9:101010111 VEC-COUNT
(0011 вектор-кількість довжина)
(0011 vec-count вектор-кількість)

; D9:110000010 VEC-NTH
(0011 вектор-n-тий елемент-списку)
(0011 vec-nth вектор-n-тий)

; D9 list-alist derived functions, lifted from research/d9-map-insert-store-batch-2026-10-17.lisp.
; D9:101101110 MAP-INSERT — front pair + drop old key
(0011 мапа-вставити
  (0010 (ключ значення мапа)
    (111
      (111 ключ (111 значення (001 ())))
      (відсіяти
        (0010 (пара) (not? (equal? (100 пара) ключ)))
        мапа))))
(0011 map-insert мапа-вставити)

; D9:101011000 VEC->LIST
(0011 вектор-список
  (0010 (вектор) вектор))
(0011 vec->list вектор-список)





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

; English projections of the already-defined D6 residents; no new semantic laws.
(0011 compose скласти-функції)
(0011 flip поміняти-аргументи)

; D6:001101 — ACONS, приєднати пару ключ/значення до асоціацій.
; Лише два D3:111 CONS; без direct D6 callability.
(0011 додати-асоціацію
  (0010 (ключ значення асоціації)
    (111 (111 ключ значення) асоціації)))



; D6:001110 ADD1 / D6:001111 SUB1 — purely derived D24+ arithmetic.
; D5:01010 PLUS and D5:01011 DIFFERENCE preserve the qualified mathematical carrier.
; No implied arithmetic on D1-D10 identities, no new direct D6 call admission.
; D6:001110/001111 — точні похідні від кваліфікованої D5 арифметики.
; Визначення без залежності від порядку пізніших SENS-алиасів.
; Жодної шестибітної прямої callability чи числового посередника.
(0011 додати-1
  (0010 (значення)
    (додати значення #d24:000000000000000000000001)))
(0011 відняти-1
  (0010 (значення)
    (відняти значення #d24:000000000000000000000001)))

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

; Canonical D6 name projections for the already-defined four-step selectors.
; These are ordinary Lisp aliases to D3 CAR/CDR closures, not direct D6 opcode admission.
(0011 рппп р-п-п-п)
(0011 решта-перше-перше-перше р-п-п-п)
(0011 cdaaar р-п-п-п)
(0011 рппр р-п-п-р)
(0011 решта-перше-перше-решта р-п-п-р)
(0011 cdaadr р-п-п-р)
(0011 рпрп р-п-р-п)
(0011 решта-перше-решта-перше р-п-р-п)
(0011 cdadar р-п-р-п)
(0011 рпрр р-п-р-р)
(0011 решта-перше-решта-решта р-п-р-р)
(0011 cdaddr р-п-р-р)
(0011 ррпп р-р-п-п)
(0011 решта-решта-перше-перше р-р-п-п)
(0011 cddaar р-р-п-п)
(0011 ррпр р-р-п-р)
(0011 решта-решта-перше-решта р-р-п-р)
(0011 cddadr р-р-п-р)
(0011 рррп р-р-р-п)
(0011 решта-решта-решта-перше р-р-р-п)
(0011 cdddar р-р-р-п)
(0011 рррр р-р-р-р)
(0011 решта-чотирьох р-р-р-р)
(0011 cddddr р-р-р-р)
(0011 пппп п-п-п-п)
(0011 перше-перше-перше-перше п-п-п-п)
(0011 caaaar п-п-п-п)
(0011 пппр п-п-п-р)
(0011 перше-перше-перше-решта п-п-п-р)
(0011 caaadr п-п-п-р)
(0011 ппрп п-п-р-п)
(0011 перше-перше-решта-перше п-п-р-п)
(0011 caadar п-п-р-п)
(0011 ппрр п-п-р-р)
(0011 перше-перше-решта-решта п-п-р-р)
(0011 caaddr п-п-р-р)
(0011 прпп п-р-п-п)
(0011 перше-решта-перше-перше п-р-п-п)
(0011 cadaar п-р-п-п)
(0011 прпр п-р-п-р)
(0011 перше-решта-перше-решта п-р-п-р)
(0011 cadadr п-р-п-р)
(0011 пррп п-р-р-п)
(0011 перше-решта-решта-перше п-р-р-п)
(0011 caddar п-р-р-п)
(0011 пррр fourth)
(0011 четверте fourth)

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
      ((нуль-д24? кількість) (001 ()))
      ((0101 елементи) (001 ()))
      ((0101 (001 ()))
       (111 (100 елементи)
            (взяти (зменшити-на-один кількість) (011 елементи)))))))

(0011 відкинути
  (0010 (кількість елементи)
    (110
      ((нуль-д24? кількість) елементи)
      ((0101 елементи) (001 ()))
      ((0101 (001 ()))
       (відкинути (зменшити-на-один кількість) (011 елементи))))))

; D8:00100001 SUBSEQ — лише списки та кваліфіковані D24 межі.
; На 0 <= початок <= кінець <= LENGTH(елементи):
; SUBSEQ(xs,a,b) = D6:110000 TAKE(D5:01011 (b-a), D6:110001 DROP(a,xs)).
; Визначення власне SENS; це не прямий допуск D8:bits.
(0011 підпослідовність
  (0010 (елементи початок кінець)
    (взяти (відняти кінець початок)
           (відкинути початок елементи))))

; D8:00001010 REPEAT: похідна функція SENS, дослідження
; research/d8-repeat-elt-quotient-surface-2026-10-17.lisp.
; Кількість — невід'ємне явно кваліфіковане D24; без прямого D8 opcode.
(0011 повторити
  (0010 (кількість значення)
    (110
      ((нуль? кількість) (001 ()))
      ((0100 (нуль? кількість))
       (111 значення (повторити (зменшити-на-один кількість) значення))))))

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
    (110
      ((нуль? b) a)
      (#d1:1 (нсд b (mod a b))))))
; ===== НСД (розширення) + T5M (транспортний кодек) =====
; Власник 2026-10-17: «реалізуй T5M новими функціями + реалізуй НСД».
; Усе — похідні від наявних D3/D4/D5/D6; жодних нових координат.

; --- НСД (gcd) ---
; нсд для списку: згортка бінарного нсд (уже визначеного вище) по списку.
(0011 нсд-списку
  (0010 (числа)
    (110
      ((null? числа) #d24:000000000000000000000000)
      ((null? (решта числа)) (перше числа))
      (#d1:1 (нсд (перше числа) (нсд-списку (решта числа)))))))

; нсд трьох чисел — явна трійкова форма (зручна для свідків).
(0011 нсд-трьох
  (0010 (a b c)
    (нсд a (нсд b c))))

; --- T5M: точні слова -> трійковий транспорт ---
; 5 трітів/байт (3^5=243<256); тріт-розділювач 2; фінальний байт ДОПОВНЮЄТЬСЯ трітами 2
; (підтверджено незалежно: t5m.zig encode -> while (used!=0) appendDigit(...,2)).

(0011 тріт-розділювач #d24:000000000000000000000010)
(0011 трітів-у-байті #d24:000000000000000000000101)
(0011 трійкова-основа #d24:000000000000000000000011)

; D1 bits stay predicates at the boundary; base-3 math uses D24 trits.
(0011 т5м-д24-тріт
  (0010 (значення)
    ; Input is a D1 PredicateBit, so use it as control, never as a number.
    (110
      (значення #d24:000000000000000000000001)
      (#d1:1 #d24:000000000000000000000000))))

; Decoder exposes D1 bits again, not D24 surrogate bits.
(0011 т5м-біт-д1
  (0010 (значення)
    (110
      ((тотожне? значення #d24:000000000000000000000000) #d1:0)
      ((тотожне? значення #d24:000000000000000000000001) #d1:1)
      (#d1:1 значення))))

; накопичити: новий акумулятор = поточний*3 + тріт
(0011 т5-накопичити
  (0010 (поточний тріт)
    (додати (помножити поточний трійкова-основа) тріт)))

; біти слова (старший перший) -> список трітів (0/1 як тріти)
(0011 т5-тріти-слова
  (0010 (біти)
    (110
      ((null? біти) (001 ()))
      (#d1:1 (111 (т5м-д24-тріт (перше біти)) (т5-тріти-слова (решта біти)))))))

; згорнути список трітів у трійкове число
(0011 т5-трійкове
  (0010 (тріти)
    (т5-трійкове-з #d24:000000000000000000000000 тріти)))

; акумуляторна згортка зліва направо: перший тріт — старший
(0011 т5-трійкове-з
  (0010 (акум тріти)
    (110
      ((null? тріти) акум)
      (#d1:1 (т5-трійкове-з (т5-накопичити акум (перше тріти)) (решта тріти))))))

; доповнити список трітів до 5 значенням 2 (розділювач) — фінальний байт
(0011 т5-заповнити
  (0010 (тріти)
    (110
      ((рівно-пять? (довжина тріти)) тріти)
      (#d1:1 (т5-заповнити (111 (001 ()) (111 тріти тріт-розділювач)))))))

; один байт T5 з одного слова (<=5 трітів) — контрольований приклад
(0011 т5-байт-слова
  (0010 (біти)
    (т5-трійкове (т5-заповнити (т5-тріти-слова біти)))))

; рівно-пять? — допоміжний предикат довжини (без host-семантики)
; --- T5M: ПОВНИЙ багатобайтовий кодек ---
; Перевірено 6/6 проти scripts/sens_t5_codec.py (енкодер і декодер, round-trip).
; Правило: тріти = (розділювач 2 між словами) + біти; доповнити до кратного 5
; трітом 2 У КІНЦІ; групами по 5, згортка ЗЛІВА НАПРАВО (перший тріт — старший).

; тріти одного слова: (якщо не перше) 2, потім біти
(0011 т5-тріти-списку
  (0010 (слова)
    (110
      ((null? слова) (001 ()))
      ((null? (решта слова))
       (т5-тріти-слова (перше слова)))
      (#d1:1
       (т5-зшити (т5-тріти-слова (перше слова))
         (111 тріт-розділювач (т5-тріти-списку (решта слова))))))))

; доповнити список трітів до кратного 5 (тріт 2 у КІНЦІ)
(0011 т5-вирівняти
  (0010 (тріти)
    (110
      ((нуль? (остача (довжина тріти) #d24:000000000000000000000101)) тріти)
      (#d1:1 (т5-вирівняти (т5-зшити тріти (111 тріт-розділювач (001 ()))))))))

; перші 5 трітів -> один байт (акумуляторна згортка зліва направо)
(0011 т5-група-байт-з
  (0010 (акум пять)
    (110
      ((null? пять) акум)
      (#d1:1 (т5-група-байт-з (т5-накопичити акум (перше пять)) (решта пять))))))

; взяти перші n елементів
(0011 т5-взяти-н
  (0010 (n список)
    (110
      ((нуль? n) (001 ()))
      ((null? список) (001 ()))
      (#d1:1 (111 (перше список) (т5-взяти-н (зменшити-на-один n) (решта список)))))))

; відкинути перші n елементів
(0011 т5-відкинути-н
  (0010 (n список)
    (110
      ((нуль? n) список)
      ((null? список) (001 ()))
      (#d1:1 (т5-відкинути-н (зменшити-на-один n) (решта список))))))

; повний енкодер: список слів (кожне — список бітів) -> список байтів
; --- Партія D9: content-store put/remove + fs-empty (наказ: партіями, у main) ---
; Семантика задана фікстурою d9-content-store-projection-laws.lisp:
; сховище = список пар (адреса . значення); розмір = довжина; отримати -> (значення) або ().
; Точні коди: 100 CAR, 011 CDR, 111 CONS, 001 QUOTE, 0101 EMPTY?, 101 EQ, 110 COND.

; content-store-put (вміст-сховище-покласти) — додати пару (адреса . значення) на початок
(0011 вміст-сховище-покласти
  (0010 (сховище адреса значення)
    (111 (111 адреса значення) сховище)))

; content-store-remove (вміст-сховище-видалити) — прибрати всі пари з цією адресою
(0011 вміст-сховище-видалити
  (0010 (сховище адреса)
    (110
      ((0101 сховище) (001 ()))
      ((101 адреса (100 (100 сховище)))
       (вміст-сховище-видалити (011 сховище) адреса))
      (#d1:1 (111 (100 сховище)
                  (вміст-сховище-видалити (011 сховище) адреса))))))

; fs-empty (фс-порожній) — порожнє сховище фактів (той самий контракт)
(0011 фс-порожній
  (0010 () (001 ())))

; prune-entry (обрізати-запис) — відкинути найстаріший (останній) запис
(0011 обрізати-запис
  (0010 (сховище)
    (110
      ((0101 сховище) (001 ()))
      ((0101 (011 сховище)) сховище)
      (#d1:1 (111 (100 сховище) (обрізати-запис (011 сховище)))))))

; --- Партія D8 №2: аксесори й похідні (наказ: партіями, у main) ---
; Точні коди: 100 CAR, 011 CDR, 111 CONS, 001 QUOTE. Жодних нових координат.

; rational (чисельник/знаменник) — раціональне як пара (чисельник . знаменник)
(0011 чисельник
  (0010 (дріб) (100 дріб)))

(0011 знаменник
  (0010 (дріб) (011 дріб)))

; realpart / imagpart — дійсна та уявна частини комплексної пари
(0011 дійсна-частина
  (0010 (пара) (100 пара)))

(0011 уявна-частина
  (0010 (пара) (011 пара)))

; aref (елемент-масиву) — n-й елемент послідовності
(0011 елемент-масиву
  (0010 (n список) (nth n список)))

; vector-copy (копіювати-вектор) — копія списку через append з порожнім
(0011 копіювати-вектор
  (0010 (с) (append с (001 ()))))

; getprop (отримати-властивість) — знайти значення за ключем у списку пар
(0011 отримати-властивість
  (0010 (ключ список) (assoc ключ список)))

; putprop (встановити-властивість) — додати пару (ключ . значення) на початок
(0011 встановити-властивість
  (0010 (ключ значення список)
    (111 (111 ключ значення) список)))

; --- Партія D8: чисті похідні функції (наказ власника: визначати партіями) ---
; Усе — похідне від наявних D3/D4/D5/D6/D8; жодних нових координат.

; dotimes (повторити-разів) — викликати дію N разів, повернути останній результат
(0011 повторити-разів
  (0010 (n дія)
    (повторити-з n дія (001 ()))))

(0011 повторити-з
  (0010 (n дія акум)
    (110
      ((нуль? n) акум)
      (#d1:1 (повторити-з (зменшити-на-один n) дія (дія))))))

; values (значення) — тотожність (одне значення не загортається)
(0011 значення
  (0010 (x) x))

; multiple-value-list (список-значень) — обгорнути у список
(0011 список-значень
  (0010 (x) (111 x (001 ()))))

; incf!/decf! (збільшити!/зменшити!) — арифметичні інкременти
(0011 збільшити!
  (0010 (x) (+ x #d24:000000000000000000000001)))

(0011 зменшити!
  (0010 (x) (- x #d24:000000000000000000000001)))

; closurep? (замикання?) — чи є значення функцією (через symbol? на car голови)
(0011 замикання?
  (0010 (x) (symbol? x)))

; boundp? (зв'язане?) — чи є символ зв'язаним (через symbol?)
(0011 зв'язане?
  (0010 (x)
    (110
      ((symbol? x) (001 #d1:1))
      (#d1:1 (001 ())))))

; pairlis-lite: vcons (вектор-сполучити) — cons двох значень у пару
(0011 вектор-сполучити
  (0010 (a b) (111 a b)))

; --- T5M: 3-байтова упаковка (15 трітів у 3 байти, LE) ---
; Власник 2026-10-17: «ми в т5м пакуєм по 3 байти». 3^15=14348907 < 2^24=16777216.
; Перевірено round-trip 7/7 (Python-модель). Група = 15 трітів -> одне 24-бітне
; число -> 3 байти little-endian. Група доповнюється трітом 2 до кратного 15.

(0011 т5м-вирівняти
  (0010 (тріти)
    (110
      ((нуль? (остача (довжина тріти) #d24:000000000000000000001111)) тріти)
      (#d1:1 (т5м-вирівняти (т5-зшити тріти (111 тріт-розділювач (001 ()))))))))

; 15 трітів -> 24-бітне значення (згортка зліва направо)
(0011 т5м-значення-15
  (0010 (тріти)
    (т5м-значення-з #d24:000000000000000000000000 тріти)))

(0011 т5м-значення-з
  (0010 (акум тріти)
    (110
      ((null? тріти) акум)
      (#d1:1 (т5м-значення-з (т5-накопичити акум (перше тріти)) (решта тріти))))))

; значення -> 3 байти (LE): [v%256, (v/256)%256, (v/65536)%256]
(0011 т5м-три-байти
  (0010 (v)
    (111 (остача v #d24:000000000000000100000000)
         (111 (остача (quotient v #d24:000000000000000100000000) #d24:000000000000000100000000)
              (111 (остача (quotient v #d24:000000010000000000000000) #d24:000000000000000100000000)
                   (001 ()))))))

; повний 3-байтовий енкодер: список слів -> плоский список байтів
(0011 т5м-у-байти
  (0010 (слова)
    (т5м-групувати-15 (т5м-вирівняти (т5-тріти-списку слова)))))

; --- T5M: ДЕКОДЕР 3 байти -> 15 трітів -> слова ---
; Round-trip перевірено 4/4 (Python-модель).

; 3 байти (LE) -> 24-бітне значення
(0011 т5м-значення-байтів
  (0010 (b0 b1 b2)
    (додати b0 (додати (помножити b1 #d24:000000000000000100000000) (помножити b2 #d24:000000010000000000000000)))))

; 24-бітне значення -> рівно 15 трітів (старший перший), акумуляторно
(0011 т5м-15-трітів
  (0010 (v)
    (т5м-15-з v #d24:000000000000000000000000 (001 ()))))

(0011 т5м-15-з
  (0010 (v акум тріти)
    (110
      ((рівно-15? (довжина тріти)) тріти)
      (#d1:1 (т5м-15-з (quotient v #d24:000000000000000000000011) акум (111 (остача v #d24:000000000000000000000011) тріти))))))

(0011 рівно-15?
  (0010 (n)
    (тотожне? n #d24:000000000000000000001111)))

; перевернути список (хвіст-рекурсивно, з акумулятором)
(0011 т5-перевернути
  (0010 (список акум)
    (110
      ((null? список) акум)
      (#d1:1 (т5-перевернути (решта список) (111 (перше список) акум))))))

; усі байти -> плоский список трітів

; Обернений стовпчиковий поділ трьох D24 байтів на 3.
; Математична межа кожного тимчасового слова <= 767.
; Повернення: (залишок . (новий-b0 новий-b1 новий-b2)).
(0011 т5м-байти-ділити-на-три
  (0010 (байти)
    (т5м-ділити-старший
      (перше байти)
      (перше (решта байти))
      (перше (решта (решта байти))))))

(0011 т5м-ділити-старший
  (0010 (b0 b1 b2)
    (т5м-ділити-середній
      b0 b1
      (quotient b2 #d24:000000000000000000000011)
      (остача b2 #d24:000000000000000000000011))))

(0011 т5м-ділити-середній
  (0010 (b0 b1 q2 r2)
    (т5м-ділити-середній-з
      b0 q2
      (додати (помножити r2 #d24:000000000000000100000000) b1))))

(0011 т5м-ділити-середній-з
  (0010 (b0 q2 v1)
    (т5м-ділити-молодший
      b0 q2
      (quotient v1 #d24:000000000000000000000011)
      (остача v1 #d24:000000000000000000000011))))

(0011 т5м-ділити-молодший
  (0010 (b0 q2 q1 r1)
    (т5м-ділити-молодший-з
      q1 q2 (додати (помножити r1 #d24:000000000000000100000000) b0))))

(0011 т5м-ділити-молодший-з
  (0010 (q1 q2 v0)
    (сполучити
      (остача v0 #d24:000000000000000000000011)
      (list (quotient v0 #d24:000000000000000000000011) q1 q2))))

; Наймолодший тріт видобуваємо першим; CONS дає порядок MSB-first.
(0011 т5м-15-трітів-із-байтів
  (0010 (байти кількість зібрані)
    (110
      ((нуль? кількість) зібрані)
      (#d1:1
       (т5м-15-із-частки
         (т5м-байти-ділити-на-три байти)
         кількість зібрані)))))

(0011 т5м-15-із-частки
  (0010 (ділення кількість зібрані)
    (т5м-15-трітів-із-байтів
      (решта ділення)
      (зменшити-на-один кількість)
      (сполучити (перше ділення) зібрані))))

(0011 т5м-тріти-байтів
  (0010 (байти)
    (110
      ((null? байти) (001 ()))
      (#d1:1
       (т5-зшити
        (т5м-15-трітів-із-байтів (list (перше байти) (перше (решта байти)) (перше (решта (решта байти)))) #d24:000000000000000000001111 (001 ()))
        (т5м-тріти-байтів (решта (решта (решта байти)))))))))

; прибрати хвостові 2 (пад)
(0011 т5-без-хвостових-2
  (0010 (тріти)
    (110
      ((null? тріти) (001 ()))
      (#d1:1
       (110
        ((тотожне? (т5-останній тріти) тріт-розділювач) (т5-без-хвостових-2 (т5-без-останнього тріти)))
        (#d1:1 тріти))))))

; розбити тріти на слова по розділювачу 2
(0011 т5-розбити-по-2
  (0010 (тріти поточне слова)
    (110
      ((null? тріти) (т5-перевернути (т5-додати-слово поточне слова) (001 ())))
      ((тотожне? (перше тріти) тріт-розділювач)
       (т5-розбити-по-2 (решта тріти) (001 ()) (т5-додати-слово поточне слова)))
      (#d1:1 (т5-розбити-по-2 (решта тріти)
                              (111 (т5м-біт-д1 (перше тріти)) поточне) слова)))))

(0011 т5-додати-слово
  (0010 (поточне слова)
    (110
      ((null? поточне) слова)
      (#d1:1 (111 (т5-перевернути поточне (001 ())) слова)))))

(0011 т5-останній
  (0010 (список)
    (110 ((null? (решта список)) (перше список))
         (#d1:1 (т5-останній (решта список))))))

(0011 т5-без-останнього
  (0010 (список)
    (110 ((null? (решта список)) (001 ()))
         (#d1:1 (111 (перше список) (т5-без-останнього (решта список)))))))

; ПОВНИЙ декодер: список байтів -> список слів (кожне — список бітів)
(0011 т5м-з-байтів
  (0010 (байти)
    (т5-розбити-по-2 (т5-без-хвостових-2 (т5м-тріти-байтів байти)) (001 ()) (001 ()))))


; Т5М — стовпчикове пакування трьох байтів у самій мові SENS.
; Кожний проміжний перенос <= 767 (D24). Не обчислюємо тимчасове
; 15-трітове число > межі звичайного знакового D24.
; Закон: [b0,b1,b2] = [0,0,0]; для тріта t повторити V := 3V+t.
; T5M three-byte streaming step. Direct D4 LAMBDA applications bind v0/v1/v2;
; LET macro projection is not an authority for domain-qualified numbers.
; Each step is exact D24: (3 × byte + trit + previous carry).
(0011 т5м-байтовий-крок
  (0010 (тріт байти)
    (т5м-байтовий-крок-другий
      (додати (помножити (перше байти) #d24:000000000000000000000011) тріт)
      (решта байти))))

(0011 т5м-байтовий-крок-другий
  (0010 (v0 решта-байтів)
    (т5м-байтовий-крок-третій
      v0
      (додати (помножити (перше решта-байтів) #d24:000000000000000000000011)
              (quotient v0 #d24:000000000000000100000000))
      (перше (решта решта-байтів)))))

(0011 т5м-байтовий-крок-третій
  (0010 (v0 v1 b2)
    (list
      (остача v0 #d24:000000000000000100000000)
      (остача v1 #d24:000000000000000100000000)
      (остача
        (додати (помножити b2 #d24:000000000000000000000011) (quotient v1 #d24:000000000000000100000000))
        #d24:000000000000000100000000))))

(0011 т5м-байти-групи-з
  (0010 (тріти байти)
    (110
      ((null? тріти) байти)
      (#d1:1
       (т5м-байти-групи-з
         (решта тріти) (т5м-байтовий-крок (перше тріти) байти))))))

(0011 т5м-байти-із-трітів
  (0010 (тріти)
    (т5м-байти-групи-з тріти (list #d24:000000000000000000000000 #d24:000000000000000000000000 #d24:000000000000000000000000))))

(0011 т5м-групувати-15
  (0010 (тріти)
    (110
      ((null? тріти) (001 ()))
      (#d1:1
       (т5-зшити
        (т5м-байти-із-трітів (т5-взяти-н #d24:000000000000000000001111 тріти))
        (т5м-групувати-15 (т5-відкинути-н #d24:000000000000000000001111 тріти)))))))

; зшити два списки
(0011 т5-зшити
  (0010 (a b)
    (110
      ((null? a) b)
      (#d1:1 (111 (перше a) (т5-зшити (решта a) b))))))

(0011 т5-у-байти
  (0010 (слова)
    (т5-групувати (т5-вирівняти (т5-тріти-списку слова)))))

(0011 т5-групувати
  (0010 (тріти)
    (110
      ((null? тріти) (001 ()))
      (#d1:1
       (111 (т5-група-байт-з #d24:000000000000000000000000 (т5-взяти-н #d24:000000000000000000000101 тріти))
            (т5-групувати (т5-відкинути-н #d24:000000000000000000000101 тріти)))))))

(0011 рівно-пять?
  (0010 (n)
    (тотожне? n #d24:000000000000000000000101)))

; expt (піднести-до-степеня)
; D6 POWER: власна рекурсія SENS; показники — невід'ємні D24+.
; Канонічні D24 нуль/один, жодних числових голів або десяткових посередників.
(0011 піднести-до-степеня
  (0010 (основа показник)
    (110
      ((нуль? показник) #d24:000000000000000000000001)
      (#d1:1
       (помножити основа
         (піднести-до-степеня основа (зменшити-на-один показник)))))))
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
(0011 curry частково-застосувати)
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


; === D9 SENS-native verified-coordinate cohort: no D9 opcode admission ===
; D9:110100101 NUMERIC-EQUALITY. Exact D24+ numeric order is from D5
; LESSP/GREATERP; mixed widths and unqualified operands reject in D5.
(0011 числовий-рівність
  (0010 (лівий правий)
    (за-умовою
      ((менше? лівий правий) #d1:0)
      ((більше? лівий правий) #d1:0)
      (#d1:1 #d1:1))))

; D9:010000000 CDR-PROPER. Observational equality of the proper list tail.
; The only construction/deconstruction is ratified D3 CONS/CDR.
(0011 канон-закон-решта-правильний
  (0010 (голова хвіст)
    (equal? (решта (сполучити голова хвіст)) хвіст)))

; D9:010110001 CDR-DOTTED. EQ on an atomic dotted tail; D3 EQ
; rejects non-atomic carriers rather than silently inventing identity.
(0011 канон-закон-решта-крапковий
  (0010 (голова хвіст)
    (тотожне? (решта (сполучити голова хвіст)) хвіст)))

; D9:001110010 CANON-LAW-EQ-REFLEXIVE-ATOM — owner #4008.
; Atom(x) => EQ(x,x)=D1:1. Pair carrier rejected via CAR(D3:000).
; Lower D3 laws only; no new D9 call mechanism or independent primitive.
(0011 канон-закон-рівність-рефлексивний-атом
  (0010 (значення)
    (за-умовою
      ((атом? значення) (тотожне? значення значення))
      ((атом? (як-є ())) (перше (як-є ()))))))

; D9 Canon law harvest from lib/canon.lisp (owner-ratified D9 #4008).
; D9:001111001 CANON-EMPTY-LIST is structural D3:000, never D1:0.
; The following D9 laws return the donor's explicit three-field result
; (canon-law-result law status), not a coerced truth value or a new primitive.
(0011 канон-порожній-список (001 ()))

(0011 канон-запис-закону
  (0010 (закон стан-закону)
    (111 (001 canon-law-result)
      (111 закон (111 стан-закону (001 ()))))))

; D9:010111011 CANON-LAW-EMPTY-LIST.
(0011 канон-закон-порожній-список
  (0010 ()
    (110
      ((101 канон-порожній-список (001 ()))
       (канон-запис-закону (001 empty-list) (001 satisfied)))
      (#d1:1
       (канон-запис-закону (001 empty-list) (001 violated))))))

; D9:010111100 CANON-LAW-QUOTE-SUPPRESSES-EVALUATION.
; Undefined names remain quoted data, never an evaluated lookup.
(0011 канон-закон-цитування-пригнічує-обчислення
  (0010 ()
    (110
      ((101 (001 never-defined-canon-symbol)
            (001 never-defined-canon-symbol))
       (канон-запис-закону
         (001 quote-suppresses-evaluation) (001 satisfied)))
      (#d1:1
       (канон-запис-закону
         (001 quote-suppresses-evaluation) (001 violated))))))

; D9:010101100 CANON-LAW-COND-FIRST-MATCH-SHORT-CIRCUIT.
; An unselected undefined test must not execute.
(0011 канон-закон-умова-перший-збіг-короткий-ланцюг
  (0010 ()
    (110
      ((101
         (110
           (#d1:1 (001 selected))
           ((never-defined-canon-predicate) (001 forbidden)))
         (001 selected))
       (канон-запис-закону
         (001 cond-first-match-short-circuit) (001 satisfied)))
      (#d1:1
       (канон-запис-закону
         (001 cond-first-match-short-circuit) (001 violated))))))

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
; Інваріант 0 < chunk ≤ a (D24+). Перевірка a < 2*chunk
; переповнювала D24 у D48 перед D5 LESSP (змішаний домен).
; Рівносильна перевірка a - chunk < chunk лишається у вхідному Dn;
; тільки після неї подвоюємо chunk, коли 2*chunk ≤ a.
(0011 largest-chunk
  (0010 (a b chunk mult)
    (110
      ((менше? (відняти a chunk) chunk) (сполучити chunk mult))
      (#d1:1
       (largest-chunk a b
         (додати chunk chunk)
         (додати mult mult))))))

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
; Integer quotient recurses in SENS; D5 QUOTIENT is exact rational division.
; Consume the (chunk . multiplier) pair as data directly, not through a
; historical LET macro that can turn a numeric result into a callable head.
(0011 quotient-from-chunk
  (0010 (a b chunk-and-multiplier)
    (додати (решта chunk-and-multiplier)
            (quotient (відняти a (перше chunk-and-multiplier)) b))))
(0011 quotient
  (0010 (a b)
    (110
      ((нуль? b) (частка a b))
      ((менше? a b) #d24:000000000000000000000000)
      (#d1:1
       (quotient-from-chunk a b
         (largest-chunk a b b #d24:000000000000000000000001))))))

; Integer remainder uses the Lisp-owned floor quotient: a - b * floor(a / b).
(0011 mod
  (0010 (a b)
    (відняти a (помножити b (quotient a b)))))

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
    (1110 (10111 dividend divisor) (mod dividend divisor))))

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


; D8:10100001 CHAR< / D8:00100111 CHAR> — Unicode codepoint order.
; D8:11100000 CHAR-CODE supplies an exact D24 value, D5:11010 LESSP owns order.
; No direct D8 predicate admission: these are SENS language closures.
(0011 символ-менший?
  (0010 (ліве праве)
    (11010 (11100000 ліве) (11100000 праве))))
(0011 символ-більший?
  (0010 (ліве праве)
    (11010 (11100000 праве) (11100000 ліве))))

; D8:00101000 CHAR= — equality is neither less-than nor greater-than.
(0011 символ-рівний?
  (0010 (ліве праве)
    (110
      ((символ-менший? ліве праве) #d1:0)
      ((символ-більший? ліве праве) #d1:0)
      (#d1:1 #d1:1))))

; D8:00110111 STRING= — lexical equality from both ratified orders.
; String comparison rejects incompatible non-string operands by its own law.
(0011 текст-рівний?
  (0010 (ліве праве)
    (110
      ((string<? ліве праве) #d1:0)
      ((string<? праве ліве) #d1:0)
      (#d1:1 #d1:1))))


; D8:10101011 SCALE — exact numeric scaling through ratified D5 TIMES.
; Both operands retain explicit qualified D24+ numeric carriers.
(0011 масштабувати
  (0010 (число коефіцієнт)
    (помножити число коефіцієнт)))


; D8:00000011 REMAP — proper-list specialization by D6:101000 MAP.
; List-order and D1/structural results belong to SENS, not host iteration.
(0011 перевідобразити
  (0010 (дія елементи)
    (відобразити дія елементи)))


; D8:00000001 DOSEQ — proper-list effect iteration, left to right.
; Native SENS D6 MAP evaluates each application; all mapped values are
; discarded, and the iteration itself returns canonical D3:000 empty ().
(0011 для-кожного-елемента
  (0010 (дія елементи)
    ((0010 (відкинуті-результати) (001 ()))
     (відобразити дія елементи))))


; D8 дослідницька партія 2026-10-17: точні ратифіковані поверхні.
; knowledge/d8-ratified.json + tests/semantic/d8-partial-tailp-lcm-push-laws.lisp
; D8:00011010 PARTIAL = D6:111110 CURRY/partial (без нового D8 opcode).
(0011 застосувати-префікс частково-застосувати)

; D8:00100110 LCM = |a*b| / gcd(|a|,|b|), із нульовою межею.
; Усі числа — кваліфікована D24+ математика, не координати D8.
(0011 нск
  (0010 (ліве праве)
    (110
      ((нуль? ліве) #d24:000000000000000000000000)
      ((нуль? праве) #d24:000000000000000000000000)
      (#d1:1
       (quotient
         (помножити (модуль ліве) (модуль праве))
         (нсд (модуль ліве) (модуль праве)))))))

; D8:00101100 MOD — ратифікований поверхневий синонім
; вже мовного SENS визначення mod, без окремої хост-семантики.
(0011 модульна-остача mod)

; D9:011010000 CDADAAAAR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-п-п-п
  (0010 (значення)
    (011 (100 (011 (100 (100 (100 (100 значення)))))))))

; D9:011010001 CDADAAADR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-п-п-р
  (0010 (значення)
    (011 (100 (011 (100 (100 (100 (011 значення)))))))))

; D9:011010010 CDADAADAR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-п-р-п
  (0010 (значення)
    (011 (100 (011 (100 (100 (011 (100 значення)))))))))

; D9:011010011 CDADAADDR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-п-р-р
  (0010 (значення)
    (011 (100 (011 (100 (100 (011 (011 значення)))))))))

; D9:011010100 CDADADAAR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-р-п-п
  (0010 (значення)
    (011 (100 (011 (100 (011 (100 (100 значення)))))))))

; D9:011010101 CDADADADR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-р-п-р
  (0010 (значення)
    (011 (100 (011 (100 (011 (100 (011 значення)))))))))

; D9:011010110 CDADADDAR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-р-р-п
  (0010 (значення)
    (011 (100 (011 (100 (011 (011 (100 значення)))))))))

; D9:011010111 CDADADDDR: сім кроків D3 CAR/CDR за ратифікованим порядком.
(0011 р-п-р-п-р-р-р
  (0010 (значення)
    (011 (100 (011 (100 (011 (011 (011 значення)))))))))

; D8:01011011 CHAR — character cell at D24 index in a string.
; D9:110011100 STRING-EMPTY?, D9:110101011 STRING-FIRST and
; D9:110011101 STRING-REST are existing exact-domain mechanisms.
; Bounds failure uses a native D3 CAR(()) error, never a false value.
(0011 символ
  (0010 (текст індекс)
    (110
      ((110011100 текст) (100 (001 ())))
      ((нуль? індекс) (110101011 текст))
      (#d1:1
       (символ
         (110011101 текст)
         (зменшити-на-один індекс))))))

; D9:110100010 STRING-LENGTH — D24 codepoint count, no host number.
(0011 рядок-довжина
  (0010 (текст)
    (110
      ((110011100 текст) #d24:000000000000000000000000)
      (#d1:1 (збільшити-на-один (рядок-довжина (110011101 текст)))))))

; D9:110101110 IDENTITY — projection of already defined Lisp identity.
(0011 тотожність identity)

; D9:001110110 CANON-LAW-CDR-IMPROPER: atomic dotted tail survives CONS/CDR.
; Does not claim a new independent primitive or direct D9 opcode admission.
(0011 канон-закон-решта-неправильний
  (0010 (голова атомний-хвіст)
    (101 (011 (111 голова атомний-хвіст)) атомний-хвіст)))

; D9:011011000 CDADDAAAR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-п-п-п
  (0010 (значення)
    (011 (100 (011 (011 (100 (100 (100 значення)))))))))

; D9:011011001 CDADDAADR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-п-п-р
  (0010 (значення)
    (011 (100 (011 (011 (100 (100 (011 значення)))))))))

; D9:011011010 CDADDADAR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-п-р-п
  (0010 (значення)
    (011 (100 (011 (011 (100 (011 (100 значення)))))))))

; D9:011011011 CDADDADDR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-п-р-р
  (0010 (значення)
    (011 (100 (011 (011 (100 (011 (011 значення)))))))))

; D9:011011100 CDADDDAAR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-р-п-п
  (0010 (значення)
    (011 (100 (011 (011 (011 (100 (100 значення)))))))))

; D9:011011101 CDADDDADR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-р-п-р
  (0010 (значення)
    (011 (100 (011 (011 (011 (100 (011 значення)))))))))

; D9:011011110 CDADDDDAR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-р-р-п
  (0010 (значення)
    (011 (100 (011 (011 (011 (011 (100 значення)))))))))

; D9:011011111 CDADDDDDR — ратифікована композиція семи D3 CAR/CDR.
(0011 р-п-р-р-р-р-р
  (0010 (значення)
    (011 (100 (011 (011 (011 (011 (011 значення)))))))))

; D9:011100000 CDDAAAAAR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-п-п-п
  (0010 (значення)
    (011 (011 (100 (100 (100 (100 (100 значення)))))))))

; D9:011100001 CDDAAAADR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-п-п-р
  (0010 (значення)
    (011 (011 (100 (100 (100 (100 (011 значення)))))))))

; D9:011100010 CDDAAADAR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-п-р-п
  (0010 (значення)
    (011 (011 (100 (100 (100 (011 (100 значення)))))))))

; D9:011100011 CDDAAADDR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-п-р-р
  (0010 (значення)
    (011 (011 (100 (100 (100 (011 (011 значення)))))))))

; D9:011100100 CDDAADAAR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-р-п-п
  (0010 (значення)
    (011 (011 (100 (100 (011 (100 (100 значення)))))))))

; D9:011100101 CDDAADADR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-р-п-р
  (0010 (значення)
    (011 (011 (100 (100 (011 (100 (011 значення)))))))))

; D9:011100110 CDDAADDAR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-р-р-п
  (0010 (значення)
    (011 (011 (100 (100 (011 (011 (100 значення)))))))))

; D9:011100111 CDDAADDDR — 7 точних D3:100 CAR / D3:011 CDR.
(0011 р-р-п-п-р-р-р
  (0010 (значення)
    (011 (011 (100 (100 (011 (011 (011 значення)))))))))


; D9 canonical reasoning outcomes — ratified exact coordinates, from
; lib/result-status.lisp (historical research source; only SENS owns meaning).
; Each result is ordinary D3/D4 list data, never a new host Value variant.
; Canonical tags are quoted data, not executable English identifiers.
; D9:000111101 MAKE-PROVED / D9:000110101 MAKE-UNKNOWN.
(0011 створити-доведений
  (0010 (твердження докази)
    (1110 (001 proved) твердження докази)))
(0011 створити-невідоме
  (0010 (предмет)
    (1110 (001 unknown) предмет)))

; D9:001000000 MAKE-PARTIAL / D9:000100111 MAKE-BLOCKED.
(0011 створити-частковий
  (0010 (значення межа)
    (1110 (001 partial) значення межа)))
(0011 створити-заблокований
  (0010 (причина)
    (1110 (001 blocked) причина)))

; D9:000000111 MAKE-DISPUTED / D9:000001101 MAKE-INVALID.
(0011 створити-спірний
  (0010 (докази)
    (1110 (001 disputed) докази)))
(0011 створити-некоректний
  (0010 (причина вміст)
    (1110 (001 invalid) причина вміст)))


; D9:101100110 / 101101010 / 101010011 / 101111111 / 101010100 / 101111000.
; Партія епістемічних проєкцій із lib/epistemic.lisp.
; Сигнатура: структурний запис -> поле; пошук за ключем — D5:11100 ASSOC,
; вибір значення — D4:1001 CADR; без нового D9 opcode чи host-семантики.
(0011 твердження-твердження
  (0010 (запис)
    (1001 (знайти-за-ключем (001 statement) (011 запис)))))
(0011 твердження-перевірка
  (0010 (запис)
    (1001 (знайти-за-ключем (001 review) (011 запис)))))
(0011 доказ-метод
  (0010 (запис)
    (1001 (знайти-за-ключем (001 method) (011 запис)))))
(0011 доказ-підсумок
  (0010 (запис)
    (1001 (знайти-за-ключем (001 outcome) (011 запис)))))
(0011 намір-ціль
  (0010 (запис)
    (1001 (знайти-за-ключем (001 goal) (011 запис)))))
(0011 спостереження-твердження
  (0010 (запис)
    (1001 (знайти-за-ключем (001 statement) (011 запис)))))


; D10:0010010001 / 0010000111 / 0001110111 / 0001111011 / 0010010000 / 0010011010.
; Шість епістемічних проєкцій із lib/epistemic.lisp, чітка D5:11100 ASSOC
; + D4:1001 CADR над структурними записами SENS, без зовнішніх обчислювачів.
(0011 посилання-на-джерело-доказу
  (0010 (запис)
    (1001 (знайти-за-ключем (001 source-ref) (011 запис)))))
(0011 посилання-доказу-на-твердження
  (0010 (запис)
    (1001 (знайти-за-ключем (001 claim-ref) (011 запис)))))
(0011 джерело-спостереження
  (0010 (запис)
    (1001 (знайти-за-ключем (001 source) (011 запис)))))
(0011 вимоги-наміру
  (0010 (запис)
    (1001 (знайти-за-ключем (001 requires) (011 запис)))))
(0011 умови-зупинки-наміру
  (0010 (запис)
    (1001 (знайти-за-ключем (001 stop-on) (011 запис)))))
(0011 продукти-наміру
  (0010 (запис)
    (1001 (знайти-за-ключем (001 produces) (011 запис)))))

; D9:000000100 RESULT-TAGGED? — strict one-bit D1 verdict, not host truthiness.
; A malformed pair-valued head is not an admitted status atom.
(0011 результат-позначений?
  (0010 (результат)
    (110
      ((010 результат) #d1:0)
      ((0100 (010 (100 результат))) #d1:0)
      ((101 (100 результат) (001 proved)) #d1:1)
      ((101 (100 результат) (001 unknown)) #d1:1)
      ((101 (100 результат) (001 partial)) #d1:1)
      ((101 (100 результат) (001 blocked)) #d1:1)
      ((101 (100 результат) (001 disputed)) #d1:1)
      ((101 (100 результат) (001 invalid)) #d1:1)
      (#d1:1 #d1:0))))

; D9:000011001 RESULT-STATUS / D9:000110010 RESULT-PAYLOAD.
; Unsupported outcome shapes project to (), as the research donor specifies.
(0011 результат-стан
  (0010 (результат)
    (110
      ((результат-позначений? результат) (100 результат))
      (#d1:1 (001 ())))))
(0011 результат-вміст
  (0010 (результат)
    (110
      ((результат-позначений? результат) (011 результат))
      (#d1:1 (001 ())))))

; D9:011101000 CDDADAAAR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-п-п-п
  (0010 (значення)
    (011 (011 (100 (011 (100 (100 (100 значення)))))))))

; D9:011101001 CDDADAADR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-п-п-р
  (0010 (значення)
    (011 (011 (100 (011 (100 (100 (011 значення)))))))))

; D9:011101010 CDDADADAR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-п-р-п
  (0010 (значення)
    (011 (011 (100 (011 (100 (011 (100 значення)))))))))

; D9:011101011 CDDADADDR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-п-р-р
  (0010 (значення)
    (011 (011 (100 (011 (100 (011 (011 значення)))))))))

; D9:011101100 CDDADDAAR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-р-п-п
  (0010 (значення)
    (011 (011 (100 (011 (011 (100 (100 значення)))))))))

; D9:011101101 CDDADDADR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-р-п-р
  (0010 (значення)
    (011 (011 (100 (011 (011 (100 (011 значення)))))))))

; D9:011101110 CDDADDDAR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-р-р-п
  (0010 (значення)
    (011 (011 (100 (011 (011 (011 (100 значення)))))))))

; D9:011101111 CDDADDDDR — сім CAR/CDR кроків із ратифікованої драбини.
(0011 р-р-п-р-р-р-р
  (0010 (значення)
    (011 (011 (100 (011 (011 (011 (011 значення)))))))))


; D9:011110000 CDDDAAAAR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-п-п-п
  (0010 (значення)
    (011 (011 (011 (100 (100 (100 (100 значення)))))))))

; D9:011110001 CDDDAAADR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-п-п-р
  (0010 (значення)
    (011 (011 (011 (100 (100 (100 (011 значення)))))))))

; D9:011110010 CDDDAADAR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-п-р-п
  (0010 (значення)
    (011 (011 (011 (100 (100 (011 (100 значення)))))))))

; D9:011110011 CDDDAADDR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-п-р-р
  (0010 (значення)
    (011 (011 (011 (100 (100 (011 (011 значення)))))))))

; D9:011110100 CDDDADAAR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-р-п-п
  (0010 (значення)
    (011 (011 (011 (100 (011 (100 (100 значення)))))))))

; D9:011110101 CDDDADADR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-р-п-р
  (0010 (значення)
    (011 (011 (011 (100 (011 (100 (011 значення)))))))))

; D9:011110110 CDDDADDAR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-р-р-п
  (0010 (значення)
    (011 (011 (011 (100 (011 (011 (100 значення)))))))))

; D9:011110111 CDDDADDDR — сім вкладених D3 CAR/CDR, тільки SENS.
(0011 р-р-р-п-р-р-р
  (0010 (значення)
    (011 (011 (011 (100 (011 (011 (011 значення)))))))))

; D9:011111000 CDDDDAAAR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-п-п-п
  (0010 (значення)
    (011 (011 (011 (011 (100 (100 (100 значення)))))))))

; D9:011111001 CDDDDAADR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-п-п-р
  (0010 (значення)
    (011 (011 (011 (011 (100 (100 (011 значення)))))))))

; D9:011111010 CDDDDADAR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-п-р-п
  (0010 (значення)
    (011 (011 (011 (011 (100 (011 (100 значення)))))))))

; D9:011111011 CDDDDADDR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-п-р-р
  (0010 (значення)
    (011 (011 (011 (011 (100 (011 (011 значення)))))))))

; D9:011111100 CDDDDDAAR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-р-п-п
  (0010 (значення)
    (011 (011 (011 (011 (011 (100 (100 значення)))))))))

; D9:011111101 CDDDDDADR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-р-п-р
  (0010 (значення)
    (011 (011 (011 (011 (011 (100 (011 значення)))))))))

; D9:011111110 CDDDDDDAR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-р-р-п
  (0010 (значення)
    (011 (011 (011 (011 (011 (011 (100 значення)))))))))

; D9:011111111 CDDDDDDDR — ратифікований семикроковий селектор D3.
(0011 р-р-р-р-р-р-р
  (0010 (значення)
    (011 (011 (011 (011 (011 (011 (011 значення)))))))))

; D9 four translation-envelope projections, harvested from lib/translation.lisp.
; Canonical envelope is (translation/1 STATUS KIND SOURCE PAYLOAD), ordinary
; SENS list data. The external translator grants no semantic admission.
; Direct D3 CAR/CDR projection; no host registry, no decimal intermediary.
; D9:000000101 TRANSLATION-STATUS, D9:000101100 TRANSLATION-KIND.
(0011 переклад-стан
  (0010 (пропозиція)
    (100 (011 пропозиція))))
(0011 переклад-вид
  (0010 (пропозиція)
    (100 (011 (011 пропозиція)))))

; D9:000010100 TRANSLATION-SOURCE, D9:000101110 TRANSLATION-PAYLOAD.
(0011 переклад-джерело
  (0010 (пропозиція)
    (100 (011 (011 (011 пропозиція))))))
(0011 переклад-вміст
  (0010 (пропозиція)
    (100 (011 (011 (011 (011 пропозиція)))))))

; D8:01001100 TRUNCATE — integer quotient toward zero, exact D24+ only.
(0011 округлити-до-нуля
  (0010 (ділене дільник)
    ((0010 (частка-модуля)
       (за-умовою
         ((менше? ділене #d24:000000000000000000000000)
          (за-умовою
            ((менше? дільник #d24:000000000000000000000000) частка-модуля)
            (#d1:1 (змінити-знак частка-модуля))))
         ((менше? дільник #d24:000000000000000000000000) (змінити-знак частка-модуля))
         (#d1:1 частка-модуля)))
     (quotient (модуль ділене) (модуль дільник)))))

; D8:01000000 REM — dividend-signed remainder, a - b * trunc(a/b).
(0011 остача-зі-знаком
  (0010 (ділене дільник)
    (відняти ділене
      (помножити дільник (округлити-до-нуля ділене дільник)))))


; D9 guard decision/status algebra from lib/guard.lisp.
; Ratified D9:000010001 GUARD-DECISION? and D9:000000000 GUARD-EVIDENCE-STATUS?
; Every result is a strict D1 one-bit predicate. Non-atomic decision/status
; data is rejected by D1:NO rather than sent to D3 EQ on a pair.
(0011 захист-рішення?
  (0010 (рішення)
    (110
      ((0100 (010 рішення)) #d1:0)
      ((101 рішення (як-є allow)) #d1:1)
      ((101 рішення (як-є warn)) #d1:1)
      ((101 рішення (як-є reject)) #d1:1)
      ((101 рішення (як-є unknown)) #d1:1)
      (#d1:1 #d1:0))))
(0011 захист-доказ-стан?
  (0010 (стан)
    (110
      ((0100 (010 стан)) #d1:0)
      ((101 стан (як-є confirmed)) #d1:1)
      ((101 стан (як-є partial)) #d1:1)
      ((101 стан (як-є unresolved)) #d1:1)
      ((101 стан (як-є broken)) #d1:1)
      (#d1:1 #d1:0))))


; D8:11111101 PAIR — historical two-sequence pair constructor.
; Historical Lisp PAIR is recursively derived from CAR/CDR/CONS; the
; existing D6 ZIP expression has this exact list-of-cons geometry.
; The new D8 coordinate is an identity/projection, not a direct opcode.
(0011 пара
  (0010 (ліві праві)
    (спарувати-послідовності ліві праві)))


; D8:10111111 INTEGER-LENGTH — закон ратифікованої координати #3960.
; Математичний D24 (не текст D7 і не голова виклику D8); для від'ємного
; двійкове доповнення рахуємо за абсолютним значенням мінус один.
(0011 біт-довжина-невідємного
  (0010 (число)
    (110
      ((нуль? число) #d24:000000000000000000000000)
      (#d1:1
       (додати #d24:000000000000000000000001
         (біт-довжина-невідємного (quotient число #d24:000000000000000000000010)))))))
(0011 бітова-довжина-цілого
  (0010 (число)
    (110
      ((менше? число #d24:000000000000000000000000)
       (біт-довжина-невідємного (відняти (модуль число) #d24:000000000000000000000001)))
      (#d1:1 (біт-довжина-невідємного число)))))

; D8:01001110 LOGBITP — D1 strict bit predicate over the qualified
; mathematical D24 index. Negative integers: two's-complement NOT(|n|-1).
(0011 біт-невідємного?
  (0010 (позиція число)
    (110
      ((нуль? позиція)
       (equal? (модульна-остача число #d24:000000000000000000000010) #d24:000000000000000000000001))
      (#d1:1
       (біт-невідємного? (зменшити-на-один позиція)
                          (quotient число #d24:000000000000000000000010))))))
(0011 біт-встановлений?
  (0010 (позиція число)
    (110
      ((менше? число #d24:000000000000000000000000)
       (not? (біт-невідємного? позиція
               (відняти (модуль число) #d24:000000000000000000000001))))
      (#d1:1 (біт-невідємного? позиція число)))))
; D9 Canon record algebra, recovered from lib/canon.lisp. All six identities
; have ratified nine-bit coordinates; no direct D9 opcode admission.
; D9:001110101 CANON-LAW-RESULT reuses the existing SENS record constructor.
(0011 канон-закон-результат канон-запис-закону)
; D9:101000100 / D9:001010111 explicit SATISFIED/VIOLATED records.
(0011 канон-закон-виконаний
  (0010 (закон)
    (канон-закон-результат закон (як-є satisfied))))
(0011 канон-закон-порушений
  (0010 (закон)
    (канон-закон-результат закон (як-є violated))))
; D9:001000010 third field of (canon-law-result law status).
(0011 канон-закон-стан
  (0010 (запис) (перше (решта (решта запис)))))
; D9:010011011 two-field conformance report.
(0011 канон-відповідність-результат
  (0010 (стан)
    (сполучити (як-є canon-conformance)
      (сполучити стан (як-є ())))))
; D9:010010100 aggregate exact Canon statuses; empty list is satisfied.
(0011 канон-відповідність-з
  (0010 (результати)
    (за-умовою
      ((атом? результати)
       (за-умовою
         ((тотожне? результати (як-є ()))
          (канон-відповідність-результат (як-є satisfied)))
         (#d1:1 (канон-відповідність-результат (як-є violated)))))
      (#d1:1
       (за-умовою
         ((тотожне? (канон-закон-стан (перше результати)) (як-є satisfied))
          (канон-відповідність-з (решта результати)))
         (#d1:1 (канон-відповідність-результат (як-є violated))))))))

; D9:001111000 CANON-LAW-SYMBOLIC-SURFACE from lib/canon.lisp.
; Exact D3 ATOM/CAR/CDR/EQ/CONS law, as the already admitted Canon record.
; It is a D9 language definition, not a new host primitive or opcode.
(0011 канон-закон-символьний-поверхня
  (0010 ()
    (110
      ((010 (001 атом))
       (110
         ((101 (100 (111 (001 ліве) (001 праве))) (001 ліве))
          (110
            ((101 (011 (111 (001 ліве) (001 праве))) (001 праве))
             (канон-запис-закону (001 symbolic-surface) (001 satisfied)))
            (#d1:1
             (канон-запис-закону (001 symbolic-surface) (001 violated)))))
         (#d1:1
          (канон-запис-закону (001 symbolic-surface) (001 violated)))))
      (#d1:1
       (канон-запис-закону (001 symbolic-surface) (001 violated))))))

; D9:000011010 MAKE-TRANSLATION-REVIEW — ratified review envelope.
; Physical SENS D3 CONS builds (translation-review/1 STATUS CODE PROPOSAL DETAIL).
(0011 створити-переклад-перевірка
  (0010 (стан код пропозиція деталі)
    (111 (001 translation-review/1)
      (111 стан (111 код (111 пропозиція (111 деталі (001 ()))))))))

; D9:000111100 TRANSLATION-REVIEW-STATUS — projection of review field 2.
(0011 переклад-перевірка-стан
  (0010 (перевірка) (100 (011 перевірка))))

; D9:000100011 TRANSLATION-REVIEW-CODE — projection of review field 3.
(0011 переклад-перевірка-код
  (0010 (перевірка) (100 (011 (011 перевірка)))))

; D9:000100101 TRANSLATION-REVIEW-PROPOSAL — field 4.
(0011 переклад-перевірка-пропозиція
  (0010 (перевірка) (100 (011 (011 (011 перевірка))))))

; D9:000101111 TRANSLATION-REVIEW-DETAIL — field 5.
(0011 переклад-перевірка-деталь
  (0010 (перевірка) (100 (011 (011 (011 (011 перевірка)))))))


; D8:11100110 LSH — left shift by a nonnegative D24+ count.
; Recurrence uses only SENS arithmetic and SUB1; no host bit operator.
(0011 зсунути-вліво
  (0010 (значення зсув)
    (110
      ((нуль? зсув) значення)
      ((нуль? значення) #d24:000000000000000000000000)
      (#d1:1
       (зсунути-вліво
         (помножити значення #d24:000000000000000000000010)
         (зменшити-на-один зсув))))))
(0011 lsh зсунути-вліво)

; D8:00011111 CEILING — дослідницький закон для D24+ a>=0 та b>0.
; Числова область лишається D24+; це SENS-похідна, не прямий D8 opcode.
(0011 округлити-вгору
  (0010 (чисельник знаменник)
    (110
      ((нуль? (mod чисельник знаменник))
       (quotient чисельник знаменник))
      (#d1:1
       (додати-1 (quotient чисельник знаменник))))))

; D8:01000101 ASH — множення на два k разів, лише k>=0 в D24+.
; Відсутні D7-цифри й недопущені числові голови.
(0011 арифметичний-зсув
  (0010 (значення зсув)
    (110
      ((нуль? зсув) значення)
      (#d1:1
       (арифметичний-зсув
         (помножити значення #d24:000000000000000000000010)
         (зменшити-на-один зсув))))))

; D8:00011110 RSH — ділення на два k разів, невід'ємний D24+.
(0011 зсунути-вправо
  (0010 (значення зсув)
    (110
      ((нуль? зсув) значення)
      (#d1:1
       (зсунути-вправо
         (quotient значення #d24:000000000000000000000010)
         (зменшити-на-один зсув))))))

; D9:111100001 MAKE-WORLD: immutable (world parent journal metadata) record.
(0011 створити-світ
  (0010 (батько журнал метадані)
    (сполучити (як-є world)
      (сполучити батько
        (сполучити журнал
          (сполучити метадані (як-є ())))))))

; D9:111001000 EMPTY-WORLD — root world contains three structural D3 NILs.
(0011 порожній-світ
  (0010 ()
    (створити-світ (як-є ()) (як-є ()) (як-є ()))))

; D9:111111000 WORLD-PARENT — second field of immutable world record.
(0011 світ-батько
  (0010 (світ) (перше (решта світ))))

; D9:111010100 WORLD-JOURNAL — third field of immutable world record.
(0011 світ-журнал
  (0010 (світ) (перше (решта (решта світ)))))

; D9:111000111 WORLD-METADATA — fourth field of immutable world record.
(0011 світ-метадані
  (0010 (світ) (перше (решта (решта (решта світ))))))

; D9:111111011 WORLD-RECORD — persistent journal prepend, parent retained.
(0011 світ-запис
  (0010 (світ подія)
    (створити-світ світ
      (сполучити подія (світ-журнал світ))
      (світ-метадані світ))))

; D9:101110011 CONTAINS-ATOM? — пошук атома в парному дереві знань.
; Усі рішення D1, обходи D3 CAR/CDR, EQ лише над атомним листком.
(0011 містить-атом?
  (0010 (шукане дерево)
    (110
      ((not? (атом? шукане)) #d1:0)
      ((атом? дерево) (тотожне? шукане дерево))
      (#d1:1
       (110
         ((містить-атом? шукане (перше дерево)) #d1:1)
         (#d1:1 (містить-атом? шукане (решта дерево))))))))

; D9:101111110 MILLISECONDS-FROM-NANOSECONDS.
; Числовий D24+ шлях; рівно мільйон наносекунд на мілісекунду.
; Від’ємний аргумент — помилка, жодного знакового або текстового посередника.
(0011 мілісекунди-з-наносекунди
  (0010 (наносекунди)
    (110
      ((менше? наносекунди #d24:000000000000000000000000) (100 (001 ())))
      (#d1:1 (quotient наносекунди #d24:000011110100001001000000)))))


; D8:10111010 LOGAND, D8:01011100 LOGIOR, D8:11011001 LOGXOR.
; research/d8-logand-logior-logxor-batch-2026-10-17.lisp.
; Точна невід'ємна D24+ арифметика; SENS-декомпозиція через mod/quotient.
; Це похідні визначення, не прямий допуск D8 машинних кодів.
(0011 побітове-і
  (0010 (ліве праве)
    (110
      ((нуль? ліве) #d24:000000000000000000000000)
      ((нуль? праве) #d24:000000000000000000000000)
      (#d1:1
        (додати
          (110
            ((нуль? (mod ліве #d24:000000000000000000000010)) #d24:000000000000000000000000)
            ((нуль? (mod праве #d24:000000000000000000000010)) #d24:000000000000000000000000)
            (#d1:1 #d24:000000000000000000000001))
          (помножити
            #d24:000000000000000000000010
            (побітове-і
              (quotient ліве #d24:000000000000000000000010)
              (quotient праве #d24:000000000000000000000010))))))))

(0011 побітове-або
  (0010 (ліве праве)
    (110
      ((нуль? ліве)
        (110
          ((нуль? праве) #d24:000000000000000000000000)
          (#d1:1
            (додати
              (110
                ((нуль? (mod ліве #d24:000000000000000000000010))
                  (mod праве #d24:000000000000000000000010))
                (#d1:1 #d24:000000000000000000000001))
              (помножити
                #d24:000000000000000000000010
                (побітове-або
                  (quotient ліве #d24:000000000000000000000010)
                  (quotient праве #d24:000000000000000000000010)))))))
      (#d1:1
        (додати
          (110
            ((нуль? (mod ліве #d24:000000000000000000000010))
              (mod праве #d24:000000000000000000000010))
            (#d1:1 #d24:000000000000000000000001))
          (помножити
            #d24:000000000000000000000010
            (побітове-або
              (quotient ліве #d24:000000000000000000000010)
              (quotient праве #d24:000000000000000000000010))))))))

(0011 побітове-виключне-або
  (0010 (ліве праве)
    (110
      ((нуль? ліве)
        (110
          ((нуль? праве) #d24:000000000000000000000000)
          (#d1:1
            (додати
              (110
                ((equal? (mod ліве #d24:000000000000000000000010) (mod праве #d24:000000000000000000000010))
                  #d24:000000000000000000000000)
                (#d1:1 #d24:000000000000000000000001))
              (помножити
                #d24:000000000000000000000010
                (побітове-виключне-або
                  (quotient ліве #d24:000000000000000000000010)
                  (quotient праве #d24:000000000000000000000010)))))))
      (#d1:1
        (додати
          (110
            ((equal? (mod ліве #d24:000000000000000000000010) (mod праве #d24:000000000000000000000010))
              #d24:000000000000000000000000)
            (#d1:1 #d24:000000000000000000000001))
          (помножити
            #d24:000000000000000000000010
            (побітове-виключне-або
              (quotient ліве #d24:000000000000000000000010)
              (quotient праве #d24:000000000000000000000010))))))))


; D9:001000101 APPEND-NEW — ратифікована композиція списків.
; research/d9-append-new-batch-2026-10-17.lisp
; Лівий префікс збережено; далі елементи правого списку, відсутні в лівому.
(0011 додати-нові
  (0010 (ліві праві)
    (append ліві
      (відсіяти
        (0010 (елемент)
          (not? (значення-у-списку? елемент ліві)))
        праві))))
(0011 append-new додати-нові)

; D9:111001011 WORLD-DEPTH — structural SENS depth, exact D24+.
; Paired result selection is an ordinary derived SENS closure; never LET
; lowering through a numeric 01010 call head or an unqualified number.
(0011 більша-глибина
  (0010 (ліва права)
    (110
      ((менше? ліва права) права)
      (#d1:1 ліва))))
(0011 світ-глибина
  (0010 (дерево)
    (110
      ((атом? дерево) #d24:000000000000000000000000)
      (#d1:1
        (збільшити-на-один
          (більша-глибина
            (світ-глибина (перше дерево))
            (світ-глибина (решта дерево))))))))
(0011 world-depth світ-глибина)


; D9 content-store algebra — derived SENS representation from lib/content-store.lisp.
; Immutable address/value alist: ((address . value) ...), D3:101 atom key identity.
; The lookup returns a singleton (value) on presence, () on absence;
; a stored () therefore remains distinguishable from an absent address.
; These language closures do not grant D9 direct value-call mechanisms.
; D9:000100001 EMPTY-CONTENT-STORE
(0011 порожній-вміст-сховище
  (0010 () (001 ())))

; D9:000010111 CONTENT-STORE-SIZE — D6 LENGTH's exact D24 numeric law.
(0011 вміст-сховище-розмір
  (0010 (сховище)
    (довжина сховище)))

; D9:000100000 CONTENT-STORE-GET — singleton value for found key, () if absent.
(0011 вміст-сховище-отримати
  (0010 (сховище адреса)
    (110
      ((0101 сховище) (001 ()))
      ((101 адреса (100 (100 сховище)))
       (1110 (011 (100 сховище))))
      (#d1:1 (вміст-сховище-отримати (011 сховище) адреса)))))

; D9:000011110 CONTENT-STORE-CONTAINS? — presence, never value truthiness.
(0011 вміст-сховище-містить?
  (0010 (сховище адреса)
    (110
      ((0101 сховище) #d1:0)
      ((101 адреса (100 (100 сховище))) #d1:1)
      (#d1:1 (вміст-сховище-містить? (011 сховище) адреса)))))

; D8:10110111 FLOOR, exact integer quotient rounded down.
; D8:01001100 TRUNCATE and D8:01000000 dividend-signed REM are the
; lower-domain proofs. When signs differ and REM != 0, FLOOR = TRUNC - 1.
(0011 округлити-вниз
  (0010 (ділене дільник)
    (за-умовою
      ((нуль? (остача-зі-знаком ділене дільник))
       (округлити-до-нуля ділене дільник))
      ((менше? ділене #d24:000000000000000000000000)
       (за-умовою
         ((менше? дільник #d24:000000000000000000000000)
          (округлити-до-нуля ділене дільник))
         (#d1:1
          (відняти (округлити-до-нуля ділене дільник) #d24:000000000000000000000001))))
      ((менше? дільник #d24:000000000000000000000000)
       (відняти (округлити-до-нуля ділене дільник) #d24:000000000000000000000001))
      (#d1:1 (округлити-до-нуля ділене дільник)))))

; D8:10110010 LOGNOT, infinite two's-complement arithmetic identity:
; for any admitted signed integer n, NOT(n) = -n - 1.
(0011 побітове-не
  (0010 (число)
    (відняти (змінити-знак число) #d24:000000000000000000000001)))


; D9:000010011 GUARD-REFERENCE-FIELD — tagged reference contains (field value).
; Match keys via established D5 ASSOC / structural equality; never D9 direct call.
; D9:000010011 — SENS-owned direct traversal of the tagged record fields.
; Avoid anonymous call-head lowering; shape (tag (field value) ...).
(0011 внутрішнє-поле-у-парах
  (0010 (поле пари)
    (110
      ((порожнє? пари) (як-є ()))
      ((equal? поле (перше (перше пари))) (п-р (перше пари)))
      (#d1:1 (внутрішнє-поле-у-парах поле (решта пари))))))
(0011 захист-еталон-поле
  (0010 (поле запис)
    (внутрішнє-поле-у-парах поле (решта запис))))


; D9:000001111 PROVENANCE-RULE from canonical (statement goal (source ...) (rule ...) ...).
(0011 походження-правило
  (0010 (запис)
    (захист-еталон-поле (як-є rule) (решта запис))))


; D9:000010110 PROVENANCE-GOAL is second cell of the canonical record.
(0011 походження-ціль
  (0010 (запис)
    (п-р запис)))


; D9:000011100 PROVENANCE-DERIVED-FROM: immutable proof children field.
(0011 походження-похідний-з
  (0010 (запис)
    (захист-еталон-поле (як-є derived-from) (решта запис))))


; D9:000101001 PROVENANCE-SOURCE: record's explicit evidence source field.
; D9:000101001 PROVENANCE-SOURCE: exact third field in the canonical
; (statement goal (source value) (rule ...) (derived-from ...)) record.
; `source` is a data-field label, not a callable/domain surface identity.
(0011 походження-джерело
  (0010 (запис)
    (п-р (перше (решта (решта запис))))))


; D9:000001000 GUARD-UNKNOWN-ROUTES — exact canonical routing choices from lib/guard.lisp.
; No runtime orchestration; routing remains an immutable SENS value.
(0011 захист-невідоме-маршрути
  (0010 ()
    (як-є
      (((route ask-agent)
        (when ecosystem-local-or-component-owned)
        (action ask-responsible-live-agent)
        (verify commit-or-artifact-or-direct-source))
       ((route ask-owner)
        (when authority-choice-intent-license-or-destructive-scope)
        (action ask-owner-explicitly)
        (verify owner-decision-record))
       ((route research-web)
        (when external-current-or-primary-source-needed)
        (action search-authoritative-external-sources)
        (verify citations-and-access-date))))))


; D9:000100100 MAKE-GUARD-FINDING — canonical record from lib/guard.lisp.
; Explicit allowed decision/evidence status, immutable SENS list fields.
(0011 створити-захист-висновок
  (0010 (вхідне-рішення вхідний-доказ-стан предмет стан контракт різниця вплив порада докази)
    (110
      ((хибне? (захист-рішення? вхідне-рішення))
       (список (як-є invalid-guard-decision) вхідне-рішення))
      ((хибне? (захист-доказ-стан? вхідний-доказ-стан))
       (список (як-є invalid-evidence-status) вхідний-доказ-стан))
      (#d1:1
       (список
         (як-є guard-finding)
         (список (як-є schema) (як-є guard/1))
         (список (як-є decision) вхідне-рішення)
         (список (як-є evidence-status) вхідний-доказ-стан)
         (список (як-є subject) предмет)
         (список (як-є state) стан)
         (список (як-є contract) контракт)
         (список (як-є difference) різниця)
         (список (як-є impact) вплив)
         (список (як-є guidance) порада)
         (список (як-є evidence) докази)
         (список (як-є unknown-routes)
           (110
             ((101 вхідне-рішення (як-є unknown))
              (захист-невідоме-маршрути))
             (#d1:1 (як-є ())))))))))

; D9:000110110 GUARD-COMPARE — pure SENS projection of lib/guard.lisp.
; Existing structural EQUAL decides, D9 MAKE-GUARD-FINDING builds the record.
(0011 захист-порівняти
  (0010 (предмет очікуване спостережене докази)
    (110
      ((equal? очікуване спостережене)
       (створити-захист-висновок
         (як-є allow) (як-є confirmed) предмет спостережене очікуване
         (як-є ()) (як-є invariant-preserved) (як-є no-action) докази))
      (#d1:1
       (створити-захист-висновок
         (як-є warn) (як-є confirmed) предмет спостережене очікуване
         (список (як-є expected) очікуване (як-є observed) спостережене)
         (як-є contract-drift)
         (як-є reconcile-observation-with-contract) докази)))))

; D9:000000110 GUARD-UNKNOWN — preserve explicit missing evidence,
; and classify unknown as a routable epistemic state, not silent reject.
; The record layout is ratified from lib/guard.lisp make-guard-finding.
(0011 захист-невідоме
  (0010 (предмет відсутні-докази порада)
    (список
      (як-є guard-finding)
      (список (як-є schema) (як-є guard/1))
      (список (як-є decision) (як-є unknown))
      (список (як-є evidence-status) (як-є unresolved))
      (список (як-є subject) предмет)
      (список (як-є state) (як-є not-observed))
      (список (як-є contract) (як-є insufficient-evidence))
      (список (як-є difference) відсутні-докази)
      (список (як-є impact) (як-є decision-not-earned))
      (список (як-є guidance) порада)
      (список (як-є evidence) (як-є ()))
      (список (як-є unknown-routes) (захист-невідоме-маршрути)))))

; D9:010111110 CANON-CONFORMS? — executable exact eleven-law aggregate.
; lib/canon.lisp is the semantic donor. Existing D1 property laws are
; projected into the canonical explicit three-field status record in SENS.
(0011 канон-запис-д1-ознаки
  (0010 (закон ознака)
    (за-умовою
      (ознака (канон-закон-виконаний закон))
      (#d1:1 (канон-закон-порушений закон)))))

(0011 канон-відповідає?
  (0010 ()
    (канон-відповідність-з
      (список
        (канон-закон-порожній-список)
        (канон-запис-д1-ознаки (як-є atom-cons)
          (канон-закон-атом-пара (як-є x) (як-є y)))
        (канон-запис-д1-ознаки (як-є car-cons)
          (канон-закон-перше-пара (як-є x) (як-є y)))
        (канон-запис-д1-ознаки (як-є cdr-cons)
          (канон-закон-решта-пара (як-є x) (як-є y)))
        (канон-запис-д1-ознаки (як-є eq-reflexive-atom)
          (канон-закон-рівність-рефлексивний-атом (як-є x)))
        (канон-запис-д1-ознаки (як-є cdr-dotted)
          (канон-закон-решта-крапковий (як-є x) (як-є y)))
        (канон-запис-д1-ознаки (як-є cdr-proper)
          (канон-закон-решта-правильний (як-є x)
            (список (як-є y))))
        (канон-запис-д1-ознаки (як-є cdr-improper)
          (канон-закон-решта-неправильний (як-є x) (як-є y)))
        (канон-закон-цитування-пригнічує-обчислення)
        (канон-закон-умова-перший-збіг-короткий-ланцюг)
        (канон-закон-символьний-поверхня)))))
; D6:110101 MIN and D6:110111 MAX — proper variadic SENS projections.
; A required first argument guarantees the original D6 arity boundary.
; Exactly qualified D24+ comparisons occur in existing D6 list reducers.
(0011 найменше
  (0010 (перше-значення . решта-значень)
    (найменше-у-списку (сполучити перше-значення решта-значень))))
(0011 найбільше
  (0010 (перше-значення . решта-значень)
    (найбільше-у-списку (сполучити перше-значення решта-значень))))


; D9:111111010 WORLD? — exactly (world parent journal metadata),
; recovered from lib/world.lisp. No mutable host object or host predicate.
(0011 світ?
  (0010 (значення)
    (за-умовою
      ((атом? значення) #d1:0)
      ((equal? (перше значення) (як-є world))
        (за-умовою
          ((атом? (решта значення)) #d1:0)
          ((атом? (решта (решта значення))) #d1:0)
          ((атом? (решта (решта (решта значення)))) #d1:0)
          (#d1:1 (порожнє?
            (решта (решта (решта (решта значення))))))))
      (#d1:1 #d1:0))))

; D9 world donor: filter newest-first tell/retract events by module.
; Events have the ratified (operation module clause) list form.
(0011 внутрішні-події-модуля
  (0010 (модуль події)
    (за-умовою
      ((порожнє? події) (як-є ()))
      ((атом? події) (як-є ()))
      ((тотожне? (п-р (перше події)) модуль)
        (сполучити (перше події)
          (внутрішні-події-модуля модуль (решта події))))
      (#d1:1 (внутрішні-події-модуля модуль (решта події))))))

; D9:111100100 WORLD-MODULE-EVENTS. Persistent journal is unmodified.
(0011 світ-модуль-події
  (0010 (світ модуль)
    (внутрішні-події-модуля модуль (світ-журнал світ))))

; D9:111100000 WORLD-MODULE-KNOWN? — only a nonempty pair event stream
; establishes existence; D1:NO is never silently coerced from ().
(0011 світ-модуль-відомий?
  (0010 (світ модуль)
    (хибне? (атом? (світ-модуль-події світ модуль)))))


; D9:111010101 WORLD-TELL — a new immutable world with a tell-event.
; Event identity and order are inherited from lib/world.lisp.
(0011 світ-повідомити
  (0010 (світ модуль клауза)
    (світ-запис світ (список (як-є tell) модуль клауза))))

; D9:111001010 WORLD-RETRACT — record retraction, do not mutate parent.
(0011 світ-відкликати
  (0010 (світ модуль клауза)
    (світ-запис світ (список (як-є retract) модуль клауза))))


; D9 WORLD-CLAUSES donor (lib/world.lisp), pure chronological event fold.
; The journal is newest-first; fold oldest to newest without mutating worlds.
(0011 внутрішній-зворот-подій
  (0010 (події акумулятор)
    (за-умовою
      ((порожнє? події) акумулятор)
      ((атом? події) акумулятор)
      (#d1:1 (внутрішній-зворот-подій
        (решта події) (сполучити (перше події) акумулятор))))))

; Retract only the first structurally identical active clause.
(0011 внутрішній-вилучити-клаузу
  (0010 (клауза клаузи)
    (за-умовою
      ((порожнє? клаузи) (як-є ()))
      ((equal? клауза (перше клаузи)) (решта клаузи))
      (#d1:1
        (сполучити (перше клаузи)
          (внутрішній-вилучити-клаузу клауза (решта клаузи)))))))

; Historical event shape is (tell|retract module clause). Unknown kinds
; preserve state: no new host case, no implicit opcode admission.
(0011 внутрішньо-застосувати-подію
  (0010 (клаузи подія)
    (за-умовою
      ((тотожне? (перше подія) (як-є tell))
        (сполучити (перше (решта (решта подія))) клаузи))
      ((тотожне? (перше подія) (як-є retract))
        (внутрішній-вилучити-клаузу
          (перше (решта (решта подія))) клаузи))
      (#d1:1 клаузи))))

(0011 внутрішнє-згортання-подій
  (0010 (події клаузи)
    (за-умовою
      ((порожнє? події) клаузи)
      ((атом? події) клаузи)
      (#d1:1
        (внутрішнє-згортання-подій
          (решта події)
          (внутрішньо-застосувати-подію клаузи (перше події)))))))

; D9:111010110 WORLD-CLAUSES. Project currently asserted clauses for one
; module from immutable journal, respecting tell/retract event order.
(0011 світ-клаузи
  (0010 (світ модуль)
    (внутрішнє-згортання-подій
      (внутрішній-зворот-подій
        (світ-модуль-події світ модуль) (як-є ()))
      (як-є ()))))


; D9/D10 batch — 17.10.2026, owned semantic bodies (no direct D9/D10 dispatch).
; D9:010011101 JUSTIFIED-MEMBER? — ратифікована проєкція членства.
; Джерело: research/d9-justified-member-remove-batch-2026-10-17.lisp.
(0011 обґрунтований-член?
  (0010 (факт записи)
    (110
      ((0101 записи) #d1:0)
      ((equal? факт (100 (100 записи))) #d1:1)
      (#d1:1 (обґрунтований-член? факт (011 записи))))))

; D9:010101001 REMOVE-JUSTIFIED — незмінний список, усі рівні елементи вилучено.
(0011 видалити-обґрунтований
  (0010 (факт записи)
    (відсіяти
      (0010 (запис)
        (not? (equal? факт (100 запис))))
      записи)))

; D9:001111010 MAKE-JUSTIFIED — факт та його список підтримок.
; Джерело: research/d9-justified-vec-arglist-batch-2026-10-17.lisp.
(0011 створити-обґрунтований
  (0010 (факт підтримки)
    (сполучити факт підтримки)))

; D9:001111011 AXIOM — native historical TMS axiom (fact . NIL).
; Law from lib/forward.lisp; exact D3 empty is data, no D9 direct opcode.
(0011 аксіома
  (0010 (факт)
    (створити-обґрунтований факт (001 ()))))


; D9:010101011 FACT-OF / D9:010001010 SUPPORTS-OF.
; Донор lib/forward.lisp: TMS-запис (fact . supports), не W8 і не масив.
; CAR/CDR точно D3:100/011; відсутній запис відхиляє D3 типом.
(0011 факт-від
  (0010 (запис) (100 запис)))
(0011 підтримки-від
  (0010 (запис) (011 запис)))

; D9:010011001 MAP-FACT-OF — рекурсивна проєкція фактів без зміни порядку.
; Власне SENS-визначення, не прямий D9 value-call.
(0011 мапа-факт-від
  (0010 (записи)
    (110
      ((0101 записи) (001 ()))
      ((010 (001 ()))
       (111 (факт-від (100 записи))
            (мапа-факт-від (011 записи)))))))

; D9:001110000 PRUNE-JUSTIFICATIONS — зберігаємо тільки факти,
; у яких другий компонент (список доказів) непорожній.
; Важливо: (решта пара) — одноелементний список, а не сама підтримка.
(0011 обрізати-обґрунтування
  (0010 (факти)
    (відсіяти
      (0010 (пара)
        (not? (0101 (011 пара))))
      факти)))

; D9:010010011 JUSTIFICATIONS-OF, D9:101000000 ADD-JUSTIFICATION.
; D9:101111011 VEC-FROM-LIST, D9:110001111 ARGLIST,
; D9:110011010 NUMERIC-BUFFER-LENGTH.
; Дослідження: research/d9-justified-vec-arglist-batch-2026-10-17.lisp.
; Механізми належать SENS DEFINE, це не дозвіл на прямий D9 opcode.
(0011 обґрунтування-від
  (0010 (ключ мапа)
    (мапа-отримати ключ мапа)))

(0011 додати-обґрунтування
  (0010 (ключ підтримка мапа)
    (мапа-вставити ключ підтримка мапа)))

; Вектор і arglist поки представляються списком: без нового host-vector.
(0011 вектор-з-список
  (0010 (елементи) елементи))

(0011 аргументи
  (0010 (елементи) елементи))

(0011 числовий-буфер-довжина
  (0010 (буфер) (довжина буфер)))

; D10:0000000111 NUMERIC-NOT-EQUAL — заперечення точного
; числового D9:110100101; не структурна рівність різних доменів.
; Джерело: research/d10-d9-noteq-vector-lint-batch-2026-10-17.lisp.
(0011 числа-нерівні?
  (0010 (ліве праве)
    (not? (числовий-рівність ліве праве))))


; D10:0011001000 FIND-ALL (PAIP auxfns.lisp@2db2ba9).
; Keep every matching list element, preserving order and repetitions.
; Default D8 EQL identity; optional supplied binary D1 predicate is the
; language projection of the donor's :test law (no host keyword registry).
(0011 знайти-усі
  (0010 (зразок елементи . способи)
    (110
      ((0101 способи)
       (відсіяти
         (0010 (елемент) (тотожне-значення? зразок елемент))
         елементи))
      (#d1:1
       (відсіяти
         (0010 (елемент) ((100 способи) зразок елемент))
         елементи)))))


; D10:0011011000 UNIQUE-FIND-IF-ANYWHERE (PAIP auxfns.lisp@2db2ba9).
; Only leaves are tested. Visit CDR before CAR, ADJOIN matching CAR at
; the front, yielding first-occurrence order without duplicate leaves.
; Optional third list is the donor's found-so-far accumulator.
(0011 знайти-єдиний-вкладений
  (0010 (умова дерево . попередні)
    ((0010 (знайдене)
       (110
         ((010 дерево)
          (110
            ((умова дерево)
             (приєднати-якщо-нема дерево знайдене))
            (#d1:1 знайдене)))
         (#d1:1
          (знайти-єдиний-вкладений
            умова (100 дерево)
            (знайти-єдиний-вкладений умова (011 дерево) знайдене)))))
     (110
       ((0101 попередні) (001 ()))
       (#d1:1 (100 попередні))))))

; D10:0011001111 PARTITION-IF, derived from pinned PAIP auxfns.lisp.
; PAIP returns two Common Lisp values; the SENS projection is an explicit list
; (selected rejected). Every source item is tested once; both partitions retain order.
; Research-derived library helper only; no direct D10 opcode or F1-F4 admission.
(0011 розділити-за-умовою-до
  (0010 (предикат елементи так ні)
    (110
      ((порожнє? елементи)
       (список (зворот так) (зворот ні)))
      ((предикат (перше елементи))
       (розділити-за-умовою-до предикат (решта елементи)
         (сполучити (перше елементи) так) ні))
      (#d1:1
       (розділити-за-умовою-до предикат (решта елементи)
         так (сполучити (перше елементи) ні))))))
(0011 розділити-за-умовою
  (0010 (предикат елементи)
    (розділити-за-умовою-до предикат елементи (як-є ()) (як-є ()))))

; D8 admitted mechanism projections; names are Ukrainian surfaces, not new authority.
; Exact width D8:11100000 -> D24 CHAR-CODE, D8:11101101/11101110 -> names.
; Mechanisms already exist in SENS evaluator, never re-route via historical SID8.
(0011 код-символу
  (0010 (знак)
    (11100000 знак)))
(0011 текст-у-символ
  (0010 (текст)
    (11101101 текст)))
(0011 символ-у-текст
  (0010 (значення)
    (11101110 значення)))


; D9:010101110 DROP-UNSUPPORTED: стабільний відбір доказових пар.
; Формат елемента — (ключ . D1-ознака), підтримка лише точно D1:1.
; Джерело: research/d9-justified-member-remove-batch-2026-10-17.lisp.
(0011 відкинути-непідтримані
  (0010 (пари)
    (відсіяти
      (0010 (пара)
        (equal? (решта пара) #d1:1))
      пари)))

; D9:001100001 LINT-SIZE: довжина матеріалізованого списку
; в явно кваліфікованому D24, без схованого лічильника.
; Джерело: research/d10-d9-noteq-vector-lint-batch-2026-10-17.lisp.
(0011 аналіз-розмір довжина)


; Партія D9/D10 із ратифікованих історичних досліджень, тільки SENS.
; D9:010010001 ADD-NEW-JUSTIFIED — той самий бездубльовий append-new.
(0011 додати-нові-обґрунтований
  (0010 (нові записи)
    (110
      ((0101 нові) записи)
      ((обґрунтований-член? (100 (100 нові)) записи)
       (додати-нові-обґрунтований (011 нові) записи))
      (#d1:1
       (додати-нові-обґрунтований
         (011 нові) (111 (100 нові) записи))))))

; D10:0010001110 KNOWLEDGE-PROPER-LIST? — harvested from lib/knowledge.lisp.
; The entire CDR spine must terminate in D3:000, not an arbitrary atom.
; Exact D1 result, no implicit truthiness or D10 opcode admission.
(0011 правильний-список-знань?
  (0010 (значення)
    (110
      ((0101 значення) #d1:1)
      ((010 значення) #d1:0)
      (#d1:1 (правильний-список-знань? (011 значення))))))

; D10:0010010110 RESULT-PROPER-LIST? — same structural law,
; independently located in lib/result-status.lisp.
(0011 правильний-список-результатів? правильний-список-знань?)

; D10:0000000001 RESULT-COUNT: матеріалізовані результати як правильний список.
(0011 кількість-результатів довжина)

; D10:0001001001 FORALL-EVERY-CANDIDATE-SATISFIES.
; Native SENS recursion over exact D1 predicate bits: empty=YES,
; first NO stops; later candidates are evaluated only after preceding YES.
; The predicate is an evaluated callable value, not a macro/code head.
(0011 кожен-задовольняє?
  (0010 (перевірка кандидати)
    (110
      ((0101 кандидати) #d1:1)
      ((перевірка (100 кандидати))
       (кожен-задовольняє? перевірка (011 кандидати)))
      (#d1:1 #d1:0))))


; D9:110101000 STRING-CONTAINS? — substring search, SENS-owned recursion.
; D9:110101010 takes (prefix string); both empty and rest are exact D9.
; Empty needle is included, non-string carriers fail in admitted D9 mechanisms.
; This is a derived SENS definition, not a new direct D9 value-call mechanism.
(0011 рядок-містить?
  (0010 (рядок голка)
    (110
      ((110101010 голка рядок) #d1:1)
      ((110011100 рядок) #d1:0)
      (#d1:1 (рядок-містить? (110011101 рядок) голка)))))


; D9:000111011 TRANSLATION-EVIDENCE-WORTHY?.
; Donor: lib/translation.lisp (rejected|ambiguous valid reviews are
; evidence; accepted reviews never create a rejection/ambiguity journal).
; This is pure D3/D4/D5 structure with exact D1 verdicts, not D9 opcode.
(0011 переклад-доказ-вартий?
  (0010 (перевірка)
    (110
      ((010 перевірка) #d1:0)
      ((not? (010 (100 перевірка))) #d1:0)
      ((not? (101 (100 перевірка) (001 translation-review/1))) #d1:0)
      ((not? (equal? (довжина перевірка) #d24:000000000000000000000101)) #d1:0)
      ((not? (010 (переклад-перевірка-стан перевірка))) #d1:0)
      ((not? (010 (переклад-перевірка-код перевірка))) #d1:0)
      ((101 (переклад-перевірка-стан перевірка) (001 rejected)) #d1:1)
      ((101 (переклад-перевірка-стан перевірка) (001 ambiguous)) #d1:1)
      (#d1:1 #d1:0))))


; D9:000000011 TRANSLATION-EVIDENCE-ENTRY:
; exact (translation-evidence/1 REVIEW) pair of SENS list data.
(0011 переклад-доказ-запис
  (0010 (перевірка)
    (111 (001 translation-evidence/1)
         (111 перевірка (001 ())))))


; D9:000001110 TRANSLATION-EVIDENCE-NEXT:
; immutable journal cons only when the reviewed outcome is worthy.
(0011 переклад-доказ-наступний
  (0010 (перевірка журнал)
    (110
      ((переклад-доказ-вартий? перевірка)
       (111 (переклад-доказ-запис перевірка) журнал))
      (#d1:1 журнал))))
; D9:111011111 WORLD-AT-DEPTH, D9:111101010 WORLD-COMMON-ANCESTOR.
; Donor lib/world.lisp: history generations != generic tree-depth.
; No direct D9 opcode or host-side semantics: exact D24 and D1 only.
(0011 внутрішня-глибина-поколінь
  (0010 (світ)
    (за-умовою
      ((порожнє? (світ-батько світ)) #d24:000000000000000000000000)
      (#d1:1 (збільшити-на-один
        (внутрішня-глибина-поколінь (світ-батько світ)))))))

(0011 внутрішній-світ-на-глибині
  (0010 (світ поточна-глибина цільова-глибина)
    (за-умовою
      ((equal? поточна-глибина цільова-глибина) світ)
      ((порожнє? (світ-батько світ)) (як-є World-not-found))
      (#d1:1 (внутрішній-світ-на-глибині
        (світ-батько світ)
        (відняти поточна-глибина #d24:000000000000000000000001)
        цільова-глибина)))))

(0011 світ-у-глибина
  (0010 (світ цільова-глибина)
    (за-умовою
      ((хибне? (світ? світ)) (як-є World-not-found))
      ((менше? цільова-глибина #d24:000000000000000000000000) (як-є World-not-found))
      (#d1:1 (внутрішній-світ-на-глибині
        світ (внутрішня-глибина-поколінь світ) цільова-глибина)))))

(0011 внутрішній-предок-світу?
  (0010 (кандидат світ)
    (за-умовою
      ((хибне? (світ? світ)) #d1:0)
      ((equal? кандидат світ) #d1:1)
      ((порожнє? (світ-батько світ)) #d1:0)
      (#d1:1 (внутрішній-предок-світу? кандидат (світ-батько світ))))))

(0011 світ-спільний-предок
  (0010 (лівий правий)
    (за-умовою
      ((хибне? (світ? лівий)) (як-є World-no-common-ancestor))
      ((хибне? (світ? правий)) (як-є World-no-common-ancestor))
      ((внутрішній-предок-світу? лівий правий) лівий)
      ((порожнє? (світ-батько лівий))
        (як-є World-no-common-ancestor))
      (#d1:1 (світ-спільний-предок (світ-батько лівий) правий)))))


; Internal donor helper: finite D3 proper-list check, exact D1 only.
(0011 результат-правильний-список?
  (0010 (значення)
    (110
      ((010 значення) (101 значення (001 ())))
      (#d1:1 (результат-правильний-список? (011 значення))))))


; Internal donor helper: the two quoted negation heads are data symbols.
(0011 результат-голова-заперечення?
  (0010 (голова)
    (110
      ((101 голова (001 not?)) #d1:1)
      ((101 голова (001 not)) #d1:1)
      (#d1:1 #d1:0))))


; D9:000011101 RESULT-GOAL? · lib/result-status.lisp.
; Ordinary goal: proper nonempty list with a symbol head.
; Negation is unary (not? nested-goal), recursively validated.
(0011 результат-ціль?
  (0010 (ціль)
    (110
      ((010 ціль) #d1:0)
      ((not? (результат-правильний-список? ціль)) #d1:0)
      ((not? (результат-символ? (100 ціль))) #d1:0)
      ((результат-голова-заперечення? (100 ціль))
       (110
         ((010 (011 ціль)) #d1:0)
         ((not? (010 (011 (011 ціль)))) #d1:0)
         (#d1:1 (результат-ціль? (100 (011 ціль))))))
      (#d1:1 #d1:1))))


; D9:000111010 RESULT-NEGATED-GOAL? · exact one-bit classification.
(0011 результат-заперечений-ціль?
  (0010 (ціль)
    (110
      ((not? (результат-ціль? ціль)) #d1:0)
      ((результат-голова-заперечення? (100 ціль)) #d1:1)
      (#d1:1 #d1:0))))


; D9:000111110 RESULT-OPPOSITE-GOAL: involution on valid goals.
(0011 результат-протилежний-ціль
  (0010 (ціль)
    (110
      ((результат-заперечений-ціль? ціль) (100 (011 ціль)))
      (#d1:1 (111 (001 not?) (111 ціль (001 ())))))))
; D9:111010010 SCIENTIFIC-CONSTANT-STATUS and D9:111110010 STATUS-VALID?.
; Exact language donor: lib/quantity.lisp — a seven-slot immutable record
; (scientific-constant/1 name quantity status kind system source).
; Status admits exact-by-definition and measured; physical-derived is a KIND,
; not a third status. All predicate results are strict D1 width-one words.
(0011 науковий-константа-стан
  (0010 (константа)
    (перше (решта (решта (решта константа))))))

(0011 науковий-константа-стан-чинний?
  (0010 (стан)
    (за-умовою
      ((хибне? (атом? стан)) #d1:0)
      ((тотожне? стан (як-є exact-by-definition)) #d1:1)
      ((тотожне? стан (як-є measured)) #d1:1)
      (#d1:1 #d1:0))))


; Local derived type check used by D9 RESULT-GOAL?, not an admitted
; D9:110101100 machine call; language-owned SYMBOL? already exists in Core4.
; Local SENS-only SYMBOL? predicate, borrowed from lib/world.lisp.
; D8:11110100 serializes an atom; D8:11101101 restores its symbol name.
; Do not call non-admitted D9:110101100 or missing English compatibility names.
(0011 результат-символ?
  (0010 (значення)
    (110
      ((0101 значення) #d1:0)
      ((not? (010 значення)) #d1:0)
      ((101 значення (11101101 (11110100 значення))) #d1:1)
      (#d1:1 #d1:0))))

; D9 exact text surfaces: language projections over already admitted W9
; identities. No new opcode, arithmetic conversion, or D9 registry.
; D9:110011100 STRING-EMPTY? / D9:110011101 STRING-REST.
(0011 рядок-порожній?
  (0010 (текст)
    (110011100 текст)))

(0011 рядок-решта
  (0010 (текст)
    (110011101 текст)))

; D9:110101010 STRING-PREFIX? (prefix first) / D9:110101011 STRING-FIRST.
(0011 рядок-префікс?
  (0010 (префікс текст)
    (110101010 префікс текст)))

(0011 рядок-перший
  (0010 (текст)
    (110101011 текст)))

; D8:00100100 VALUES-LIST. У SENS список уже є точним носієм набору
; повернених значень. Це проєкція над існуючим носієм, не host multiple values.
; research/d8-lsh-values-list-quotient-batch-2026-10-17.lisp.
(0011 значення-списком
  (0010 (значення) значення))

; D9:101101001 APPLY-SUBST: точна структурна підстановка D5:11111.
; research/d9-nunion-subst-depth-batch-2026-10-17.lisp.
(0011 застосувати-підстановка замінити)


; D10:0001100010 MEMQ — original atom-only EQ membership returns matching tail.
; This is a language-defined D10 surface; no direct D10 call mechanism.
(0011 входження-eq
  (0010 (шукане елементи)
    (110
      ((0101 елементи) (001 ()))
      ((101 шукане (100 елементи)) елементи)
      (#d1:1 (входження-eq шукане (011 елементи))))))

; D10:0001011001 SASSQ — atom-key EQ lookup with zero-arg fallback on miss.
; Fallthrough callback is invoked only after list exhaustion.
(0011 асоціація-eq
  (0010 (ключ асоціації запасна-дія)
    (110
      ((0101 асоціації) (запасна-дія))
      ((101 ключ (100 (100 асоціації))) (100 асоціації))
      (#d1:1 (асоціація-eq ключ (011 асоціації) запасна-дія)))))

; D9:100000000 п-п-п-п-п-п-п — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CAR:100.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-п-п-п
  (0010 (значення)
    (п-п-п-п-п-п (100 значення))))

; D9:100000001 п-п-п-п-п-п-р — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CDR:011.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-п-п-р
  (0010 (значення)
    (п-п-п-п-п-п (011 значення))))

; D9:100000010 п-п-п-п-п-р-п — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CAR:100.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-п-р-п
  (0010 (значення)
    (п-п-п-п-п-р (100 значення))))

; D9:100000011 п-п-п-п-п-р-р — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CDR:011.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-п-р-р
  (0010 (значення)
    (п-п-п-п-п-р (011 значення))))

; D9:100000100 п-п-п-п-р-п-п — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CAR:100.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-р-п-п
  (0010 (значення)
    (п-п-п-п-р-п (100 значення))))

; D9:100000101 п-п-п-п-р-п-р — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CDR:011.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-р-п-р
  (0010 (значення)
    (п-п-п-п-р-п (011 значення))))

; D9:100000110 п-п-п-п-р-р-п — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CAR:100.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-р-р-п
  (0010 (значення)
    (п-п-п-п-р-р (100 значення))))

; D9:100000111 п-п-п-п-р-р-р — ratified seven-step selector,
; composition of proven six-step D8 selector and exact D3 CDR:011.
; No new direct D9 machine-call mechanism.
(0011 п-п-п-п-р-р-р
  (0010 (значення)
    (п-п-п-п-р-р (011 значення))))

; D9:101011101 VEC-CONJ: дописати один елемент у список-носій вектора.
; Жодної неявної конверсії між різними машинними носіями.
; research/d9-string-vec-conj-batch-2026-10-17.lisp
(0011 вектор-додати
  (0010 (вектор елемент)
    (append вектор (list елемент))))

; D9:001011100 DEPENDENTS-OF: читання з асоціативної мапи SENS;
; закон проєкції над D9:101100101 MAP-GET, не host-регістр.
; research/d10-d9-noteq-vector-lint-batch-2026-10-17.lisp
(0011 залежні-від
  (0010 (факт записи)
    (110
      ((0101 записи) (001 ()))
      ((значення-у-списку? факт (011 (100 записи)))
       (111 (100 (100 записи))
            (залежні-від факт (011 записи))))
      (#d1:1 (залежні-від факт (011 записи))))))

; D9:100001000 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-п-п-п
  (0010 (значення)
    (п-п-п-р-п-п (100 значення))))

; D9:100001001 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-п-п-р
  (0010 (значення)
    (п-п-п-р-п-п (011 значення))))

; D9:100001010 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-п-р-п
  (0010 (значення)
    (п-п-п-р-п-р (100 значення))))

; D9:100001011 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-п-р-р
  (0010 (значення)
    (п-п-п-р-п-р (011 значення))))

; D9:100001100 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-р-п-п
  (0010 (значення)
    (п-п-п-р-р-п (100 значення))))

; D9:100001101 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-р-п-р
  (0010 (значення)
    (п-п-п-р-р-п (011 значення))))

; D9:100001110 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-р-р-п
  (0010 (значення)
    (п-п-п-р-р-р (100 значення))))

; D9:100001111 exact seven-step CAR/CDR path, composed over ratified six-step D8.
(0011 п-п-п-р-р-р-р
  (0010 (значення)
    (п-п-п-р-р-р (011 значення))))

; D9:111110000 WORLD-ADDRESS-CONTENT, exact immutable projection from lib/world.lisp.
; Complete journal plus metadata, independent of parent; structural key, not hash.
(0011 світ-адреса-вміст
  (0010 (світ)
    (список (як-є world-history) (світ-журнал світ) (світ-метадані світ))))

; D9:111000000 ANSWER-ATOM, lifted D1 answer from lib/core.lisp.
; Empty list has no atom/pair verdict, atom is (D1:1), pair is (D1:0).
; Do not quote text digits or coerce D1 values through D7.
(0011 відповідь-атом
  (0010 (значення)
    (за-умовою
      ((порожнє? значення) (як-є ()))
      ((атом? значення) (список #d1:1))
      (#d1:1 (список #d1:0)))))

; D9:110110001 ANSWER-EQ, exactly D3 atomic equality lifted to answer value.
; Non-atomic carriers inherit the strict D3 EQ rejection.
(0011 відповідь-рівність
  (0010 (ліве праве)
    (список (тотожне? ліве праве))))

; Recovery of exact SENS D8-D9/D10 functions after concurrent whole-file T5M replacement.
; Original verified definitions from main@4f72ee8; no machine opcode admission.
(0011 науковий-константа-вид-чинний?
  (0010 (вид)
    (за-умовою
      ((хибне? (атом? вид)) #d1:0)
      ((тотожне? вид (як-є physical-defining)) #d1:1)
      ((тотожне? вид (як-є physical-derived)) #d1:1)
      (#d1:1 #d1:0))))

(0011 створити-науковий-константа
  (0010 (ім'я величина стан вид система джерело)
    (список (як-є scientific-constant/1) ім'я величина стан вид система джерело)))

(0011 науковий-константа-ім'я
  (0010 (константа) (перше (решта константа))))

(0011 науковий-константа-величина
  (0010 (константа) (перше (решта (решта константа)))))

(0011 науковий-константа-значення
  (0010 (константа) (перше (решта (науковий-константа-величина константа)))))

(0011 науковий-константа-одиниця
  (0010 (константа) (перше (решта (решта (науковий-константа-величина константа))))))

(0011 науковий-константа-вид
  (0010 (константа) (перше (решта (решта (решта (решта константа)))))))

(0011 науковий-константа-система
  (0010 (константа) (перше (решта (решта (решта (решта (решта константа))))))))

(0011 науковий-константа-джерело
  (0010 (константа) (перше (решта (решта (решта (решта (решта (решта константа)))))))))

(0011 копіювати-структуру
  (0010 (дерево)
    (110
      ((атом? дерево) дерево)
      (#d1:1
       (сполучити
         (копіювати-структуру (перше дерево))
         (копіювати-структуру (решта дерево)))))))

(0011 арифметично-зсунути арифметичний-зсув)

(0011 зріз-вектора підпослідовність)

(0011 список-усіх-значень значення-списком)


; D9:001010000 FS-OBJECTS / 010000001 FS-BINDINGS / 010010101 FS-REVISION.
; Похідні структурні проєкції чинної immutable-FS форми з lib/lisp-fs.lisp:
; (objects bindings revision). D3 CAR, D4 CADR, D5 CADDR — тільки SENS.
; Не надають нової прямої D9 callable identity та не змінюють FS storage law.
(0011 фс-об'єкти
  (0010 (знімок) (100 знімок)))
(0011 фс-зв'язки
  (0010 (знімок) (1001 знімок)))
(0011 фс-ревізія
  (0010 (знімок) (10011 знімок)))


; Партія визначень D8/D9: виконувані SENS-поверхні з ратифікованих доменів.
; D8:11110101 AND і D8:11111100 OR — вже мовні макроси and/or.
; Семантика короткого замикання зберігається як спільний макрооб'єкт;
; D8-код тут НЕ оголошує самостійну машинну callability.
(0011 та and)
(0011 або or)

; D9:110110101 FIFTH — чиста композиція D3:CAR/CDR;
; послідовність: CDR CDR CDR CDR CAR (п'ятий елемент).
(0011 п'ятий
  (0010 (значення)
    (перше (решта (решта (решта (решта значення)))))))

; Партія D8: дослідження research/d8-partial-tailp-lcm-push-batch-2026-10-17.lisp.
; D8:00011010 PARTIAL — повторне використання чинного D6 CURRY.
; Не дублювати вже визначене застосувати-префікс.
(0011 partial застосувати-префікс)

; D8:01010110 TAILP — структурний збіг із CDR-суфіксом.
; ЦЕ НЕ тотожність адрес конс-комірок (D3 EQ приймає тільки атоми).
; На цьому кроці допускається лише мовний structural-tail закон.
(0011 спільний-хвіст?
  (0010 (хвіст послідовність)
    (110
      ((equal? хвіст послідовність) #d1:1)
      ((0101 послідовність) #d1:0)
      ((010 послідовність) #d1:0)
      (#d1:1 (спільний-хвіст? хвіст (011 послідовність))))))
(0011 tailp? спільний-хвіст?)

; D8:01000110 PUSH: чиста побудова CONS без руйнування джерела.
; Відсутню мутацію Common Lisp PUSH не видавати за реалізовану.
(0011 додати-на-початок
  (0010 (значення список)
    (111 значення список)))

; D8:10111100 POP: чисте вилучення голови шляхом CDR.
; Відсутню мутацію Common Lisp POP не видавати за реалізовану.
(0011 зняти-з-початку
  (0010 (список)
    (011 список)))


; D9 CLIPS semantic projections from lib/clips-import.lisp.
; D9:001100011 CLIPS-SLOT-NAME; D9:001110111 CLIPS-SLOT-NAMES;
; D9:001100110 CLIPS-DEFTEMPLATE-SLOTS; D9:010111000 CLIPS-FACT-CLAUSE.
; Only SENS D3/D4 structural laws; no host parser or direct D9 call admission.
(0011 clips-слот-ім'я
  (0010 (поле)
    (1001 поле)))

(0011 clips-слот-імена
  (0010 (поля)
    (110
      ((0101 поля) (001 ()))
      (#d1:1
       (111 (clips-слот-ім'я (100 поля))
            (clips-слот-імена (011 поля)))))))

(0011 clips-deftemplate-слоти
  (0010 (форма)
    (clips-слот-імена (0111 форма))))

(0011 clips-факт-клауза
  (0010 (факт)
    (1110 факт)))

; D9:001010100 FS-OBJECT-ADDRESSES: immutable FS (address . value) entries.
; Закон перенесено з lib/lisp-fs.lisp, без нової машинної викличності D9.
(0011 фс-об'єкт-адреси
  (0010 (записи)
    (110
      ((0101 записи) (001 ()))
      ((0100 (010 записи))
       (111 (100 (100 записи))
            (фс-об'єкт-адреси (011 записи)))))))

; D9:001011110 CLIPS-VAR-TERM, lib/clips-import.lisp:
; (?name as symbol) -> (var name); D8 SYMBOL->STRING + D9 STRING-REST + D8 STRING->SYMBOL.
(0011 clips-змінна-терм
  (0010 (символ)
    (1110 (001 var) (11101101 (110011101 (11101110 символ))))))

; D9:001010101 CLIPS-TEMPLATE-SLOT-ORDER, lib/clips-import.lisp:
; lookup atomic template key, return its original slot-order list.
(0011 clips-шаблон-слот-порядок
  (0010 (назва шаблони)
    (110
      ((0100 (010 назва)) (001 ()))
      ((010 шаблони) (001 ()))
      ((010 (100 шаблони))
       (clips-шаблон-слот-порядок назва (011 шаблони)))
      ((0100 (010 (100 (100 шаблони))))
       (clips-шаблон-слот-порядок назва (011 шаблони)))
      ((101 назва (100 (100 шаблони))) (011 (100 шаблони)))
      (#d1:1 (clips-шаблон-слот-порядок назва (011 шаблони))))))

; D9:001011001 FS-JOURNAL-APPEND, джерело lib/lisp-fs.lisp.
; Незмінне дописування одного запису: D4 APPEND(journal, LIST(event)).
; Ні direct D9 admission, ні host-side журналу.
(0011 фс-журнал-додати
  (0010 (журнал подія)
    (1111 журнал (1110 подія))))

; D9:010110100 CLIPS-DEFTEMPLATE-FORM?, джерело lib/clips-import.lisp.
; D3 ATOM/CONS та EQ з D1-контролем; не-список/складена голова = D1:0.
(0011 clips-deftemplate-форма?
  (0010 (форма)
    (110
      ((010 форма) #d1:0)
      ((0100 (010 (100 форма))) #d1:0)
      ((101 (100 форма) (001 deftemplate)) #d1:1)
      (#d1:1 #d1:0))))


; PAIP SORT*: a deliberately list-only derived SENS helper.
; Donor: juv4uk/paip-lisp@2db2ba99465cadef904e574b20b6981b32ad81df,
; lisp/auxfns.lisp. The donor's full sequence/key API is broader.
; These helpers accept a proper list and a strict "comes before" predicate
; that must return an exact D1 PredicateBit. Processing input left-to-right
; and placing a new item after equal keys keeps ties stable.
; This is NOT direct admission of D10:0011001011 SORT*; that row remains research.

(0011 вставити-впорядковано-за
  (0010 (перед? елемент упорядкований)
    (110
      ((порожнє? упорядкований)
       (сполучити елемент (як-є ())))
      ((перед? елемент (перше упорядкований))
       (сполучити елемент упорядкований))
      (#d1:1
       (сполучити
         (перше упорядкований)
         (вставити-впорядковано-за перед? елемент (решта упорядкований)))))))

(0011 сортувати-список-за-крок
  (0010 (перед? залишок упорядкований)
    (110
      ((порожнє? залишок) упорядкований)
      (#d1:1
       (сортувати-список-за-крок
         перед?
         (решта залишок)
         (вставити-впорядковано-за перед? (перше залишок) упорядкований))))))

(0011 сортувати-список-за
  (0010 (перед? елементи)
    (сортувати-список-за-крок перед? елементи (як-є ()))))

; Партія D10 / CLIPS: чотири похідні визначення на стороні SENS.
; Донорські закони: lib/clips-import.lisp — CLIPS-ASSERT-FORM?,
; CLIPS-PRINTOUT-FORM?, CLIPS-DROP-PRINTOUTS, CLIPS-ALL-ASSERTS?.
; Вхід: форма або правильний список форм CLIPS (D3-пари й атоми).
; Вихід предикатів: точно D1; фільтра: новий правильний D3-список.
; Умови застосування: EQ тільки над атомною головою; порядок зберігається;
; порожній список проходить ALL-ASSERTS? як істина.
; Тут не створюємо нових кодів і не оголошуємо direct D10 call-head admission.
; D1:YES = ATOM(QUOTE(())); D1:NO = ATOM(CONS(QUOTE(()),QUOTE(()))).

; D10:0100100110 clips-assert-form? — похідний закон через D3/D4.
(0011 твердження-clips?
  (0010 (форма)
    (110
      ((010 форма) (010 (111 (001 ()) (001 ()))))
      ((010 (100 форма)) (101 (100 форма) (001 assert)))
      ((010 (001 ())) (010 (111 (001 ()) (001 ())))))))

; D10:0100100111 clips-printout-form? — похідний закон через D3/D4.
(0011 виведення-clips?
  (0010 (форма)
    (110
      ((010 форма) (010 (111 (001 ()) (001 ()))))
      ((010 (100 форма)) (101 (100 форма) (001 printout)))
      ((010 (001 ())) (010 (111 (001 ()) (001 ())))))))

; D10:0100101000 clips-drop-printouts — похідний закон через D3/D4.
(0011 прибрати-виведення-clips
  (0010 (форми)
    (110
      ((010 форми) (001 ()))
      ((виведення-clips? (100 форми))
       (прибрати-виведення-clips (011 форми)))
      ((010 (001 ()))
       (111 (100 форми) (прибрати-виведення-clips (011 форми)))))))

; D10:0100101001 clips-all-asserts? — похідний закон через D3/D4.
(0011 усі-твердження-clips?
  (0010 (форми)
    (110
      ((010 форми) (010 (001 ())))
      ((твердження-clips? (100 форми))
       (усі-твердження-clips? (011 форми)))
      ((010 (001 ())) (010 (111 (001 ()) (001 ())))))))

; D10:0011111100 MAP-KEYS, D10:0011111110 MAP-VALUES,
; D10:0100001001 MAP-DISSOC, D10:0100001101 MAP-FROM-PAIRS.
; Джерело: lib/domains/d10.lisp і D9 мапа-вставити/мапа-список
; (knowledge/d10-current-inventory.json — координата НЕ дає runtime-допуск).
; Похідні визначення SENS: D3 CAR/CONS, D4 CADR, D6 MAP/FILTER/REDUCE,
; D9 незмінна мапа. Немає нового opcode, Rust registry або host Bool.
;
; D10:0011111100 — ключі в порядку фізичних записів алісту.
(0011 відобразити-ключі
  (0010 (мапа)
    (відобразити
      (0010 (запис) (100 запис))
      (мапа-список мапа))))

; D10:0011111110 — значення з другого поля кожного запису.
; Представлення D9 MAP-INSERT — список (ключ значення), а не host hashmap.
(0011 відобразити-значення
  (0010 (мапа)
    (відобразити
      (0010 (запис) (1001 запис))
      (мапа-список мапа))))

; D10:0100001001 — функціональне видалення ВСІХ записів за ключем;
; початковий аліст не змінюється, структурна рівність доручена SENS EQUAL.
(0011 вилучити-ключ-мапи
  (0010 (ключ мапа)
    (відсіяти
      (0010 (запис)
        (not? (equal? (100 запис) ключ)))
      (мапа-список мапа))))

; D10:0100001101 — послідовно матеріалізувати незмінну D9-мапу.
; Повторний ключ перезаписує старий, останнє значення перемагає.
; Неповний запис не підміняємо порожнім — D4 CADR відхилить його.
(0011 відобразити-з-пари
  (0010 (пари)
    (згорнути
      (0010 (мапа запис)
        (мапа-вставити (100 запис) (1001 запис) мапа))
      (мапа-порожній)
      пари)))


; D9:100010000..100011111 — 16 ратифікованих семикрокових селекторів.
; Композиції з D8-батька та D3 CAR/CDR без нового машинного виклику.
; Нативні позитиви й негативи: tests/semantic/d9-seven-step-selectors-laws.lisp.

; D9:100010000 п-п-р-п-п-п-п = п-п-р-п-п-п(D3:100(x)).
(0011 п-п-р-п-п-п-п
  (0010 (значення)
    (п-п-р-п-п-п (100 значення))))

; D9:100010001 п-п-р-п-п-п-р = п-п-р-п-п-п(D3:011(x)).
(0011 п-п-р-п-п-п-р
  (0010 (значення)
    (п-п-р-п-п-п (011 значення))))

; D9:100010010 п-п-р-п-п-р-п = п-п-р-п-п-р(D3:100(x)).
(0011 п-п-р-п-п-р-п
  (0010 (значення)
    (п-п-р-п-п-р (100 значення))))

; D9:100010011 п-п-р-п-п-р-р = п-п-р-п-п-р(D3:011(x)).
(0011 п-п-р-п-п-р-р
  (0010 (значення)
    (п-п-р-п-п-р (011 значення))))

; D9:100010100 п-п-р-п-р-п-п = п-п-р-п-р-п(D3:100(x)).
(0011 п-п-р-п-р-п-п
  (0010 (значення)
    (п-п-р-п-р-п (100 значення))))

; D9:100010101 п-п-р-п-р-п-р = п-п-р-п-р-п(D3:011(x)).
(0011 п-п-р-п-р-п-р
  (0010 (значення)
    (п-п-р-п-р-п (011 значення))))

; D9:100010110 п-п-р-п-р-р-п = п-п-р-п-р-р(D3:100(x)).
(0011 п-п-р-п-р-р-п
  (0010 (значення)
    (п-п-р-п-р-р (100 значення))))

; D9:100010111 п-п-р-п-р-р-р = п-п-р-п-р-р(D3:011(x)).
(0011 п-п-р-п-р-р-р
  (0010 (значення)
    (п-п-р-п-р-р (011 значення))))

; D9:100011000 п-п-р-р-п-п-п = п-п-р-р-п-п(D3:100(x)).
(0011 п-п-р-р-п-п-п
  (0010 (значення)
    (п-п-р-р-п-п (100 значення))))

; D9:100011001 п-п-р-р-п-п-р = п-п-р-р-п-п(D3:011(x)).
(0011 п-п-р-р-п-п-р
  (0010 (значення)
    (п-п-р-р-п-п (011 значення))))

; D9:100011010 п-п-р-р-п-р-п = п-п-р-р-п-р(D3:100(x)).
(0011 п-п-р-р-п-р-п
  (0010 (значення)
    (п-п-р-р-п-р (100 значення))))

; D9:100011011 п-п-р-р-п-р-р = п-п-р-р-п-р(D3:011(x)).
(0011 п-п-р-р-п-р-р
  (0010 (значення)
    (п-п-р-р-п-р (011 значення))))

; D9:100011100 п-п-р-р-р-п-п = п-п-р-р-р-п(D3:100(x)).
(0011 п-п-р-р-р-п-п
  (0010 (значення)
    (п-п-р-р-р-п (100 значення))))

; D9:100011101 п-п-р-р-р-п-р = п-п-р-р-р-п(D3:011(x)).
(0011 п-п-р-р-р-п-р
  (0010 (значення)
    (п-п-р-р-р-п (011 значення))))

; D9:100011110 п-п-р-р-р-р-п = п-п-р-р-р-р(D3:100(x)).
(0011 п-п-р-р-р-р-п
  (0010 (значення)
    (п-п-р-р-р-р (100 значення))))

; D9:100011111 п-п-р-р-р-р-р = п-п-р-р-р-р(D3:011(x)).
(0011 п-п-р-р-р-р-р
  (0010 (значення)
    (п-п-р-р-р-р (011 значення))))

; D9:010010110 FS-LIST і D9:010100001 FS-CONTAINS?.
; Джерело: lib/lisp-fs.lisp, форма незмінного FS (об'єкти зв'язки ревізія).
; Похідні від D4 CADR та D9 MAP->LIST/MAP-CONTAINS?, без direct D9 admission.
; Наявність ключа відмінна від значення: () є законним вмістом зв'язку.
(0011 фс-список
  (0010 (знімок)
    (мапа-список (фс-зв'язки знімок))))

(0011 фс-містить?
  (0010 (знімок назва)
    (мапа-містить? назва (фс-зв'язки знімок))))


; Партія D9: CLIPS-DEFTEMPLATE-NAME / CLIPS-TEMPLATES-FROM-FORMS.
; Джерело: lib/clips-import.lisp та ратифіковані адреси
; D9:001101010 і D9:001010011. Жодного нового opcode чи F1-допуску.
; Сфера дії: незмінні S-вирази з атомарним ім'ям, без module-prefix.
; (deftemplate NAME (slot A) ...) -> NAME через чинний D4 CADR.
(0011 clips-deftemplate-ім'я
  (0010 (форма)
    (1001 форма)))

; Зібрати впорядкований alist (NAME . (SLOT ...)) зі списку CLIPS-форм.
; Інші форми пропускаємо, підтримуємо кілька шаблонів і зберігаємо порядок.
; Сигнатура: proper list форм -> proper list пар; лише SENS D3/D4/D9.
(0011 clips-шаблони-з-форми
  (0010 (форми)
    (110
      ((0101 форми) (001 ()))
      ((clips-deftemplate-форма? (100 форми))
       (111
         (111
           (clips-deftemplate-ім'я (100 форми))
           (clips-deftemplate-слоти (100 форми)))
         (clips-шаблони-з-форми (011 форми))))
      ((010 (001 ()))
       (clips-шаблони-з-форми (011 форми))))))

; D9:100100000..100100111 — партія 09 із точних координат доменної драбини.
; D9:100100000 CADAAAAAR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-п-п + D3:100.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-п-п-п
  (0010 (значення)
    (п-р-п-п-п-п (100 значення))))

; D9:100100001 CADAAAADR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-п-п + D3:011.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-п-п-р
  (0010 (значення)
    (п-р-п-п-п-п (011 значення))))

; D9:100100010 CADAAADAR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-п-р + D3:100.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-п-р-п
  (0010 (значення)
    (п-р-п-п-п-р (100 значення))))

; D9:100100011 CADAAADDR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-п-р + D3:011.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-п-р-р
  (0010 (значення)
    (п-р-п-п-п-р (011 значення))))

; D9:100100100 CADAADAAR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-р-п + D3:100.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-р-п-п
  (0010 (значення)
    (п-р-п-п-р-п (100 значення))))

; D9:100100101 CADAADADR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-р-п + D3:011.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-р-п-р
  (0010 (значення)
    (п-р-п-п-р-п (011 значення))))

; D9:100100110 CADAADDAR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-р-р + D3:100.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-р-р-п
  (0010 (значення)
    (п-р-п-п-р-р (100 значення))))

; D9:100100111 CADAADDDR — ратифікований семикроковий селектор.
; Сигнатура: вкладена D3-пара -> значення; виконання: D8 п-р-п-п-р-р + D3:011.
; Немає нового коду, зовнішньої семантики або прямого допуску D9.
(0011 п-р-п-п-р-р-р
  (0010 (значення)
    (п-р-п-п-р-р (011 значення))))

; D10:0011001011 SORT* — чиста SENS-проєкція над незмінним списком.
; Донор PAIP auxfns.lisp@2db2ba99465cadef904e574b20b6981b32ad81df:
; (sort* sequence predicate &key key), результат — впорядкована копія.
; Тут доведено ВУЗЬКИЙ профіль: правильний список + точний D1-компаратор.
; Вектори, :key та прямий D10 opcode НЕ приймаються цим визначенням.
; Контракт поверхні: (сортувати-зірочка список перед?).
(0011 сортувати-зірочка
  (0010 (елементи перед?)
    (сортувати-список-за перед? елементи)))

; Відновлення D10 епістемічних законів після втрати під час паралельного
; оновлення core4. Джерело: коміт fbe630e23b5e, lib/epistemic.lisp.
; Лише SENS-композиція D3:001 QUOTE, D4:1110 LIST і D4:0011 DEFINE.
; Ратифіковані координати не означають direct-callability D10.
; D10:0010010011 MAKE-OBSERVATION.
(0011 створити-спостереження
  (0010 (source statement)
    (1110 (001 observation) (1110 (001 source) source) (1110 (001 statement) statement))))

; D10:0001110110 MAKE-CLAIM.
(0011 створити-твердження
  (0010 (statement source review)
    (1110 (001 claim) (1110 (001 statement) statement) (1110 (001 source) source) (1110 (001 review) review))))

; D10:0010001111 MAKE-EVIDENCE.
(0011 створити-доказ
  (0010 (claim-ref method outcome source-ref)
    (1110 (001 evidence)
          (1110 (001 claim-ref) claim-ref)
          (1110 (001 method) method)
          (1110 (001 outcome) outcome)
          (1110 (001 source-ref) source-ref))))

; D10:0010000101 MAKE-INTENT.
(0011 створити-намір
  (0010 (goal requirements stop-condition produces)
    (1110 (001 intent)
          (1110 (001 goal) goal)
          (1110 (001 requires) requirements)
          (1110 (001 stop-on) stop-condition)
          (1110 (001 produces) produces))))


; Повернено визначення з останнього успішного main f1a8fa035d5a.
; Попередній паралельний коміт загубив їх через зріз кінця lib/core4.lisp.
; Відновлено без нових ідентичностей, без зміни ратифікації та без branch.
(0011 п-р-р-п-п-п-п
  (0010 (значення)
    (п-р-р-п-п-п (100 значення))))

(0011 п-р-р-п-п-п-р
  (0010 (значення)
    (п-р-р-п-п-п (011 значення))))

(0011 п-р-р-п-п-р-п
  (0010 (значення)
    (п-р-р-п-п-р (100 значення))))

(0011 п-р-р-п-п-р-р
  (0010 (значення)
    (п-р-р-п-п-р (011 значення))))

(0011 п-р-р-п-р-п-п
  (0010 (значення)
    (п-р-р-п-р-п (100 значення))))

(0011 п-р-р-п-р-п-р
  (0010 (значення)
    (п-р-р-п-р-п (011 значення))))

(0011 п-р-р-п-р-р-п
  (0010 (значення)
    (п-р-р-п-р-р (100 значення))))

(0011 п-р-р-п-р-р-р
  (0010 (значення)
    (п-р-р-п-р-р (011 значення))))

(0011 п-р-р-р-п-п-п
  (0010 (значення)
    (п-р-р-р-п-п (100 значення))))

(0011 п-р-р-р-п-п-р
  (0010 (значення)
    (п-р-р-р-п-п (011 значення))))

(0011 п-р-р-р-п-р-п
  (0010 (значення)
    (п-р-р-р-п-р (100 значення))))

(0011 п-р-р-р-п-р-р
  (0010 (значення)
    (п-р-р-р-п-р (011 значення))))

(0011 п-р-р-р-р-п-п
  (0010 (значення)
    (п-р-р-р-р-п (100 значення))))

(0011 п-р-р-р-р-п-р
  (0010 (значення)
    (п-р-р-р-р-п (011 значення))))

(0011 п-р-р-р-р-р-п
  (0010 (значення)
    (п-р-р-р-р-р (100 значення))))

(0011 п-р-р-р-р-р-р
  (0010 (значення)
    (п-р-р-р-р-р (011 значення))))

(0011 розділити-правило-clips
  (0010 (тіло)
    (110
      ((0101 тіло) (1110 (001 ()) (001 ())))
      ((010 (100 тіло))
       (110
         ((101 (100 тіло) (001 =>))
          (1110 (001 ()) (011 тіло)))
         ((010 (001 ()))
          ((0010 (частини)
             (1110
               (111 (100 тіло) (100 частини))
               (1001 частини)))
           (розділити-правило-clips (011 тіло))))))
      ((010 (001 ()))
       ((0010 (частини)
          (1110
            (111 (100 тіло) (100 частини))
            (1001 частини)))
        (розділити-правило-clips (011 тіло)))))))

(0011 зібрати-висновки-clips
  (0010 (форми)
    (110
      ((0101 форми) (001 ()))
      ((010 (001 ()))
       (1111
         (011 (100 форми))
         (зібрати-висновки-clips (011 форми)))))))

(0011 фс-пакет-поле
  (0010 (назва пакет)
    (110
      ((0101 пакет) (001 ()))
      ((010 пакет) (001 ()))
      ((010 (100 пакет)) (001 ()))
      ((0101 (100 (100 пакет))) (001 ()))
      ((0100 (010 (100 (100 пакет)))) (001 ()))
      ((101 назва (100 (100 пакет))) (011 (100 пакет)))
      (#d1:1 (фс-пакет-поле назва (011 пакет))))))

(0011 фс-розв'язати
  (0010 (знімок назва)
    (list
      (фс-об'єкти знімок)
      (вилучити-ключ-мапи назва (фс-зв'язки знімок))
      (збільшити-на-один (фс-ревізія знімок)))))

(0011 justified-member? обґрунтований-член?)

(0011 remove-justified видалити-обґрунтований)

(0011 add-new-justified додати-нові-обґрунтований)

(0011 drop-unsupported відкинути-непідтримані)

(0011 преамбула-правила-clips?
  (0010 (форма)
    (110
      ((010 форма)
       (110
         ((101 форма (001 =>)) (010 (111 (001 ()) (001 ()))))
         ((010 (001 ())) (010 (001 ())))))
      ((0100 (010 (100 форма))) (010 (111 (001 ()) (001 ()))))
      ((101 (100 форма) (001 declare)) (010 (001 ())))
      ((010 (001 ())) (010 (111 (001 ()) (001 ())))))))

(0011 прибрати-преамбулу-clips
  (0010 (тіло)
    (110
      ((010 тіло) тіло)
      ((преамбула-правила-clips? (100 тіло))
       (прибрати-преамбулу-clips (011 тіло)))
      ((010 (001 ())) тіло))))

(0011 п-р-п-р-п-п-п
  (0010 (значення) (п-р-п-р-п-п (100 значення))))

(0011 п-р-п-р-п-п-р
  (0010 (значення) (п-р-п-р-п-п (011 значення))))

(0011 п-р-п-р-п-р-п
  (0010 (значення) (п-р-п-р-п-р (100 значення))))

(0011 п-р-п-р-п-р-р
  (0010 (значення) (п-р-п-р-п-р (011 значення))))

(0011 п-р-п-р-р-п-п
  (0010 (значення) (п-р-п-р-р-п (100 значення))))

(0011 п-р-п-р-р-п-р
  (0010 (значення) (п-р-п-р-р-п (011 значення))))

(0011 п-р-п-р-р-р-п
  (0010 (значення) (п-р-п-р-р-р (100 значення))))

(0011 п-р-п-р-р-р-р
  (0010 (значення) (п-р-п-р-р-р (011 значення))))


; D10:0011000010 EMPTY-QUEUE? — вузький закон для черги-списку.
; Джерело: research/d10-queue-sortcar-mapinto-batch-2026-10-17.lisp.
; Вхід: правильний D3-список; вихід: точне D1, без host Bool.
; Це похідне SENS-визначення, не новий D10 прямий машинний виклик.
(0011 черга-порожня?
  (0010 (черга) (порожнє? черга)))

; D10:0001110011 SORTCAR — стабільне сортування за CAR кожної пари.
; Ключі: допущені точні числа D24+; рівні ключі зберігають порядок.
; Композиція раніше визначеного SENS сортувати-список-за.
(0011 сортувати-за-першим
  (0010 (елементи)
    (сортувати-список-за
      (0010 (ліве праве) (менше? (перше ліве) (перше праве)))
      елементи)))

; Чотири чинні D9-значення: українські поверхні існуючих SENS-замикань.
; Точні D9 координати — lib/domains/d9.lisp; без нових opcode чи ратифікації.
; Числові операнди утворюються тільки через D24+ (довжина/арифметика).
; D9:110101100
(0011 символ? symbol?)
; D9:110110110
(0011 бінарний binary)
; D9:110111001
(0011 число-рядок number->string)
; D9:110111111
(0011 частка-остача divmod)

; D5 точні функції над кваліфікованими числами D24+.
; Джерело: research/d5-arith-order-surface-batch-2026-10-17.lisp.
; D5:01011 DIFFERENCE, 10110 TIMES, 11010 LESSP, 11011 GREATERP.
; Похідні SENS-визначення через ратифіковані коди; жодних нових opcode.
(0011 відняти
  (0010 (ліве праве) (01011 ліве праве)))
(0011 difference відняти)
(0011 помножити
  (0010 (ліве праве) (10110 ліве праве)))
(0011 times помножити)
(0011 менше?
  (0010 (ліве праве) (11010 ліве праве)))
(0011 lessp? менше?)
(0011 більше?
  (0010 (ліве праве) (11011 ліве праве)))
(0011 greaterp? більше?)
; D8:11001100 DIV — дослідження D1–D10, source:
; research/d8-div-lognot-batch-2026-10-17.lisp.
; Явні числові операнди D24+; результат — правильний список
; (частка остача), без проміжних десяткових значень у SENS.
; Це похідне SENS-визначення, не прямий виклик opcode D8.
(0011 частка+остача
  (0010 (ділене дільник)
    (111 (quotient ділене дільник)
      (111 (mod ділене дільник) (001 ())))))

; Довизначення D10 із knowledge/d10-current-inventory.json
; та research/d10-sassoc-vector-string-count-batch-2026-10-17.lisp.
; D10:0001100101 SASSOC — перша пара alist із рівним ключем.
; Закон: D5:11100 ASSOC повертає саме пару, відсутність — D3:000.
; Сигнатура: (атом, D3-alist) -> D3-пара або D3:000.
; Механізм: похідна SENS-LAMBDA, не прямий D10 opcode.
(0011 пошук-асоціації
  (0010 (ключ пари)
    (знайти-за-ключем ключ пари)))
(0011 sassoc пошук-асоціації)

; Визначені D10-механізми вже є в Core4. Додаємо тільки точні
; ратифіковані en-проєкції без дублювання змісту.
; D10:0011000010 EMPTY-QUEUE?, D10:0001110011 SORTCAR.
(0011 empty-queue? черга-порожня?)
(0011 sortcar сортувати-за-першим)

; D10:0000000001 RESULT-COUNT, 0010001110 KNOWLEDGE-PROPER-LIST?,
; 0010010110 RESULT-PROPER-LIST?, 0001001001 FORALL-... .
(0011 result-count кількість-результатів)
(0011 knowledge-proper-list? правильний-список-знань?)
(0011 result-proper-list? правильний-список-результатів?)
(0011 forall-every-candidate-satisfies? кожен-задовольняє?)

; D10:0011001011 SORT* — наявне двоаргументне SENS-сортування,
; без історичного байтового dispatch.
(0011 sort* сортувати-зірочка)


; D10:0101100111 MY-SELECT-DEFS-BY-NAMES і D10:0101101000
; MY-REMOVE-DEFS-BY-NAMES — похідні мовні операції з lib/meta-eval.lisp.
; Вхід: правильний список визначень (DEFINE name body...) та список атомних імен.
; D4:1001 CADR дістає ім'я; D10:0001100010 MEMQ дає атомну EQ-належність.
; Результат: новий правильний список без перестановки, збережено дублікати.
; Немає нового opcode, direct D10 admission чи host-семантики.
(0011 вибрати-визначення-за-іменами
  (0010 (форми імена)
    (110
      ((0101 форми) (001 ()))
      ((not? (0101 (входження-eq (1001 (100 форми)) імена)))
       (111 (100 форми)
            (вибрати-визначення-за-іменами (011 форми) імена)))
      ((010 (001 ()))
       (вибрати-визначення-за-іменами (011 форми) імена)))))

(0011 вилучити-визначення-за-іменами
  (0010 (форми імена)
    (110
      ((0101 форми) (001 ()))
      ((not? (0101 (входження-eq (1001 (100 форми)) імена)))
       (вилучити-визначення-за-іменами (011 форми) імена))
      ((010 (001 ()))
       (111 (100 форми)
            (вилучити-визначення-за-іменами (011 форми) імена))))))
