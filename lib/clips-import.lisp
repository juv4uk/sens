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
(визначити кліпс-визначити-шаблон-форма?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((хибне? (атом? (перше форма))) ні)
      ((тотожне? (перше форма) (як-є deftemplate)) так)
      (так ні))))

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
(визначити кліпс-рядок-порожній? (функція (рядок) (тотожне? рядок "")))

; This is a D1 predicate, not a partial search returning NIL on failure.
; D3 COND can inspect only the exact one-bit results; empty/short strings,
; mismatched first character and mismatched second character are all D1:NO.
(визначити кліпс-рядок-починається-з-подвійної-двокрапки?
  (функція (рядок)
    (за-умовою
      ((кліпс-рядок-порожній? рядок) ні)
      ((кліпс-рядок-порожній? (рядок-решта рядок)) ні)
      ((тотожне? (рядок-перший рядок) ":") (тотожне? (рядок-перший (рядок-решта рядок)) ":"))
      (так ні))))

(визначити кліпс-рядок-після-останньої-подвійної-двокрапки
  (функція (рядок)
    (за-умовою
      ((кліпс-рядок-порожній? рядок) (як-є ()))
      ((кліпс-рядок-починається-з-подвійної-двокрапки? рядок)
       ((функція (залишок)
          (за-умовою
            ((тотожне? залишок (як-є ())) (рядок-решта (рядок-решта рядок)))
            (так залишок)))
        (кліпс-рядок-після-останньої-подвійної-двокрапки (рядок-решта (рядок-решта рядок)))))
      (так (кліпс-рядок-після-останньої-подвійної-двокрапки (рядок-решта рядок))))))

(визначити прибрати-префікс-модуля-кліпс
  (функція (позначення)
    (за-умовою
      ((символ? позначення)
       ((функція (залишок)
          (за-умовою
            ((тотожне? залишок (як-є ())) позначення)
            (так (текст-у-символ залишок))))
        (кліпс-рядок-після-останньої-подвійної-двокрапки (символ-у-текст позначення))))
      (так позначення))))

