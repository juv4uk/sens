; A universal(-ish) importer for old symbolic-AI systems, starting with
; CLIPS (see NASA's Johnson Space Center, 1985 — the same forward-chaining
; lineage lib/forward.lisp grew independently). "Universal" here means: this
; project reads *whatever S-expression syntax the old system used* as raw
; data via my-lisp's own `read`/`quote` — no dedicated tokenizer, no string
; primitives, no new Rust code. CLIPS forms like `(defrule foo (bar ?x) =>
; (assert (baz ?x)))` parse cleanly as ordinary my-lisp data (`?x`, `=>`,
; `defrule` are all just symbols to the reader) even though none of them
; are meaningful my-lisp forms to *evaluate* — homoiconicity used exactly
; as McCarthy's own S-expression choice intended: code (or someone else's
; code) is data first.
;
; Step 1 (deliberately small, by explicit agreement before writing this):
; `deffacts` only — CLIPS's variable-free fact declarations. A CLIPS form
; `(deffacts name (fact1 ...) (fact2 ...) ...)` becomes the same
; `(head . body)` clause list `defmodule` already expects, one
; zero-condition clause per fact. `defrule` (rules, and CLIPS's `?x`
; variable syntax needing conversion to `(var x)`) is a separate, later
; step — not assumed here.
;
; Універсальний(-уватий) імпортер зі старих символьних AI-систем, починаючи
; з CLIPS (NASA Johnson Space Center, 1985 рік — та сама forward-chaining
; лінія, яку lib/forward.lisp виростив незалежно). "Універсальний" тут
; означає: цей проєкт читає *будь-який S-вираз старої системи* як сирі дані
; через власні `read`/`quote` my-lisp — без окремого токенізатора, без
; рядкових примітивів, без нового Rust-коду. CLIPS-форми на кшталт
; `(defrule foo (bar ?x) => (assert (baz ?x)))` парсяться як звичайні
; my-lisp дані (`?x`, `=>`, `defrule` — просто символи для reader'а), хоча
; жоден з них не є осмисленою my-lisp-формою для *виконання* —
; гомоіконічність, використана саме так, як і задумував вибір S-виразів
; Маккарті: код (навіть чужий) — спершу дані.
;
; Крок 1 (свідомо маленький, за явною домовленістю перед написанням):
; лише `deffacts` — CLIPS-декларації фактів без змінних. CLIPS-форма
; `(deffacts name (факт1 ...) (факт2 ...) ...)` стає тим самим списком
; clause `(head . body)`, якого вже чекає `defmodule`, по одному
; clause-факту без умов на кожен факт. `defrule` (правила, і CLIPS-синтаксис
; змінних `?x`, який треба конвертувати в `(var x)`) — окремий, пізніший
; крок, тут не мається на увазі.
;
; Ein universeller(-ähnlicher) Importer für alte symbolische KI-Systeme,
; beginnend mit CLIPS (NASA Johnson Space Center, 1985 — dieselbe
; Forward-Chaining-Linie, die lib/forward.lisp unabhängig entwickelt hat).
; "Universell" bedeutet hier: dieses Projekt liest *jede S-Ausdruck-Syntax
; des alten Systems* als Rohdaten über my-lisps eigenes `read`/`quote` —
; kein eigener Tokenizer, keine String-Primitive, kein neuer Rust-Code.
; CLIPS-Formen wie `(defrule foo (bar ?x) => (assert (baz ?x)))` parsen
; sauber als gewöhnliche my-lisp-Daten (`?x`, `=>`, `defrule` sind für den
; Reader nur Symbole), obwohl keine davon eine sinnvolle my-lisp-Form zum
; *Auswerten* ist — Homoikonizität genau so eingesetzt, wie McCarthys
; eigene Wahl der S-Ausdrücke es beabsichtigte: Code (auch fremder) ist
; zuerst Daten.
;
; Schritt 1 (bewusst klein, nach ausdrücklicher Absprache vor dem
; Schreiben): nur `deffacts` — CLIPS' variablenfreie Faktendeklarationen.
; Eine CLIPS-Form `(deffacts name (fakt1 ...) (fakt2 ...) ...)` wird zur
; selben `(head . body)`-Clause-Liste, die `defmodule` bereits erwartet,
; eine bedingungslose Clause pro Fakt. `defrule` (Regeln, und CLIPS'
; `?x`-Variablensyntax, die zu `(var x)` konvertiert werden muss) ist ein
; separater, späterer Schritt, hier nicht unterstellt.
; --- Step 8: deftemplate, CLIPS's named-slot facts -----------------------
; Ordinary CLIPS facts are positional, the same shape my-lisp facts always
; were: `(planet earth)`. A `deftemplate` changes that for facts of its
; name: `(deftemplate reading (slot sensor) (slot value))` means every
; `reading` fact from then on is written by slot name, in any order —
; `(reading (value 98) (sensor probe1))`, not `(reading probe1 98)`.
; my-lisp facts stay purely positional (no reason to grow that
; representation just to mirror CLIPS) — so a template's declared slot
; order becomes the fixed positional order its facts get converted to on
; import: the example above becomes `(reading probe1 98)`, matching
; `(slot sensor)` then `(slot value)`.
;
; Deliberately a two-pass, pure-functional approach, not a running mutable
; registry: `clips-templates-from-forms` scans the *whole* form list once
; up front and builds a plain `(name . (slot1 slot2 ...))` alist, which
; every fact/condition/conclusion conversion then just looks up — no
; `def`-based global state needed (see `lib/knowledge.lisp`'s
; `*knowledge-base*` for why that would need the same top-level-only-def
; care this project keeps avoiding when a pure function already works).
; A term whose head isn't a known template name passes through unchanged.
;
; Крок 8: deftemplate, іменовані слоти CLIPS. Звичайні CLIPS-факти —
; позиційні, та сама форма, що й факти my-lisp завжди мали: `(planet
; earth)`. `deftemplate` змінює це для фактів своєї назви: `(deftemplate
; reading (slot sensor) (slot value))` означає, що відтепер кожен факт
; `reading` записується за іменем слота, у будь-якому порядку — `(reading
; (value 98) (sensor probe1))`, не `(reading probe1 98)`. Факти my-lisp
; лишаються чисто позиційними (нема причини розширювати це представлення
; лише щоб віддзеркалити CLIPS) — тож оголошений порядок слотів шаблону
; стає фіксованим позиційним порядком, у який його факти конвертуються при
; імпорті: приклад вище стає `(reading probe1 98)`, відповідно до `(slot
; sensor)`, тоді `(slot value)`.
;
; Свідомо дво-прохідний, чисто функціональний підхід, не робочий
; мутабельний реєстр: `clips-templates-from-forms` сканує *весь* список
; форм наперед один раз і будує звичайний alist `(назва . (слот1 слот2
; ...))`, який потім просто шукає кожна конвертація факту/умови/висновку —
; жодного `def`-based глобального стану не потрібно. Терм, чия голова не є
; відомою назвою шаблону, проходить незмінним.
;
; Schritt 8: deftemplate, CLIPS' benannte Slots. Gewöhnliche CLIPS-Fakten
; sind positional, dieselbe Form, die my-lisp-Fakten immer hatten:
; `(planet earth)`. Ein `deftemplate` ändert das für Fakten seines Namens:
; `(deftemplate reading (slot sensor) (slot value))` bedeutet, dass jeder
; `reading`-Fakt fortan per Slot-Name geschrieben wird, in beliebiger
; Reihenfolge — `(reading (value 98) (sensor probe1))`, nicht `(reading
; probe1 98)`. my-lisp-Fakten bleiben rein positional (kein Grund, diese
; Darstellung nur zu erweitern, um CLIPS zu spiegeln) — die deklarierte
; Slot-Reihenfolge eines Templates wird also zur festen positionalen
; Reihenfolge, in die seine Fakten beim Import umgewandelt werden: das
; obige Beispiel wird zu `(reading probe1 98)`, entsprechend `(slot
; sensor)`, dann `(slot value)`.
;
; Bewusst ein zweistufiger, rein funktionaler Ansatz, keine laufende
; mutable Registry: `clips-templates-from-forms` durchsucht die *ganze*
; Formliste einmal im Voraus und baut eine gewöhnliche Alist `(name .
; (slot1 slot2 ...))`, die jede Fakt-/Bedingungs-/Schlussfolgerungs-
; Konvertierung dann einfach nachschlägt — kein `def`-basierter globaler
; Zustand nötig. Ein Term, dessen Kopf kein bekannter Template-Name ist,
; bleibt unverändert.
(00001001 clips-deftemplate-form?
  (00001000 (form)
    (00000111
      
      ((00000010 form)  (00000001 ()))
      ((0100 (00000010 (00000101 form))) (00000011 (00000101 form) (00000001 deftemplate)))
      ((00000010 (00000101 form))  (00000011 (00000101 form) (00000001 deftemplate)))
      (t (00000001 ())))))

; Real CLIPS files namespace their deftemplate/deffacts names with a
; `defmodule` prefix, e.g. `QUESTIONS::question`. `wine-external.clp`
; (fetched from CLIPS's own examples) declares `(deftemplate QUESTIONS::question ...)`
; but then asserts plain `(question ...)` facts inside `deffacts` — CLIPS
; resolves the bare name against whichever module is current, but this
; importer has no notion of modules at all. Stripping every name down to
; whatever follows the last `::` (or the whole name, if there is none)
; before it ever reaches the template alist lets bare and qualified names
; match each other, without needing to model `defmodule` for real.
; Реальні CLIPS-файли простороюють імена deftemplate/deffacts префіксом
; `defmodule`, напр. `QUESTIONS::question`. `wine-external.clp` (зі
; справжніх прикладів CLIPS) оголошує `(deftemplate QUESTIONS::question ...)`,
; але потім у `deffacts` асертує прості факти `(question ...)` — CLIPS сам
; резолвить голе ім'я відносно поточного модуля, а цей імпортер модулів
; узагалі не знає. Обрізання кожного імені до частини після останнього
; `::` (або всього імені, якщо `::` немає) ще до потрапляння в реєстр
; шаблонів дозволяє голим і кваліфікованим іменам збігатися одне з одним,
; без реальної підтримки `defmodule`.
; Echte CLIPS-Dateien versehen deftemplate/deffacts-Namen mit einem
; `defmodule`-Präfix, z.B. `QUESTIONS::question`. `wine-external.clp` (aus
; den echten CLIPS-Beispielen) deklariert `(deftemplate QUESTIONS::question ...)`,
; asserted dann aber schlichte `(question ...)`-Fakten in `deffacts` — CLIPS
; löst den nackten Namen selbst gegen das aktuelle Modul auf, dieser
; Importer kennt Module überhaupt nicht. Jeden Namen schon vor der
; Aufnahme in die Vorlagen-Registry auf den Teil nach dem letzten `::`
; zu kürzen (oder den ganzen Namen, falls kein `::` vorkommt) lässt nackte
; und qualifizierte Namen einander finden, ohne `defmodule` wirklich
; abzubilden.
(00001001 clips-string-empty? (00001000 (s) (00000011 s "")))

(00001001 clips-string-starts-with-double-colon?
  (00001000 (s)
    (00000111
      ((clips-string-empty? s) (00000001 ()))
      ((clips-string-empty? (01000000 s)) (00000001 ()))
      ((00000011 (00111111 s) ":") (00000011 (00111111 (01000000 s)) ":"))
      (t (00000001 ())))))

(00001001 clips-string-after-last-double-colon
  (00001000 (s)
    (00000111
      ((clips-string-empty? s) (00000001 ()))
      ((clips-string-starts-with-double-colon? s)
       (10011100 ((after (clips-string-after-last-double-colon (01000000 (01000000 s)))))
         (00000111
           ((00000011 after (00000001 ())) (01000000 (01000000 s)))
           (t after))))
      (t (clips-string-after-last-double-colon (01000000 s))))))

(00001001 clips-strip-module-prefix
  (00001000 (sym)
    (00000111
      ((00100011 sym)
       (10011100 ((after (clips-string-after-last-double-colon (01000010 sym))))
         (00000111
           ((00000011 after (00000001 ())) sym)
           (t (01000011 after)))))
      (t sym))))

(00001001 clips-deftemplate-name (00001000 (form) (clips-strip-module-prefix (00101111 form))))

(00001001 clips-slot-name (00001000 (slot-form) (00101111 slot-form)))

(00001001 clips-slot-names
  (00001000 (slot-forms)
    (00000111
      
      ((00000010 slot-forms)  (00000001 ()))
      (t (00000100 (clips-slot-name (00000101 slot-forms)) (clips-slot-names (00000110 slot-forms)))))))

(00001001 clips-deftemplate-slots
  (00001000 (form)
    (clips-slot-names (00110101 form))))

(00001001 clips-templates-from-forms
  (00001000 (forms)
    (00000111
      
      ((00000010 forms)  (00000001 ()))
      ((clips-deftemplate-form? (00000101 forms))
       (00000100 (00000100 (clips-deftemplate-name (00000101 forms)) (clips-deftemplate-slots (00000101 forms)))
             (clips-templates-from-forms (00000110 forms))))
      (t (clips-templates-from-forms (00000110 forms))))))

(00001001 clips-template-slot-order
  (00001000 (name templates)
    (10011100 ((entry (00101101 name templates)))
      (00000111
        
        ((00000010 entry)  (00000001 ()))
        (t (00000110 entry))))))

; A CLIPS condition can name a multislot with no value at all, e.g.
; `(precursors)` in wine-external.clp's `ask-a-question` rule — CLIPS reads
; that as "match regardless of what's in this slot, including empty". A
; well-formed slot form otherwise always has a value part (`(slotname
; value)`), so `(cdr slot-form)` being empty is exactly this valueless
; case; degrading to '() (no constraint) here follows the same "skip,
; don't crash" policy as clips-lookup-slot-value's own atom guard below,
; instead of letting `second` fail on a list with no cdr.
; CLIPS-умова може називати мультислот зовсім без значення, напр.
; `(precursors)` у правилі `ask-a-question` з wine-external.clp — CLIPS
; читає це як "збігається незалежно від вмісту цього слота, навіть
; порожнього". Добре сформована форма слота завжди має частину значення
; (`(slotname value)`), тож порожній `(cdr slot-form)` — це саме цей
; безвартісний випадок; деградація до '() (без обмеження) тут іде тим
; самим шляхом "пропустити, не впасти", що й власна atom-перевірка
; clips-lookup-slot-value нижче, замість падіння `second` на списку без
; cdr.
; Eine CLIPS-Bedingung kann einen Multislot ganz ohne Wert benennen, z.B.
; `(precursors)` in der Regel `ask-a-question` aus wine-external.clp —
; CLIPS liest das als "passt unabhängig vom Inhalt dieses Slots, auch
; leer". Eine wohlgeformte Slot-Form hat sonst immer einen Wertteil
; (`(slotname value)`), also ist ein leeres `(cdr slot-form)` genau dieser
; wertlose Fall; die Degradierung zu '() (keine Einschränkung) folgt hier
; derselben "überspringen statt abstürzen"-Politik wie die eigene
; atom-Prüfung von clips-lookup-slot-value weiter unten, statt `second`
; auf einer Liste ohne cdr abstürzen zu lassen.
(00001001 clips-slot-value-of
  (00001000 (slot-form)
    (00000111
      
      ((00000010 (00000110 slot-form))  (00000001 ()))
      (t (00101111 slot-form)))))

; Guards with `(atom (car slot-forms))` before comparing: a well-formed
; slot entry is `(slotname value)`, a compound list, but a positional fact
; whose head happens to collide with an unrelated template's name (a
; contradictory, malformed CLIPS input — a name can't be both positional
; and slot-based) would hand this bare atoms instead. Degrading to "no
; value found" here keeps the same "skip, don't crash" policy the rest of
; this file follows, rather than letting `car` error on a non-pair.
(00001001 clips-lookup-slot-value
  (00001000 (slot-name slot-forms)
    (00000111
      
      ((00000010 slot-forms)  (00000001 ()))
      ((0100 (00000010 (00000101 slot-forms))) (clips-lookup-slot-value slot-name (00000110 slot-forms)))
      ((00000010 (00000101 slot-forms))  (clips-lookup-slot-value slot-name (00000110 slot-forms)))
      ((00100010 slot-name (00000101 (00000101 slot-forms))) (clips-slot-value-of (00000101 slot-forms)))
      (t (clips-lookup-slot-value slot-name (00000110 slot-forms))))))

(00001001 clips-positional-args
  (00001000 (slot-order slot-forms)
    (00000111
      
      ((00000010 slot-order)  (00000001 ()))
      (t (00000100 (clips-lookup-slot-value (00000101 slot-order) slot-forms)
                (clips-positional-args (00000110 slot-order) slot-forms))))))

; Step 13 (fold-in fix, verified before writing — same discipline as
; lib/forward.lisp's Steps 10-12): originally recursed through a `not`
; wrapper only. A template fact nested inside `or`/`and` — e.g. `(or (cat
; (name ?x)) (dog (name ?x)))` — silently never had its named slots
; converted to positional form at all, since neither `or` nor `and` was
; special-cased; the whole condition passed through unchanged (`(cat
; (name ?x))` never became `(cat ?x)`), so it could never unify against a
; positional `(cat tom)` fact — a rule that quietly derived nothing. Same
; underlying lesson `lib/forward.lisp`'s Steps 10-12 kept re-learning:
; `not`, `or`, and `and` all need explicit recursion, not just `not`.
;
; Крок 13 (виправлення вбудовано, перевірено перед написанням — та сама
; дисципліна, що й Кроки 10-12 `lib/forward.lisp`): раніше рекурсував лише
; крізь обгортку `not`. Факт-шаблон, вкладений в `or`/`and` — напр. `(or
; (cat (name ?x)) (dog (name ?x)))` — мовчки взагалі не мав своїх
; іменованих слотів конвертованих у позиційну форму, бо ні `or`, ні `and`
; не були окремо оброблені; уся умова проходила незмінною (`(cat (name
; ?x))` ніколи не ставала `(cat ?x)`), тож ніколи не могла унікуватись з
; позиційним фактом `(cat tom)` — правило, що мовчки нічого не виводило.
; Той самий урок, який Кроки 10-12 `lib/forward.lisp` повторювали: `not`,
; `or` і `and` усі потребують явної рекурсії, не лише `not`.
;
; Schritt 13 (eingearbeiteter Fix, vor dem Schreiben verifiziert —
; dieselbe Disziplin wie Schritte 10-12 in `lib/forward.lisp`): rekursierte
; ursprünglich nur durch einen `not`-Wrapper. Ein Template-Fakt,
; verschachtelt in `or`/`and` — z. B. `(or (cat (name ?x)) (dog (name
; ?x)))` — hatte seine benannten Slots stillschweigend nie in positionale
; Form umgewandelt, da weder `or` noch `and` gesondert behandelt wurden;
; die ganze Bedingung blieb unverändert (`(cat (name ?x))` wurde nie zu
; `(cat ?x)`), sodass sie nie gegen einen positionalen Fakt `(cat tom)`
; unifizieren konnte — eine Regel, die still nichts ableitete. Dieselbe
; Lehre, die Schritte 10-12 in `lib/forward.lisp` wiederholt lernten: `not`,
; `or` und `and` brauchen alle explizite Rekursion, nicht nur `not`.
; CLIPS `not` wird zur Sprachnegation `not?` (Prädikat mit `?`, #1444).
(00001001 clips-convert-template
  (00001000 (term templates)
    (00000111
      
      ((00000010 term)  term)
      ((0100 (00000010 (00000101 term))) (00000111
         ((00000011 (00000101 term) (00000001 not)) (00100111 (00000001 not?) (clips-convert-template (00101111 term) templates)))
         ((00000011 (00000101 term) (00000001 or)) (00000100 (00000001 or) (clips-convert-template-list (00000110 term) templates)))
         ((00000011 (00000101 term) (00000001 and)) (00000100 (00000001 and) (clips-convert-template-list (00000110 term) templates)))
         ((00000011 (00000101 term) (00000001 exists)) (00000100 (00000001 exists) (clips-convert-template-list (00000110 term) templates)))
         ((00000011 (00000101 term) (00000001 forall)) (00000100 (00000001 forall) (clips-convert-template-list (00000110 term) templates)))
         (t (10011100 ((slot-order (clips-template-slot-order (clips-strip-module-prefix (00000101 term)) templates)))
              (00000111
                
                ((00000010 slot-order)  term)
                (t (00000100 (00000101 term) (clips-positional-args slot-order (00000110 term)))))))))
      ((00000010 (00000101 term))  (00000111
         ((00000011 (00000101 term) (00000001 not)) (00100111 (00000001 not?) (clips-convert-template (00101111 term) templates)))
         ((00000011 (00000101 term) (00000001 or)) (00000100 (00000001 or) (clips-convert-template-list (00000110 term) templates)))
         ((00000011 (00000101 term) (00000001 and)) (00000100 (00000001 and) (clips-convert-template-list (00000110 term) templates)))
         ((00000011 (00000101 term) (00000001 exists)) (00000100 (00000001 exists) (clips-convert-template-list (00000110 term) templates)))
         ((00000011 (00000101 term) (00000001 forall)) (00000100 (00000001 forall) (clips-convert-template-list (00000110 term) templates)))
         (t (10011100 ((slot-order (clips-template-slot-order (clips-strip-module-prefix (00000101 term)) templates)))
              (00000111
                
                ((00000010 slot-order)  term)
                (t (00000100 (00000101 term) (clips-positional-args slot-order (00000110 term)))))))))
      (t term))))

(00001001 clips-convert-template-list
  (00001000 (terms templates)
    (00000111
      
      ((00000010 terms)  (00000001 ()))
      (t (00000100 (clips-convert-template (00000101 terms) templates)
                (clips-convert-template-list (00000110 terms) templates))))))

(00001001 clips-fact-clause
  (00001000 (fact) (00100111 fact)))

; `(cons ... (clips-facts->clauses ...))` is not a tail call — for a real
; CLIPS file with a big `deffacts` block (`animal-external.clp`'s own
; knowledge base is 128 facts in one block) the Rust call stack grew one
; frame per fact and overflowed. `-onto` accumulator + `reverse`, the same
; stack-safe shape `lib/core.lisp`'s own `map`/`filter` use, keeps every
; recursive call here in tail position.
; `(cons ... (clips-facts->clauses ...))` — не хвостовий виклик: на
; справжньому CLIPS-файлі з великим блоком `deffacts` (`animal-external.clp`'s
; власна база знань — 128 фактів в одному блоці) стек Rust ріс на один
; фрейм на факт і переповнювався. Акумулятор `-onto` + `reverse`, та сама
; стек-безпечна форма, яку використовують власні `map`/`filter` з
; `lib/core.lisp`, тримає кожен рекурсивний виклик тут у хвостовій позиції.
; `(cons ... (clips-facts->clauses ...))` ist kein Tail-Call — bei einer
; echten CLIPS-Datei mit einem großen `deffacts`-Block (`animal-external.clp`s
; eigene Wissensbasis hat 128 Fakten in einem Block) wuchs der Rust-Stack
; um einen Frame pro Fakt und lief über. Akkumulator `-onto` + `reverse`,
; dieselbe stack-sichere Form, die `lib/core.lisp`s eigene `map`/`filter`
; verwenden, hält jeden rekursiven Aufruf hier in Tail-Position.
(00001001 clips-facts->clauses-onto
  (00001000 (facts templates acc)
    (00000111
      ((0100 (00000010 facts)) (00101010 acc))
      ((00000010 facts)  (00101010 acc))
      (t (clips-facts->clauses-onto
           (00000110 facts) templates
           (00000100 (clips-fact-clause (clips-convert-template (00000101 facts) templates)) acc))))))

(00001001 clips-facts->clauses
  (00001000 (facts templates)
    (clips-facts->clauses-onto facts templates (00000001 ()))))

; `(cddr form)` drops `deffacts` and the deffacts block's own name,
; leaving just the fact list.
(00001001 clips-deffacts->clauses
  (00001000 (form templates)
    (clips-facts->clauses (00110101 form) templates)))

; --- Step 2: defrule, with CLIPS's `?x` variable syntax ------------------
; CLIPS variables are ordinary symbols to my-lisp's reader (`?x` parses as
; one atomic symbol, not reader-macro syntax) — but my-lisp has no way to
; inspect a symbol's characters on its own. `symbol->string`/`string->symbol`/
; `string-first`/`string-rest` (crates/my-lisp/src/eval/special_forms.rs)
; were added specifically for this: peeling the `?` off `?x` to build the
; logic-variable term `(var x)` `lib/unify.lisp` expects. Added deliberately,
; not casually — per this project's own "don't grow the Rust surface"
; principle (CLAUDE.md), only once a real wall was hit doing this purely in
; my-lisp.
;
; A CLIPS variable's own name becomes the `(var name)` term's name (`?x` ->
; `(var x)`, dropping only the `?`) — not renamed or namespaced, so the
; same `?x` used twice in one rule still refers to the same logic variable
; after conversion, exactly as CLIPS (and `lib/unify.lisp`) both expect.
;
; Крок 2: defrule, з CLIPS-синтаксисом змінних `?x` — CLIPS-змінні для
; reader'а my-lisp — звичайні символи (`?x` парситься як один атомарний
; символ, не reader-macro синтаксис), але my-lisp не мала способу
; перевірити символи символу сама. `symbol->string`/`string->symbol`/
; `string-first`/`string-rest` додані саме для цього: відрізати `?` від
; `?x`, щоб побудувати терм логічної змінної `(var x)`, якого чекає
; `lib/unify.lisp`. Додано свідомо, не за звичкою — за власним принципом
; проєкту "не розширювати поверхню Rust" (CLAUDE.md), лише коли впёрлись у
; реальну стіну, роблячи це чистою my-lisp.
;
; Власне ім'я CLIPS-змінної стає ім'ям терму `(var name)` (`?x` -> `(var
; x)`, відрізається лише `?`) — не перейменовується й не намespace-иться,
; тож той самий `?x`, використаний двічі в одному правилі, після конвертації
; й далі посилається на ту саму логічну змінну, точно як і CLIPS (і
; `lib/unify.lisp`) обидва очікують.
;
; Schritt 2: defrule, mit CLIPS' `?x`-Variablensyntax — CLIPS-Variablen
; sind für den my-lisp-Reader gewöhnliche Symbole (`?x` parst als ein
; atomares Symbol, keine Reader-Makro-Syntax), aber my-lisp konnte die
; Zeichen eines Symbols nicht selbst inspizieren.
; `symbol->string`/`string->symbol`/`string-first`/`string-rest` wurden
; genau dafür hinzugefügt: das `?` von `?x` abzuschälen, um den
; Logikvariablen-Term `(var x)` zu bauen, den `lib/unify.lisp` erwartet.
; Bewusst hinzugefügt, nicht beiläufig — nach dem eigenen Prinzip des
; Projekts, die Rust-Oberfläche nicht wachsen zu lassen (CLAUDE.md), erst
; als eine echte Grenze beim rein-my-lisp-Ansatz erreicht wurde.
;
; Der eigene Name einer CLIPS-Variable wird zum Namen des `(var
; name)`-Terms (`?x` -> `(var x)`, nur das `?` wird entfernt) — nicht
; umbenannt oder mit Namensraum versehen, sodass dasselbe `?x`, zweimal in
; einer Regel verwendet, nach der Konvertierung weiterhin dieselbe
; Logikvariable bezeichnet, genau wie CLIPS (und `lib/unify.lisp`) es beide
; erwarten.
; Guards on `symbol?` first: `term` may be any atom (a CLIPS fact's
; argument can just as easily be a number, e.g. `(temperature 98)`), and
; `symbol->string` (called by `clips-symbol-starts-with-?`) errors on
; anything that isn't actually a symbol.
(00001001 clips-var?
  (00001000 (term)
    (00000111
      ((0100 (00000010 term)) (00000111
         ((00100011 term) (clips-symbol-starts-with-? term))
         (t (00000001 ()))))
      ((00000010 term)  (00000111
         ((00100011 term) (clips-symbol-starts-with-? term))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 clips-symbol-starts-with-?
  (00001000 (symbol)
    (00100010 (00111111 (01000010 symbol)) (00111111 "?_"))))

(00001001 clips-var-term
  (00001000 (symbol)
    (00100111 (00000001 var) (01000011 (01000000 (01000010 symbol))))))

; Walks an arbitrary CLIPS term, replacing every `?x`-shaped symbol with
; `(var x)` and leaving everything else untouched.
(00001001 clips-convert-vars
  (00001000 (term)
    (00000111
      ((clips-var? term) (clips-var-term term))
      
      ((00000010 term)  term)
      (t (00000100 (clips-convert-vars (00000101 term)) (clips-convert-vars (00000110 term)))))))

; Splits a defrule's body at `=>` into (conditions . conclusion-forms).
; Guards the `=>`-check with `(atom (car body))` first: a condition like
; `(planet ?x)` is itself a compound list, and `eq` errors on non-atom
; arguments instead of just correctly answering "not the `=>` marker".
(00001001 clips-split-at-arrow
  (00001000 (body)
    (00000111
      ((0100 (00000010 body)) (00100111 (00000001 ()) (00000001 ())))
      ((00000010 body)  (00100111 (00000001 ()) (00000001 ())))
      ((0100 (00000010 (00000101 body))) (00000111
         ((00000011 (00000101 body) (00000001 =>)) (00100111 (00000001 ()) (00000110 body)))
         (t (10011100 ((rest (clips-split-at-arrow (00000110 body))))
              (00100111 (00000100 (00000101 body) (00000101 rest)) (00101111 rest))))))
      ((00000010 (00000101 body))  (00000111
         ((00000011 (00000101 body) (00000001 =>)) (00100111 (00000001 ()) (00000110 body)))
         (t (10011100 ((rest (clips-split-at-arrow (00000110 body))))
              (00100111 (00000100 (00000101 body) (00000101 rest)) (00101111 rest))))))
      (t (10011100 ((rest (clips-split-at-arrow (00000110 body))))
           (00100111 (00000100 (00000101 body) (00000101 rest)) (00101111 rest)))))))

; Step 3: any number of `(assert (...))` forms after `=>`, not just one.
; my-lisp's rule format only ever has one head per clause, so N assertions
; sharing one LHS become N separate clauses, one per assertion, all with
; the *same* condition list — logically equivalent to CLIPS firing all N
; assertions together whenever the shared conditions hold.
;
; Still scoped to `assert` only: a `defrule` whose `=>` side contains any
; other CLIPS action (`printout`, `retract`, `modify`, ...) imports as no
; clauses rather than guessing at an action this project doesn't model —
; same "skip, don't error" policy as an unsupported top-level form.
;
; Крок 3: будь-яка кількість форм `(assert (...))` після `=>`, не лише
; одна. Формат правил my-lisp має рівно одну голову на clause, тож N
; тверджень з однією LHS стають N окремими clause, по одному на кожне
; твердження, усі з тим самим списком умов — логічно еквівалентно тому, як
; CLIPS застосовує всі N тверджень разом, коли спільні умови виконані.
;
; Досі обмежено лише `assert`: `defrule`, чия сторона `=>` містить будь-яку
; іншу CLIPS-дію (`printout`, `retract`, `modify`, ...), імпортується як
; відсутність clause замість здогадки про дію, яку цей проєкт не моделює —
; та сама політика "пропустити, не впасти", що й для непідтримуваної
; форми верхнього рівня.
;
; Schritt 3: beliebig viele `(assert (...))`-Formen nach `=>`, nicht nur
; eine. Das Regelformat von my-lisp hat immer nur einen Kopf pro Clause,
; also werden N Behauptungen mit einer gemeinsamen LHS zu N separaten
; Clauses, eine pro Behauptung, alle mit derselben Bedingungsliste —
; logisch äquivalent dazu, dass CLIPS alle N Behauptungen zusammen auslöst,
; sobald die gemeinsamen Bedingungen erfüllt sind.
;
; Weiterhin nur auf `assert` beschränkt: eine `defrule`, deren `=>`-Seite
; irgendeine andere CLIPS-Aktion enthält (`printout`, `retract`, `modify`,
; ...), importiert als keine Clauses, statt eine Aktion zu erraten, die
; dieses Projekt nicht modelliert — dieselbe "überspringen statt
; fehlschlagen"-Politik wie bei einer nicht unterstützten Form der obersten
; Ebene.
(00001001 clips-assert-form?
  (00001000 (form)
    (00000111
      
      ((00000010 form)  (00000001 ()))
      ((0100 (00000010 (00000101 form))) (00000011 (00000101 form) (00000001 assert)))
      ((00000010 (00000101 form))  (00000011 (00000101 form) (00000001 assert)))
      (t (00000001 ())))))

; Step 9: `printout` alongside `assert` no longer disqualifies a whole
; rule. Verified before writing this (not guessed): a rule shaped
; `(defrule mass-rule (planet ?x) => (printout t "found planet " ?x crlf)
; (assert (has-mass ?x)))` — an extremely ordinary CLIPS pattern, debug
; output next to the actual assertion — previously imported as *no
; clauses at all*, silently dropping a perfectly representable `assert`
; just because a harmless side-effecting `printout` sat next to it.
; `printout` writes to a stream and asserts nothing; my-lisp has no
; matching capability to run it in, but running nothing is exactly the
; same as CLIPS not having anything meaningful to assert from it — safe
; to drop, not to treat as disqualifying.
;
; Still no such leniency for `retract`/`modify`: both refer to a specific
; already-asserted fact by its CLIPS fact-address, a concept this
; project's set-of-facts model has no equivalent for (my-lisp facts are
; compared structurally via `equal?`, not addressed by identity) — a rule
; containing either still imports as no clauses rather than guessing at
; semantics it cannot faithfully represent.
;
; Крок 9: `printout` поряд з `assert` більше не дискваліфікує все
; правило. Перевірено перед написанням (не здогадано): правило форми
; `(defrule mass-rule (planet ?x) => (printout t "found planet " ?x crlf)
; (assert (has-mass ?x)))` — надзвичайно звичайний CLIPS-патерн,
; debug-вивід поряд із самим твердженням — раніше імпортувалось як
; *взагалі відсутність clause*, мовчки відкидаючи цілком представний
; `assert` лише тому, що поруч сидів нешкідливий `printout` з побічним
; ефектом. `printout` пише в потік і нічого не стверджує; my-lisp не має
; відповідної можливості його виконати, але виконати нічого — точно те
; саме, що й CLIPS без нічого осмисленого для ствердження звідти —
; безпечно відкинути, не трактувати як дискваліфікуючу.
;
; Досі без такої поблажки для `retract`/`modify`: обидва посилаються на
; конкретний уже ствердений факт за його CLIPS fact-address, поняття, для
; якого модель множини фактів цього проєкту не має відповідника (факти
; my-lisp порівнюються структурно через `equal?`, не адресуються за
; ідентичністю) — правило з будь-яким із них і далі імпортується як
; відсутність clause замість здогадки про семантику, яку не можна чесно
; представити.
;
; Schritt 9: `printout` neben `assert` disqualifiziert eine Regel nicht
; mehr vollständig. Vor dem Schreiben verifiziert (nicht geraten): eine
; Regel der Form `(defrule mass-rule (planet ?x) => (printout t "found
; planet " ?x crlf) (assert (has-mass ?x)))` — ein äußerst gewöhnliches
; CLIPS-Muster, Debug-Ausgabe neben der eigentlichen Behauptung — wurde
; zuvor als *überhaupt keine Clauses* importiert und verwarf
; stillschweigend eine perfekt darstellbare `assert`-Anweisung nur, weil
; ein harmloser `printout`-Seiteneffekt daneben stand. `printout` schreibt
; in einen Stream und behauptet nichts; my-lisp hat keine passende
; Fähigkeit, es auszuführen, aber nichts auszuführen ist genau dasselbe,
; wie wenn CLIPS nichts Sinnvolles daraus zu behaupten hätte — sicher zu
; verwerfen, nicht als disqualifizierend zu behandeln.
;
; Weiterhin keine solche Nachsicht für `retract`/`modify`: beide beziehen
; sich auf einen bestimmten, bereits behaupteten Fakt über seine
; CLIPS-Fakt-Adresse, ein Konzept, für das das Mengen-von-Fakten-Modell
; dieses Projekts kein Äquivalent hat (my-lisp-Fakten werden strukturell
; über `equal?` verglichen, nicht über Identität adressiert) — eine Regel
; mit einem von beiden importiert weiterhin als keine Clauses, statt eine
; Semantik zu erraten, die nicht treu dargestellt werden kann.
(00001001 clips-printout-form?
  (00001000 (form)
    (00000111
      
      ((00000010 form)  (00000001 ()))
      ((0100 (00000010 (00000101 form))) (00000011 (00000101 form) (00000001 printout)))
      ((00000010 (00000101 form))  (00000011 (00000101 form) (00000001 printout)))
      (t (00000001 ())))))

(00001001 clips-drop-printouts
  (00001000 (forms)
    (00000111
      
      ((00000010 forms)  (00000001 ()))
      ((clips-printout-form? (00000101 forms)) (clips-drop-printouts (00000110 forms)))
      (t (00000100 (00000101 forms) (clips-drop-printouts (00000110 forms)))))))

(00001001 clips-all-asserts?
  (00001000 (forms)
    (00000111
      
      ((00000010 forms)  t)
      ((clips-assert-form? (00000101 forms)) (clips-all-asserts? (00000110 forms)))
      (t (00000001 ())))))

; Step 15: real CLIPS `assert` accepts *multiple* facts in one call —
; `(assert (number 0) (number 1) (number 2) ...)`, not just one. Verified
; against a genuine external `.clp` file, not a hand-written example:
; importing the classic GERALD+DONALD=ROBERT word-puzzle from CLIPS's own
; distributed examples (see tests/fixtures/wordgame-external.clp), its
; `startup` rule's single `(assert (number 0) (number 1) ... (letter T))`
; call — twenty facts — only ever produced `(number 0)`; the other
; nineteen silently vanished, because `(second (car forms))` only ever
; read the *first* fact argument out of each `assert` form. `(cdr (car
; forms))` reads *every* fact argument instead, `append`-ed across every
; `assert` form in the RHS (a rule can still have more than one `assert`
; call, each itself multi-fact).
;
; Крок 15: справжній CLIPS `assert` приймає **кілька** фактів за один
; виклик — `(assert (number 0) (number 1) (number 2) ...)`, не лише один.
; Перевірено на справжньому зовнішньому `.clp`-файлі, не вигаданому
; прикладі: імпортуючи класичну задачу GERALD+DONALD=ROBERT з офіційних
; прикладів CLIPS (див. tests/fixtures/wordgame-external.clp), її правило
; `startup` з одним викликом `(assert (number 0) (number 1) ... (letter
; T))` — двадцять фактів — давало лише `(number 0)`; решта дев'ятнадцять
; мовчки зникали, бо `(second (car forms))` читав лише *перший* аргумент-
; факт з кожної форми `assert`. `(cdr (car forms))` читає *кожен*
; аргумент-факт, `append`-нуто через усі форми `assert` у RHS (правило
; й далі може мати кілька викликів `assert`, кожен сам по собі
; багатофактовий).
;
; Schritt 15: echtes CLIPS-`assert` akzeptiert **mehrere** Fakten in einem
; Aufruf — `(assert (number 0) (number 1) (number 2) ...)`, nicht nur
; einen. Verifiziert gegen eine echte externe `.clp`-Datei, kein
; handgeschriebenes Beispiel: beim Import des klassischen
; GERALD+DONALD=ROBERT-Worträtsels aus CLIPS' eigenen mitgelieferten
; Beispielen (siehe tests/fixtures/wordgame-external.clp) lieferte der
; einzelne `(assert (number 0) (number 1) ... (letter T))`-Aufruf der
; `startup`-Regel — zwanzig Fakten — nur `(number 0)`; die anderen
; neunzehn verschwanden stillschweigend, weil `(second (car forms))` nur
; das *erste* Fakt-Argument jeder `assert`-Form las. `(cdr (car forms))`
; liest *jedes* Fakt-Argument, über alle `assert`-Formen der RHS
; `append`-t (eine Regel kann weiterhin mehrere `assert`-Aufrufe haben,
; jeder selbst mehrfaktig).
(00001001 clips-assert-conclusions
  (00001000 (forms)
    (00000111
      
      ((00000010 forms)  (00000001 ()))
      (t (00101001 (00000110 (00000101 forms)) (clips-assert-conclusions (00000110 forms)))))))

(00001001 clips-clauses-for-conclusions
  (00001000 (conclusions conditions)
    (00000111
      
      ((00000010 conclusions)  (00000001 ()))
      (t (00000100 (00000100 (clips-convert-vars (00000101 conclusions)) conditions)
                (clips-clauses-for-conclusions (00000110 conclusions) conditions))))))

; Step 5 (superseded — history kept, not silently erased): originally
; detected CLIPS's `(not (pattern))` conditions and skipped the whole rule,
; because `lib/forward.lisp`'s `match-conditions` had no negation-as-failure
; handling and a naively-converted `(not ...)` condition would silently
; never fire. Step 6 (`lib/forward.lisp`'s `match-one-condition`/
; `match-negated-condition`) closed that gap directly in the forward
; engine, so `not` conditions now import and run correctly — the guard
; that used to skip them has been removed rather than left as a dead,
; misleadingly-named no-op.
;
; Крок 5 (замінено — історія збережена, не тихо стерта): раніше виявляв
; CLIPS-умови `(not (шаблон))` і пропускав усе правило, бо
; `match-conditions` у `lib/forward.lisp` не мав обробки negation-as-failure,
; і наївно конвертована `(not ...)` умова мовчки ніколи б не спрацювала.
; Крок 6 (`match-one-condition`/`match-negated-condition` у
; `lib/forward.lisp`) закрив цю прогалину напряму у forward-рушії, тож умови
; `not` тепер імпортуються й працюють коректно — guard, що їх пропускав,
; прибрано, а не залишено як мертвий, оманливо названий no-op.
;
; Schritt 5 (ersetzt — Historie erhalten, nicht still gelöscht): erkannte
; ursprünglich CLIPS' `(not (muster))`-Bedingungen und übersprang die ganze
; Regel, weil `match-conditions` in `lib/forward.lisp` keine
; Negation-als-Fehlschlag-Behandlung hatte und eine naiv konvertierte
; `(not ...)`-Bedingung still nie gefeuert hätte. Schritt 6
; (`match-one-condition`/`match-negated-condition` in `lib/forward.lisp`)
; schloss diese Lücke direkt in der Forward-Engine, sodass `not`-Bedingungen
; nun korrekt importiert werden und funktionieren — der Guard, der sie
; übersprang, wurde entfernt statt als toter, irreführend benannter No-op
; zurückzubleiben.
; Template conversion runs *before* `?x`-variable conversion: slot lookup
; matches on slot names and reorders values, and a value can just as
; easily be `?x` as `earth` at this point — either way it's carried
; through positionally unchanged, then `clips-convert-vars` turns any
; `?x`-shaped value into `(var x)` afterward.
; Step 16: strip a `defrule`'s optional preamble — a docstring (a bare
; string literal) and/or a `(declare (salience N))` property, both of
; which CLIPS allows directly after the rule name and before its
; conditions. Verified against a second genuine external `.clp` file (not
; guessed): CLIPS's own "Automotive Expert System" example
; (tests/fixtures/auto-external.clp) gives every single one of its 21
; rules an empty docstring `""`, and several a `(declare (salience N))` —
; without stripping them, both landed in the condition list as if they
; were patterns to match against facts. Neither a bare string nor a
; `declare` form is ever a fact's head, so every affected rule silently
; never fired — the entire file was dead on arrival, not just one rule.
; `string?` (crates/my-lisp/src/eval/special_forms.rs) was added
; specifically to tell a docstring apart from an ordinary condition term.
;
; Salience itself (CLIPS's rule-firing priority) has no equivalent here:
; `run-multi`/`run-jtms-multi` materialize every derivable fact to a
; fixpoint regardless of order, so which rule "goes first" never changes
; the final result — dropping `declare` loses information CLIPS would use
; to order *when* things fire, never *whether* they do.
;
; Крок 16: обрізає необов'язковий преамбул `defrule` — докстрінг (голий
; рядковий літерал) і/або властивість `(declare (salience N))`, обидва
; CLIPS дозволяє одразу після імені правила, перед умовами. Перевірено на
; другому справжньому зовнішньому `.clp`-файлі (не здогадано): власний
; приклад CLIPS "Automotive Expert System"
; (tests/fixtures/auto-external.clp) дає кожному зі своїх 21 правил
; порожній докстрінг `""`, а кільком — `(declare (salience N))` — без
; обрізання обидва потрапляли у список умов, ніби були шаблонами для
; зіставлення з фактами. Ні голий рядок, ні форма `declare` ніколи не є
; головою факту, тож кожне зачеплене правило мовчки ніколи не
; спрацьовувало — весь файл був мертвий одразу, не одне правило. `string?`
; додано саме для того, щоб відрізнити докстрінг від звичайного терму умови.
;
; Сама salience (пріоритет спрацювання правил CLIPS) не має тут
; відповідника: `run-multi`/`run-jtms-multi` матеріалізують кожен
; виводимий факт до fixpoint незалежно від порядку, тож яке правило
; "спрацьовує першим" ніколи не змінює фінальний результат — відкидання
; `declare` втрачає інформацію, яку CLIPS використав би, щоб впорядкувати
; *коли* щось спрацьовує, ніколи не *чи* спрацьовує.
;
; Schritt 16: entfernt die optionale Präambel einer `defrule` — einen
; Docstring (ein bloßes String-Literal) und/oder eine `(declare (salience
; N))`-Eigenschaft, beide erlaubt CLIPS direkt nach dem Regelnamen, vor den
; Bedingungen. Verifiziert gegen eine zweite echte externe `.clp`-Datei
; (nicht geraten): CLIPS' eigenes Beispiel "Automotive Expert System"
; (tests/fixtures/auto-external.clp) gibt jeder seiner 21 Regeln einen
; leeren Docstring `""`, mehreren ein `(declare (salience N))` — ohne
; Entfernung landeten beide in der Bedingungsliste, als wären sie Muster
; zum Abgleich gegen Fakten. Weder ein bloßer String noch eine
; `declare`-Form ist je der Kopf eines Fakts, also feuerte jede betroffene
; Regel still nie — die ganze Datei war von Anfang an tot, nicht nur eine
; Regel. `string?` wurde genau dafür hinzugefügt, einen Docstring von
; einem gewöhnlichen Bedingungsterm zu unterscheiden.
;
; Salience selbst (CLIPS' Feuerpriorität für Regeln) hat hier kein
; Äquivalent: `run-multi`/`run-jtms-multi` materialisieren jeden
; ableitbaren Fakt bis zum Fixpunkt, unabhängig von der Reihenfolge, also
; ändert es nie das Endergebnis, welche Regel "zuerst dran ist" — das
; Verwerfen von `declare` verliert Information, die CLIPS nutzen würde, um
; zu ordnen, *wann* etwas feuert, nie *ob*.
(00001001 clips-rule-preamble-form?
  (00001000 (form)
    (00000111
      ((00100100 form) t)
      
      ((00000010 form)  (00000001 ()))
      ((0100 (00000010 (00000101 form))) (00000011 (00000101 form) (00000001 declare)))
      ((00000010 (00000101 form))  (00000011 (00000101 form) (00000001 declare)))
      (t (00000001 ())))))

(00001001 clips-strip-rule-preamble
  (00001000 (body)
    (00000111
      
      ((00000010 body)  body)
      ((clips-rule-preamble-form? (00000101 body)) (clips-strip-rule-preamble (00000110 body)))
      (t body))))

; Step 19's `exists`/`forall` guard — skip a whole rule rather than
; import one that could never fire — is gone now that `lib/forward.lisp`
; Step 15 gives `exists`/`forall` real dispatcher support, the same way
; Step 5's `not` guard was removed once `lib/forward.lisp` Step 7 gave `not`
; real support. `clips-convert-template` also learned to recurse into
; `exists`/`forall` sub-conditions (same lesson Step 13 already taught for
; `not`/`or`/`and`), so a template fact nested inside either now gets its
; named slots converted to positional form too.
; Guard `exists`/`forall` із Кроку 19 — пропустити все правило замість
; імпорту того, що ніколи б не спрацювало — прибрано, тепер коли
; `lib/forward.lisp` Крок 15 дає `exists`/`forall` справжню диспетчерну
; підтримку, так само як guard `not` з Кроку 5 прибрано, коли
; `lib/forward.lisp` Крок 7 дав `not` справжню підтримку.
; `clips-convert-template` також навчилась рекурсувати в під-умови
; `exists`/`forall` (той самий урок, що Крок 13 уже дав для `not`/`or`/
; `and`), тож факт-шаблон, вкладений у будь-яку з них, тепер теж отримує
; конвертацію іменованих слотів у позиційну форму.
; Steps 19s `exists`/`forall`-Guard — die ganze Regel überspringen statt
; eine zu importieren, die nie feuern könnte — ist jetzt weg, da
; `lib/forward.lisp` Schritt 15 `exists`/`forall` echte Dispatcher-
; Unterstützung gibt, genauso wie Schritt 5s `not`-Guard entfernt wurde,
; als `lib/forward.lisp` Schritt 7 `not` echte Unterstützung gab.
; `clips-convert-template` hat auch gelernt, in `exists`/`forall`-
; Unterbedingungen zu rekursieren (dieselbe Lehre, die Schritt 13 bereits
; für `not`/`or`/`and` gab), sodass ein Template-Fakt, verschachtelt in
; einer von beiden, jetzt auch seine benannten Slots in positionale Form
; umgewandelt bekommt.
(00001001 clips-defrule->clauses
  (00001000 (form templates)
    (10011100 ((split (clips-split-at-arrow (clips-strip-rule-preamble (00110101 form)))))
      (10011100 ((conditions (clips-convert-vars (clips-convert-template-list (00000101 split) templates)))
            (relevant (clips-drop-printouts (00101111 split))))
        (00000111
          ((clips-all-asserts? relevant)
           (clips-clauses-for-conclusions
             (clips-convert-template-list (clips-assert-conclusions relevant) templates)
             conditions))
          (t (00000001 ())))))))

; Dispatches on one top-level CLIPS form's leading symbol. Unknown or
; not-yet-supported forms produce no clauses rather than erroring — a
; partial import of a mixed file still returns whatever it *could*
; translate. `deftemplate` itself produces no clauses (it only feeds the
; `templates` lookup `clips-import` builds once, up front).
(00001001 clips-form->clauses
  (00001000 (form templates)
    (00000111
      ((00000011 (00000101 form) (00000001 deffacts)) (clips-deffacts->clauses form templates))
      ((00000011 (00000101 form) (00000001 defrule)) (clips-defrule->clauses form templates))
      (t (00000001 ())))))

; Same non-tail-call problem as `clips-facts->clauses` above, one level up:
; `(append (clips-form->clauses ...) (clips-import-forms ...))` nests one
; Rust stack frame per top-level form. `animal-external.clp` (37 forms,
; one deffacts block of 128 facts) is exactly the file that first grew
; this deep enough to crash the process outright with a real stack
; overflow rather than a graceful error — found the same "verify with a
; throwaway debug test" way as every other importer bug this file
; documents. `clips-cons-each-onto` flattens one form's own clause list
; onto the running accumulator tail-recursively, so neither loop — across
; forms, or across one form's clauses — grows the native stack.
; Та сама проблема нехвостового виклику, що й у `clips-facts->clauses`
; вище, лише рівнем вище: `(append (clips-form->clauses ...)
; (clips-import-forms ...))` вкладає один Rust-стек-фрейм на кожну
; верхньорівневу форму. `animal-external.clp` (37 форм, один блок
; deffacts зі 128 фактів) — саме той файл, що вперше виріс достатньо
; глибоко, щоб реально впасти зі stack overflow замість коректної
; помилки — знайдено тим самим способом "спершу тимчасовий debug-тест",
; що й усі інші баги імпортера в цьому файлі. `clips-cons-each-onto`
; сплющує список clause однієї форми на робочий акумулятор хвостово-
; рекурсивно, тож жоден із циклів — ні по формах, ні по clause однієї
; форми — не росте нативний стек.
; Dasselbe Nicht-Tail-Call-Problem wie bei `clips-facts->clauses` oben,
; nur eine Ebene höher: `(append (clips-form->clauses ...)
; (clips-import-forms ...))` verschachtelt einen Rust-Stack-Frame pro
; Top-Level-Form. `animal-external.clp` (37 Formen, ein deffacts-Block
; mit 128 Fakten) ist genau die Datei, die das erstmals tief genug wachsen
; ließ, um mit einem echten Stack-Overflow abzustürzen statt einen
; ordentlichen Fehler zu liefern — gefunden auf demselben Weg "erst ein
; Wegwerf-Debug-Test" wie jeder andere Importer-Bug in dieser Datei.
; `clips-cons-each-onto` glättet die Clause-Liste einer Form tail-rekursiv
; auf den laufenden Akkumulator, sodass weder die Schleife über die Formen
; noch die über die Clauses einer Form den nativen Stack wachsen lässt.
(00001001 clips-cons-each-onto
  (00001000 (items acc)
    (00000111
      
      ((00000010 items)  acc)
      (t (clips-cons-each-onto (00000110 items) (00000100 (00000101 items) acc))))))

(00001001 clips-import-forms-onto
  (00001000 (forms templates acc)
    (00000111
      ((0100 (00000010 forms)) (00101010 acc))
      ((00000010 forms)  (00101010 acc))
      (t (clips-import-forms-onto
           (00000110 forms) templates
           (clips-cons-each-onto (clips-form->clauses (00000101 forms) templates) acc))))))

(00001001 clips-import-forms
  (00001000 (forms templates)
    (clips-import-forms-onto forms templates (00000001 ()))))

(00001001 clips-import
  (00001000 (forms)
    (clips-import-forms forms (clips-templates-from-forms forms))))

; Step 4: read a real CLIPS source file off disk and import it — the tool
; this whole file exists to build. `read-file` (new Rust primitive, see
; crates/my-lisp/src/eval/special_forms.rs's header comment on it) reads
; the raw text; `read-all` (also new) parses it into every top-level form
; as data, the multi-form counterpart to `read`; `clips-import` does the
; rest exactly as it would for a caller-supplied quoted literal.
;
; Крок 4: прочитати справжній CLIPS-файл з диска й імпортувати його —
; інструмент, заради якого існує весь цей файл. `read-file` (новий
; Rust-примітив) читає сирий текст; `read-all` (теж новий) парсить його в
; кожну форму верхнього рівня як дані — багатоформний відповідник `read`;
; `clips-import` робить решту точно так само, як і для наданого викликачем
; quoted-літералу.
;
; Schritt 4: eine echte CLIPS-Quelldatei von der Festplatte lesen und
; importieren — das Werkzeug, für das diese ganze Datei existiert.
; `read-file` (neues Rust-Primitiv) liest den rohen Text; `read-all`
; (ebenfalls neu) parst ihn in jede Form der obersten Ebene als Daten — das
; Mehrform-Gegenstück zu `read`; `clips-import` erledigt den Rest genau so
; wie für ein vom Aufrufer bereitgestelltes Quote-Literal.
(00001001 clips-import-file
  (00001000 (path)
    (clips-import (01001011 (10100110 path)))))