(визначити кліпс-визначити-шаблон-ім'я (функція (форма) (прибрати-префікс-модуля-кліпс (друге форма))))

(визначити кліпс-слот-ім'я (функція (форма-слота) (друге форма-слота)))

(визначити кліпс-слот-імена
  (функція (форми-слотів)
    (за-умовою
      
      ((атом? форми-слотів)  (як-є ()))
      (так (сполучити (кліпс-слот-ім'я (перше форми-слотів)) (кліпс-слот-імена (решта форми-слотів)))))))

(визначити кліпс-визначити-шаблон-слоти
  (функція (форма)
    (кліпс-слот-імена (решта-решти форма))))

(визначити кліпс-шаблони-з-форми
  (функція (форми)
    (за-умовою
      
      ((атом? форми)  (як-є ()))
      ((кліпс-визначити-шаблон-форма? (перше форми))
       (сполучити (сполучити (кліпс-визначити-шаблон-ім'я (перше форми)) (кліпс-визначити-шаблон-слоти (перше форми)))
             (кліпс-шаблони-з-форми (решта форми))))
      (так (кліпс-шаблони-з-форми (решта форми))))))

; A template registry is a list of (atomic-name . slot-order) pairs.
; This derived lookup needs no D5 ASSOC / D8 EQUAL callable admission.
; Empty or malformed entries fail closed as data (), not D1:NO.
(визначити кліпс-шаблон-слот-порядок
  (функція (назва шаблони)
    (за-умовою
      ((хибне? (атом? назва)) (як-є ()))
      ((атом? шаблони) (як-є ()))
      ((атом? (перше шаблони))
       (кліпс-шаблон-слот-порядок назва (решта шаблони)))
      ((хибне? (атом? (перше (перше шаблони))))
       (кліпс-шаблон-слот-порядок назва (решта шаблони)))
      ((тотожне? назва (перше (перше шаблони))) (решта (перше шаблони)))
      (так (кліпс-шаблон-слот-порядок назва (решта шаблони))))))

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
(визначити кліпс-значення-слота
  (функція (форма-слота)
    (за-умовою
      
      ((атом? (решта форма-слота))  (як-є ()))
      (так (друге форма-слота)))))

; Точний D3 пошук атомарної назви CLIPS-слота.
; Коректний слот = (назва значення). У разі складеної назви
; пропускаємо запис; голий атом замість слота теж пропускаємо.
; Не можна відкидати кожний непорожній список: порівняння
; тоді недосяжне. Рядки в кліпс-символ-починається-з-питальника? і далі D8 EQUAL.

(визначити знайти-значення-слота-кліпс
  (функція (назва-слота форми-слотів)
    (за-умовою
      
      ((атом? форми-слотів)  (як-є ()))
      ((атом? (перше форми-слотів))  (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))
      ((хибне? (атом? (перше (перше форми-слотів)))) (знайти-значення-слота-кліпс назва-слота (решта форми-слотів)))
      ((тотожне? назва-слота (перше (перше форми-слотів))) (кліпс-значення-слота (перше форми-слотів)))
      (так (знайти-значення-слота-кліпс назва-слота (решта форми-слотів))))))

(визначити позиційні-аргументи-кліпс
  (функція (порядок-слотів форми-слотів)
    (за-умовою
      
      ((атом? порядок-слотів)  (як-є ()))
      (так (сполучити (знайти-значення-слота-кліпс (перше порядок-слотів) форми-слотів)
                (позиційні-аргументи-кліпс (решта порядок-слотів) форми-слотів))))))

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
(визначити кліпс-перетворити-шаблон
  (функція (терм шаблони)
    (за-умовою
      
      ((атом? терм)  терм)
      ((хибне? (атом? (перше терм))) (за-умовою
         ((тотожне? (перше терм) (як-є not)) (список (як-є not?) (кліпс-перетворити-шаблон (друге терм) шаблони)))
         ((тотожне? (перше терм) (як-є or)) (сполучити (як-є or) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є and)) (сполучити (як-є and) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є exists)) (сполучити (як-є exists) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є forall)) (сполучити (як-є forall) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         (так ((функція (порядок-слотів)
              (за-умовою
                
                ((атом? порядок-слотів)  терм)
                (так (сполучити (перше терм) (позиційні-аргументи-кліпс порядок-слотів (решта терм)))))) (кліпс-шаблон-слот-порядок (прибрати-префікс-модуля-кліпс (перше терм)) шаблони)))))
      ((атом? (перше терм))  (за-умовою
         ((тотожне? (перше терм) (як-є not)) (список (як-є not?) (кліпс-перетворити-шаблон (друге терм) шаблони)))
         ((тотожне? (перше терм) (як-є or)) (сполучити (як-є or) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є and)) (сполучити (як-є and) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є exists)) (сполучити (як-є exists) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         ((тотожне? (перше терм) (як-є forall)) (сполучити (як-є forall) (кліпс-перетворити-шаблон-список (решта терм) шаблони)))
         (так ((функція (порядок-слотів)
              (за-умовою
                
                ((атом? порядок-слотів)  терм)
                (так (сполучити (перше терм) (позиційні-аргументи-кліпс порядок-слотів (решта терм)))))) (кліпс-шаблон-слот-порядок (прибрати-префікс-модуля-кліпс (перше терм)) шаблони)))))
      (так терм))))

(визначити кліпс-перетворити-шаблон-список
  (функція (терми шаблони)
    (за-умовою
      
      ((атом? терми)  (як-є ()))
      (так (сполучити (кліпс-перетворити-шаблон (перше терми) шаблони)
                (кліпс-перетворити-шаблон-список (решта терми) шаблони))))))

(визначити кліпс-факт-клауза
  (функція (факт) (список факт)))

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
(визначити кліпс-факти-у-клаузи-дописати
  (функція (факти шаблони накопичені)
    (за-умовою
      ((атом? факти) (зворот накопичені))
      (так (кліпс-факти-у-клаузи-дописати
           (решта факти) шаблони
           (сполучити (кліпс-факт-клауза (кліпс-перетворити-шаблон (перше факти) шаблони)) накопичені))))))

(визначити кліпс-факти-клаузи
  (функція (факти шаблони)
    (кліпс-факти-у-клаузи-дописати факти шаблони (як-є ()))))

; `(cddr form)` drops `deffacts` and the deffacts block's own name,
; leaving just the fact list.
(визначити кліпс-визначити-факти-клаузи
  (функція (форма шаблони)
    (кліпс-факти-клаузи (решта-решти форма) шаблони)))

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
; `symbol->string` (called by `кліпс-символ-починається-з-питальника?`) errors on
; anything that isn't actually a symbol.
; Only atoms may be variable symbols. D1:NO is explicit
; for pairs and non-symbol atoms; no historical truthy NIL/UNKNOWN.
(визначити кліпс-змінна?
  (функція (терм)
    (за-умовою
      ((атом? терм)
       (за-умовою
         ((символ? терм) (кліпс-символ-починається-з-питальника? терм))
         (так ні)))
      (так ні))))

; Both projections are atoms, so admitted D3 EQ suffices;
; D8 EQUAL is neither needed nor implicitly admitted here.
(визначити кліпс-символ-починається-з-питальника?
  (функція (символ)
    (тотожне? (рядок-перший (символ-у-текст символ)) (рядок-перший "?_"))))

(визначити кліпс-змінна-терм
  (функція (символ)
    (список (як-є var) (текст-у-символ (рядок-решта (символ-у-текст символ))))))

; Walks an arbitrary CLIPS term, replacing every `?x`-shaped symbol with
; `(var x)` and leaving everything else untouched.
(визначити кліпс-перетворити-змінні
  (функція (терм)
    (за-умовою
      ((кліпс-змінна? терм) (кліпс-змінна-терм терм))
      
      ((атом? терм)  терм)
      (так (сполучити (кліпс-перетворити-змінні (перше терм)) (кліпс-перетворити-змінні (решта терм)))))))

; Splits a defrule's body at `=>` into (conditions . conclusion-forms).
; Guards the `=>`-check with `(atom (car body))` first: a condition like
; `(planet ?x)` is itself a compound list, and `eq` errors on non-atom
; arguments instead of just correctly answering "not the `=>` marker".
(визначити розділити-правило-кліпс
  (функція (тіло)
    (за-умовою
      ((атом? тіло) (список (як-є ()) (як-є ())))
      ((атом? (перше тіло))
       (за-умовою
         ((тотожне? (перше тіло) (як-є =>)) (список (як-є ()) (решта тіло)))
         (так ((функція (решта-форм)
              (список (сполучити (перше тіло) (перше решта-форм)) (друге решта-форм)))
              (розділити-правило-кліпс (решта тіло))))))
      (так ((функція (решта-форм)
           (список (сполучити (перше тіло) (перше решта-форм)) (друге решта-форм)))
           (розділити-правило-кліпс (решта тіло)))))))

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
(визначити твердження-кліпс?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((атом? (перше форма)) (тотожне? (перше форма) (як-є assert)))
      (так ні))))

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
(визначити виведення-кліпс?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((атом? (перше форма)) (тотожне? (перше форма) (як-є printout)))
      (так ні))))

(визначити прибрати-виведення-кліпс
  (функція (форми)
    (за-умовою
      
      ((атом? форми)  (як-є ()))
      ((виведення-кліпс? (перше форми)) (прибрати-виведення-кліпс (решта форми)))
      (так (сполучити (перше форми) (прибрати-виведення-кліпс (решта форми)))))))

(визначити усі-твердження-кліпс?
  (функція (форми)
    (за-умовою
      ((атом? форми) так)
      ((твердження-кліпс? (перше форми)) (усі-твердження-кліпс? (решта форми)))
      (так ні))))

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
(визначити зібрати-висновки-кліпс
  (функція (форми)
    (за-умовою
      
      ((атом? форми)  (як-є ()))
      (так (приєднати (решта (перше форми)) (зібрати-висновки-кліпс (решта форми)))))))

(визначити правила-для-висновків-кліпс
  (функція (висновки умови)
    (за-умовою
      
      ((атом? висновки)  (як-є ()))
      (так (сполучити (сполучити (кліпс-перетворити-змінні (перше висновки)) умови)
                (правила-для-висновків-кліпс (решта висновки) умови))))))

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
; CLIPS grammar: at rule preamble, an atom other than => is the
; optional documentation datum; valid conditions and (declare ...) are pairs.
; This is a position-specific SENS structural law, NOT a general stringp.
; Do not grant the unadmitted D9:110100110 STRINGP runtime authority.
(визначити преамбула-правила-кліпс?
  (функція (форма)
    (за-умовою
      ((атом? форма)
       (за-умовою
         ((тотожне? форма (як-є =>)) ні)
         (так так)))
      ((хибне? (атом? (перше форма))) ні)
      ((тотожне? (перше форма) (як-є declare)) так)
      (так ні))))

(визначити прибрати-преамбулу-кліпс
  (функція (тіло)
    (за-умовою
      
      ((атом? тіло)  тіло)
      ((преамбула-правила-кліпс? (перше тіло)) (прибрати-преамбулу-кліпс (решта тіло)))
      (так тіло))))

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
; Each intermediate list is computed once by language-owned derived
; functions. No ambiguous computed LAMBDA head or unadmitted LET slot.
(визначити кліпс-клаузи-правила-з-частин
  (функція (умови доречні шаблони)
    (за-умовою
      ((усі-твердження-кліпс? доречні)
       (правила-для-висновків-кліпс
         (кліпс-перетворити-шаблон-список (зібрати-висновки-кліпс доречні) шаблони)
         умови))
      (так (як-є ())))))

(визначити кліпс-клаузи-правила-з-розділу
  (функція (поділ шаблони)
    (кліпс-клаузи-правила-з-частин
      (кліпс-перетворити-змінні (кліпс-перетворити-шаблон-список (перше поділ) шаблони))
      (прибрати-виведення-кліпс (друге поділ))
      шаблони)))

(визначити кліпс-визначити-правило-клаузи
  (функція (форма шаблони)
    (кліпс-клаузи-правила-з-розділу
      (розділити-правило-кліпс (прибрати-преамбулу-кліпс (решта-решти форма)))
      шаблони)))

; Dispatches on one top-level CLIPS form's leading symbol. Unknown or
; not-yet-supported forms produce no clauses rather than erroring — a
; partial import of a mixed file still returns whatever it *could*
; translate. `deftemplate` itself produces no clauses (it only feeds the
; `templates` lookup `clips-import` builds once, up front).
(визначити кліпс-форма-клаузи
  (функція (форма шаблони)
    (за-умовою
      ((атом? форма) (як-є ()))
      ((хибне? (атом? (перше форма))) (як-є ()))
      ((тотожне? (перше форма) (як-є deffacts)) (кліпс-визначити-факти-клаузи форма шаблони))
      ((тотожне? (перше форма) (як-є defrule)) (кліпс-визначити-правило-клаузи форма шаблони))
      (так (як-є ())))))

; Same non-tail-call problem as `clips-facts->clauses` above, one level up:
; `(append (clips-form->clauses ...) (clips-import-forms ...))` nests one
; Rust stack frame per top-level form. `animal-external.clp` (37 forms,
; one deffacts block of 128 facts) is exactly the file that first grew
; this deep enough to crash the process outright with a real stack
; overflow rather than a graceful error — found the same "verify with a
; throwaway debug test" way as every other importer bug this file
; documents. `кліпс-сполучити-кожен-дописати` flattens one form's own clause list
; onto the running accumulator tail-recursively, so neither loop — across
; forms, or across one form's clauses — grows the native stack.
; Та сама проблема нехвостового виклику, що й у `clips-facts->clauses`
; вище, лише рівнем вище: `(append (clips-form->clauses ...)
; (clips-import-forms ...))` вкладає один Rust-стек-фрейм на кожну
; верхньорівневу форму. `animal-external.clp` (37 форм, один блок
; deffacts зі 128 фактів) — саме той файл, що вперше виріс достатньо
; глибоко, щоб реально впасти зі stack overflow замість коректної
; помилки — знайдено тим самим способом "спершу тимчасовий debug-тест",
; що й усі інші баги імпортера в цьому файлі. `кліпс-сполучити-кожен-дописати`
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
; `кліпс-сполучити-кожен-дописати` glättet die Clause-Liste einer Form tail-rekursiv
; auf den laufenden Akkumulator, sodass weder die Schleife über die Formen
; noch die über die Clauses einer Form den nativen Stack wachsen lässt.
(визначити кліпс-сполучити-кожен-дописати
  (функція (елементи накопичені)
    (за-умовою
      
      ((атом? елементи)  накопичені)
      (так (кліпс-сполучити-кожен-дописати (решта елементи) (сполучити (перше елементи) накопичені))))))

(визначити кліпс-імпорт-форм-дописати
  (функція (форми шаблони накопичені)
    (за-умовою
      ((атом? форми) (зворот накопичені))
      (так (кліпс-імпорт-форм-дописати
           (решта форми) шаблони
           (кліпс-сполучити-кожен-дописати (кліпс-форма-клаузи (перше форми) шаблони) накопичені))))))

(визначити кліпс-імпорт-форми
  (функція (форми шаблони)
    (кліпс-імпорт-форм-дописати форми шаблони (як-є ()))))

(визначити кліпс-імпорт
  (функція (форми)
    (кліпс-імпорт-форми форми (кліпс-шаблони-з-форми форми))))

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
(визначити кліпс-імпорт-файл
  (функція (шлях)
    (кліпс-імпорт (читати-всі (читати-файл шлях)))))

; D9 exact-width Ukrainian projections of native CLIPS S-expression importer.
; Source laws are the Lisp closures above; no new parser, Rust semantics or opcode.
; D9:010110100
(визначити clips-deftemplate-форма? кліпс-визначити-шаблон-форма?)
; D9:001110111
(визначити clips-слот-імена кліпс-слот-імена)
; D9:001100110
(визначити clips-deftemplate-слоти кліпс-визначити-шаблон-слоти)
; D9:001010011
(визначити clips-шаблони-з-форми кліпс-шаблони-з-форми)
; D9:001010101
(визначити clips-шаблон-слот-порядок кліпс-шаблон-слот-порядок)
; D9:010001111
(визначити clips-перетворити-шаблон кліпс-перетворити-шаблон)
; D9:010001101
(визначити clips-перетворити-шаблон-список кліпс-перетворити-шаблон-список)
; D9:010111000
(визначити clips-факт-клауза кліпс-факт-клауза)
; D9:001110001
(визначити clips-факти-клаузи кліпс-факти-клаузи)
; D9:010010000
(визначити clips-deffacts-клаузи кліпс-визначити-факти-клаузи)
; D9:001110100
(визначити clips-змінна? кліпс-змінна?)
; D9:101000111
(визначити clips-перетворити-змінні кліпс-перетворити-змінні)

; D9: точні 9-бітні ідентичності — lib/domains/d9.lisp.
; Чинні закони залишаються в SENS-донорі вище, не в Rust чи Zig.
; Ці DEFINE зв'язують українські поверхні; це не автоматичний D9 opcode.
; D9:001101010
(визначити clips-deftemplate-ім'я кліпс-визначити-шаблон-ім'я)
; D9:001011110
(визначити clips-змінна-терм кліпс-змінна-терм)
; D9:010001001
(визначити clips-defrule-клаузи кліпс-визначити-правило-клаузи)
; D9:010100000
(визначити clips-форма-клаузи кліпс-форма-клаузи)

; Українські D9-поверхні. Точні коди — lib/domains/d9.lisp.
; Виконання належить уже визначеним SENS-функціям, не Rust registry/opcode.
; D9:001000001
(визначити clips-імпорт-форми кліпс-імпорт-форми)
; D9:001011000
(визначити clips-імпорт кліпс-імпорт)
; D9:001000100
(визначити clips-імпорт-файл кліпс-імпорт-файл)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити clips-all-asserts? усі-твердження-кліпс?)
(визначити clips-assert-conclusions зібрати-висновки-кліпс)
(визначити clips-assert-form? твердження-кліпс?)
(визначити clips-clauses-for-conclusions правила-для-висновків-кліпс)
(визначити clips-convert-template кліпс-перетворити-шаблон)
(визначити clips-convert-template-list кліпс-перетворити-шаблон-список)
(визначити clips-convert-vars кліпс-перетворити-змінні)
(визначити clips-deffacts->clauses кліпс-визначити-факти-клаузи)
(визначити clips-defrule->clauses кліпс-визначити-правило-клаузи)
(визначити clips-deftemplate-form? кліпс-визначити-шаблон-форма?)
(визначити clips-deftemplate-name кліпс-визначити-шаблон-ім'я)
(визначити clips-deftemplate-slots кліпс-визначити-шаблон-слоти)
(визначити clips-drop-printouts прибрати-виведення-кліпс)
(визначити clips-fact-clause кліпс-факт-клауза)
(визначити clips-facts->clauses кліпс-факти-клаузи)
(визначити clips-form->clauses кліпс-форма-клаузи)
(визначити clips-import кліпс-імпорт)
(визначити clips-import-forms кліпс-імпорт-форми)
(визначити clips-lookup-slot-value знайти-значення-слота-кліпс)
(визначити clips-positional-args позиційні-аргументи-кліпс)
(визначити clips-printout-form? виведення-кліпс?)
(визначити clips-rule-preamble-form? преамбула-правила-кліпс?)
(визначити clips-slot-name кліпс-слот-ім'я)
(визначити clips-slot-names кліпс-слот-імена)
(визначити clips-split-at-arrow розділити-правило-кліпс)
(визначити clips-strip-module-prefix прибрати-префікс-модуля-кліпс)
(визначити clips-strip-rule-preamble прибрати-преамбулу-кліпс)
(визначити clips-template-slot-order кліпс-шаблон-слот-порядок)
(визначити clips-templates-from-forms кліпс-шаблони-з-форми)
(визначити clips-var-term кліпс-змінна-терм)
(визначити clips-var? кліпс-змінна?)
; Зовнішня історична назва лишається посиланням на вже визначену українську функцію.
(визначити clips-import-file кліпс-імпорт-файл)
