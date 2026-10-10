;; knowledge.lisp - A module system for the Lisp Knowledge Representation

;; --- append-only fact journal --------------------------------------------
;; Earlier, `*knowledge-base*` held one snapshot per module — every
;; `defmodule`/`tell-knowledge` call replaced it outright. That snapshot
;; could never answer "when did the module learn this?", and there was no
;; way to take a fact back at all (`retract-knowledge` didn't exist).
;; `*knowledge-journal*` replaces it as the single source of truth: a
;; flat, ever-growing list of `(tell module-name clause)`/`(retract
;; module-name clause)` events, newest first (the same `cons`-prepend
;; convention `*working-memory*`/`*usage-counts*` already use elsewhere in
;; this project). No timestamps — my-lisp has no clock primitive, and
;; inventing one here would be exactly the kind of unearned precision
;; McCarthy principle 6 warns against; list order (oldest to newest once
;; reversed) is the only ordering this journal actually has, and it's
;; honest about that. A module's current clause list is now a *projection*
;; over the journal (`module-clauses-now`), computed on demand, not stored
;; anywhere directly.
;;
;; Раніше `*knowledge-base*` тримав один знімок на модуль — кожен виклик
;; `defmodule`/`tell-knowledge` повністю його переписував. Той знімок
;; ніколи не міг відповісти "коли модуль це дізнався?", і не було способу
;; забрати факт назад узагалі (`retract-knowledge` не існував).
;; `*knowledge-journal*` замінює його як єдине джерело правди: плаский,
;; постійно зростаючий список подій `(tell module-name clause)`/`(retract
;; module-name clause)`, найновіші спершу (той самий `cons`-паттерн, що й
;; `*working-memory*`/`*usage-counts*` уже використовують деінде в
;; проєкті). Без часових міток — my-lisp не має примітиву годинника, і
;; вигадати його тут було б саме тією невиправданою точністю, проти якої
;; застерігає принцип 6 МакКарті; порядок списку (від найстарішого до
;; найновішого після розвороту) — єдиний порядок, який цей журнал
;; насправді має, і це чесно визнано. Поточний список clause модуля тепер
;; — *проекція* журналу (`module-clauses-now`), обчислена на вимогу, а не
;; збережена десь напряму.
;;
;; Früher hielt `*knowledge-base*` einen Schnappschuss pro Modul — jeder
;; `defmodule`/`tell-knowledge`-Aufruf ersetzte ihn vollständig. Dieser
;; Schnappschuss konnte nie beantworten "wann hat das Modul das gelernt?",
;; und es gab keine Möglichkeit, einen Fakt überhaupt zurückzunehmen
;; (`retract-knowledge` existierte nicht). `*knowledge-journal*` ersetzt
;; ihn als einzige Quelle der Wahrheit: eine flache, stetig wachsende
;; Liste von `(tell module-name clause)`/`(retract module-name
;; clause)`-Ereignissen, neueste zuerst (dieselbe `cons`-Präfix-Konvention,
;; die `*working-memory*`/`*usage-counts*` anderswo im Projekt bereits
;; verwenden). Keine Zeitstempel — my-lisp hat kein Uhr-Primitiv, und eines
;; hier zu erfinden wäre genau die unverdiente Präzision, vor der
;; McCarthy-Prinzip 6 warnt; die Listenreihenfolge (älteste zuerst nach
;; Umkehrung) ist die einzige Ordnung, die dieses Journal tatsächlich hat,
;; und das wird ehrlich anerkannt. Die aktuelle Clause-Liste eines Moduls
;; ist jetzt eine *Projektion* über das Journal (`module-clauses-now`), auf
;; Anfrage berechnet, nicht irgendwo direkt gespeichert.
(00001001 *knowledge-journal* (00000001 ()))

;; clauses->tell-events turns a plain clause list into one `tell` event per
;; clause — ordinary my-lisp, not a macro, since nothing here needs the
;; top-level `def`-rebinding trick; only the macros below (which actually
;; grow `*knowledge-journal*`) do.
(00001001 clauses->tell-events
  (00001000 (module-name clauses)
    (00110111 (00001000 (clause) (00100111 (00000001 tell) module-name clause)) clauses)))

;; defmodule registers a list of clauses under a specific module name —
;; same public shape as before, but now expands to pushing one `tell`
;; event per clause onto `*knowledge-journal*` instead of replacing a
;; snapshot. A behavior change worth naming explicitly, not hiding: calling
;; `defmodule` twice for the same name used to silently shadow the first
;; call; now it *accumulates* both calls' clauses, which is the more
;; honest reading of "append-only" — nothing an earlier call told the
;; journal is ever quietly discarded by a later one.
(00001010 defmodule (name rules)
  (00100111 (00000001 def) (00000001 *knowledge-journal*)
        (00100111 (00000001 append)
              (00100111 (00000001 clauses->tell-events) (00100111 (00000001 quote) name) rules)
              (00000001 *knowledge-journal*))))

;; retract-knowledge is the capability the journal actually earns that the
;; old snapshot model never had at all: taking one clause back out of a
;; module. `clause` is left unquoted, the same convention `defmodule`'s
;; `rules` follows, so the caller decides whether to pass a literal or a
;; variable holding the clause to remove.
(00001010 retract-knowledge (module-name clause)
  (00100111 (00000001 def) (00000001 *knowledge-journal*)
        (00100111 (00000001 00000100)
              (00100111 (00000001 list) (00100111 (00000001 quote) (00000001 retract)) (00100111 (00000001 quote) module-name) clause)
              (00000001 *knowledge-journal*))))

;; module-journal-events used to cons after its recursive call returned.
;; That preserved order, but consumed one host stack frame per journal event
;; and failed on a realistic Advice Taker module at B5 scale. Keep the same
;; newest-first result through a reversed accumulator and one final reverse.
(00001001 module-journal-events-onto
  (00001000 (module-name journal acc)
    (00000111
      ((0100 (00000010 journal)) (00101010 acc))
      ((00000010 journal)  (00101010 acc))
      ((00100010 (00101111 (00000101 journal)) module-name)
       (module-journal-events-onto
         module-name
         (00000110 journal)
         (00000100 (00000101 journal) acc)))
      ((00000010 ())
       (module-journal-events-onto
         module-name
         (00000110 journal)
         acc)))))

(00001001 module-journal-events
  (00001000 (module-name journal)
    (module-journal-events-onto module-name journal (00000001 ()))))

;; Existence needs no filtered-list allocation. This tail-recursive scan
;; returns at the first event for the module and still treats a fully
;; retracted module as known because its historical journal events remain.
(00001001 module-journal-has-module?
  (00001000 (module-name journal)
    (00000111
      
      ((00000010 journal)  (00000001 ()))
      ((00100010 (00101111 (00000101 journal)) module-name) t)
      ((00000010 ()) (module-journal-has-module? module-name (00000110 journal))))))

;; module-known? distinguishes "no module by this name was ever told
;; anything" from "the module exists but every clause it was ever told has
;; since been retracted" — the second case must still project to an empty
;; clause list, not `Module-not-found`. Kept as its own check (not folded
;; into `module-clauses-now`) precisely so callers can tell those two
;; apart, the same distinction `reason-in`/`forward-in`/`describe` already
;; promised before the journal existed.
(00001001 module-known?
  (00001000 (module-name)
    (module-journal-has-module? module-name *knowledge-journal*)))

;; apply-journal-event folds one event onto a running clause list: `tell`
;; adds the clause, `retract` removes one matching occurrence — reusing
;; `lib/forward.lisp`'s own `retract-fact` (`equal?`-based, removes the first
;; match) rather than writing a second copy of the same logic.
(00001001 apply-journal-event
  (00001000 (clauses event)
    (00000111
      ((00000011 (00000101 event) (00000001 tell)) (00000100 (00110000 event) clauses))
      ((00000011 (00000101 event) (00000001 retract)) (retract-fact (00110000 event) clauses))
      ((00000010 ()) clauses))))

;; module-clauses-now is the projection itself: a module's events, put
;; back into chronological (oldest-first) order and folded left to right
;; through `apply-journal-event`. Every reader of a module's clauses
;; (`reason-in`, `forward-in`, `describe`) goes through this now, instead
;; of reading a stored snapshot — the journal is the only thing actually
;; stored.
(00001001 module-clauses-now
  (00001000 (module-name)
    (00111001 apply-journal-event (00000001 ())
            (00101010 (module-journal-events module-name *knowledge-journal*)))))

;; load-knowledge reads a file and loads its module definition
(00001010 load-knowledge (module-name)
  (00100111 (00000001 load) module-name))

;; reason-in queries a specific module by name
(00001001 reason-in
  (00001000 (module-name goal)
    (00000111
      ((01111110 module-name) (10000101 goal (01111111 module-name)))
      ((00000010 ()) (00000001 Module-not-found)))))

;; --- forward-chaining integration (lib/forward.lisp) ----------------------
;; `reason-in` asks a targeted question of a module (backward-chaining:
;; goal in, one proof out). `forward-in` asks a module to materialize
;; everything it can derive (forward-chaining: run-multi to a fixpoint).
;; No new clause format needed — a module's flat clause list from
;; `defmodule` (facts as zero-condition clauses, rules as `(head cond1
;; cond2 ...)`) is already exactly what `run-multi` expects: a fact is just
;; a "rule" whose empty condition list is trivially satisfied, firing it
;; unconditionally, which is a harmless no-op re-derivation of the fact
;; itself. That's why `forward-in` starts `run-multi` from an empty fact
;; list — the module's own facts bootstrap the fixpoint.
;;
;; forward-chaining інтеграція (lib/forward.lisp) — `reason-in` ставить
;; модулю конкретне питання (backward-chaining: ціль на вхід, одне
;; доведення на вихід). `forward-in` просить модуль матеріалізувати все,
;; що можна вивести (forward-chaining: run-multi до fixpoint). Новий
;; формат clause не потрібен — плаский список clause модуля з `defmodule`
;; (факти як clause без умов, правила як `(head cond1 cond2 ...)`) уже
;; точно те, чого чекає `run-multi`: факт — просто "правило" з порожнім
;; списком умов, який тривіально задоволений, тож застосовується
;; безумовно — нешкідливе повторне виведення самого факту. Тому
;; `forward-in` стартує `run-multi` з порожнього списку фактів — власні
;; факти модуля запускають fixpoint.
;;
;; Forward-Chaining-Integration (lib/forward.lisp) — `reason-in` stellt
;; einem Modul eine gezielte Frage (Backward-Chaining: Ziel rein, ein
;; Beweis raus). `forward-in` bittet ein Modul zu materialisieren, alles
;; was es ableiten kann (Forward-Chaining: run-multi bis zum Fixpunkt).
;; Kein neues Clause-Format nötig — die flache Clause-Liste eines Moduls
;; aus `defmodule` (Fakten als Clauses ohne Bedingungen, Regeln als `(head
;; cond1 cond2 ...)`) ist bereits genau das, was `run-multi` erwartet: ein
;; Fakt ist einfach eine "Regel" mit leerer, trivial erfüllter
;; Bedingungsliste, die bedingungslos feuert — eine harmlose erneute
;; Ableitung des Fakts selbst. Deshalb startet `forward-in` `run-multi` mit
;; einer leeren Faktenliste — die eigenen Fakten des Moduls starten den
;; Fixpunkt.
(00001001 forward-in
  (00001000 (module-name)
    (00000111
      ((01111110 module-name) (run-multi (01111111 module-name) (00000001 ())))
      ((00000010 ()) (00000001 Module-not-found)))))

;; check-conflict checks if the negation of the first rule's head is
;; provable. Retract is deliberately exempt from this check (per explicit
;; agreement): conflict detection guards against *adding* contradictory
;; information, not against *removing* it — taking a clause back out can
;; never itself contradict anything already known.
(00001011 check-conflict?
  (00001000 (module-name rules)
    (00000111
      ((01111110 module-name)
       (10011100 ((head (00000101 (00000101 rules))))
         (10011100 ((proofs (01111100 module-name (opposite-knowledge-head head))))
           (00000111
             
             ((00000010 proofs)  (00000001 ()))
             ((00000010 ()) t)))))
      )))

(00001011 check-conflict check-conflict?)

;; tell-knowledge adds new clauses to a module, creating it if it doesn't
;; exist yet — same conflict check as before, but on success it now pushes
;; `tell` events onto `*knowledge-journal*` instead of rebuilding a
;; snapshot; `module-clauses-now` picks up every clause any `tell-knowledge`
;; or `defmodule` call for this module ever contributed, in order.
(00001010 tell-knowledge (module-name rules)
  (00100111 (00000001 cond)
        (00100111 (00100111 (00000001 check-conflict) (00100111 (00000001 quote) module-name) rules)
              (00100111 (00000001 quote) (00000001 Conflict-detected)))
        (00100111 (00000001 t)
              (00100111 (00000001 def) (00000001 *knowledge-journal*)
                    (00100111 (00000001 append)
                          (00100111 (00000001 clauses->tell-events) (00100111 (00000001 quote) module-name) rules)
                          (00000001 *knowledge-journal*))))))

;; --- Advice ingestion boundary -----------------------------------------
;; `advise` is the guarded write path for knowledge from outside the trusted
;; source tree (controlled language today, an LLM translator later). It
;; accepts one clause as data, validates its whole shape, checks an explicit
;; opposite, and only then appends a journal event. Absence is not
;; contradiction: negation-as-failure in rule bodies remains separate from
;; explicitly stored `(not goal)` knowledge. Every result is structured data:
;; `(accepted ...)`, `(rejected ...)`, or `(conflict ...)`.
;;
;; `advise` — захищений шлях запису для знань з-за меж довіреного дерева
;; джерел (сьогодні з контрольованої мови, пізніше від LLM-перекладача). Він
;; приймає один clause як дані, перевіряє всю його форму, шукає явно задану
;; протилежність і лише тоді додає подію до журналу. Відсутність — не
;; суперечність: negation-as-failure у тілах правил лишається окремою від
;; явно збереженого знання `(not goal)`. Кожен результат — структуровані
;; дані: `(accepted ...)`, `(rejected ...)` або `(conflict ...)`.
;;
;; `advise` ist der geschützte Schreibpfad für Wissen von außerhalb des
;; vertrauenswürdigen Quellbaums (heute kontrollierte Sprache, später ein
;; LLM-Übersetzer). Es nimmt eine Clause als Daten entgegen, prüft ihre ganze
;; Form, sucht einen expliziten Gegensatz und hängt erst dann ein
;; Journalereignis an. Abwesenheit ist kein Widerspruch: Negation als
;; Fehlschlag in Regelrümpfen bleibt von explizit gespeichertem `(not goal)`-
;; Wissen getrennt. Jedes Ergebnis sind strukturierte Daten: `(accepted ...)`,
;; `(rejected ...)` oder `(conflict ...)`.

(00001011 knowledge-proper-list?
  (00001000 (value)
    (00000111
      ((0100 (00000010 value)) (00000111 ((00000011 value (00000001 ())) t) ))
      ((00000010 value)  (00000111 ((00000011 value (00000001 ())) t) ))
      ((00000010 ()) (knowledge-proper-list? (00000110 value))))))

(00001011 knowledge-terms-valid?
  (00001000 (terms)
    (00000111
      ((0100 (00000010 terms)) (00000111 ((00000011 terms (00000001 ())) t) ))
      ((00000010 terms)  (00000111 ((00000011 terms (00000001 ())) t) ))
      ((knowledge-term-valid? (00000101 terms))
       (knowledge-terms-valid? (00000110 terms)))
      )))

(00001011 knowledge-term-valid?
  (00001000 (term)
    (00000111
      
      ((00000010 term)  t)
      ((0100 (00000010 (00000101 term))) (00000111
         ((00000011 (00000101 term) (00000001 var))
          (00000111
            ((00011100 (00101000 term) 2)  (00100011 (00101111 term)))
            ))
         ((knowledge-proper-list? term) (knowledge-terms-valid? term))
         ))
      ((00000010 (00000101 term))  (00000111
         ((00000011 (00000101 term) (00000001 var))
          (00000111
            ((00011100 (00101000 term) 2)  (00100011 (00101111 term)))
            ))
         ((knowledge-proper-list? term) (knowledge-terms-valid? term))
         ))
      )))

; Зарезервована голова заперечення: `not?` (присудок з `?`, #1444) або
; історичне `not`.
(00001011 knowledge-not-head?
  (00001000 (head)
    (00000111
      ((00000011 head (00000001 not?)) t)
      ((00000011 head (00000001 not)) t)
      )))

(00001011 knowledge-goal-valid?
  (00001000 (goal)
    (00000111
      
      ((00000010 goal)  (00000001 ()))
      ((00000011 (knowledge-proper-list? goal) (00000001 ())) (00000001 ()))
      ((00000011 (00100011 (00000101 goal)) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 goal) (00000001 not))
       (00000111
         ((00011100 (00101000 goal) 2)  (knowledge-goal-valid? (00101111 goal)))
         ))
      ((00000011 (00000101 goal) (00000001 not?))
       (00000111
         ((00011100 (00101000 goal) 2)  (knowledge-goal-valid? (00101111 goal)))
         ))
      ((00000010 ()) (knowledge-terms-valid? (00000110 goal))))))

(00001011 knowledge-goals-valid?
  (00001000 (goals)
    (00000111
      ((0100 (00000010 goals)) (00000111 ((00000011 goals (00000001 ())) t) ))
      ((00000010 goals)  (00000111 ((00000011 goals (00000001 ())) t) ))
      ((knowledge-goal-valid? (00000101 goals))
       (knowledge-goals-valid? (00000110 goals)))
      )))

(00001011 knowledge-clause-valid?
  (00001000 (clause)
    (00000111
      
      ((00000010 clause)  (00000001 ()))
      ((00000011 (knowledge-proper-list? clause) (00000001 ())) (00000001 ()))
      ((00000011 (knowledge-goal-valid? (00000101 clause)) (00000001 ())) (00000001 ()))
      ((00000010 ()) (knowledge-goals-valid? (00000110 clause))))))

;; Explicit opposites operate on heads, not whole clauses: a rule and a fact
;; may derive the same head, and either is sufficient evidence.
;; Явні протилежності працюють із головами, не з цілими clause: правило і
;; факт можуть вивести ту саму голову, і кожного достатньо як доказу.
;; Explizite Gegensätze arbeiten mit Köpfen statt ganzen Clauses: Regel und
;; Fakt können denselben Kopf ableiten; jeder ist als Beleg ausreichend.
(00001011 opposite-knowledge-head
  (00001000 (head)
    (00000111
      ((knowledge-not-head? (00000101 head)) (00101111 head))
      ((00000010 ()) (00100111 (00000001 not?) head)))))

(00001011 advice-conflict-proof
  (00001000 (module-name clause)
    (00000111
      ((01111110 module-name)
       (10011100 ((proofs (01111100 module-name (opposite-knowledge-head (00000101 clause)))))
         (00000111
           ((0100 (00000010 proofs)) (00000111
              ((00000011 (00000101 (00000101 clause)) (00000001 not)) (00000001 ()))
              ((00000011 (00000101 (00000101 clause)) (00000001 not?)) (00000001 ()))
              ((00000010 ()) (01111100 module-name (00100111 (00000001 not?) (00000101 clause))))))
           ((00000010 proofs)  (00000111
              ((00000011 (00000101 (00000101 clause)) (00000001 not)) (00000001 ()))
              ((00000011 (00000101 (00000101 clause)) (00000001 not?)) (00000001 ()))
              ((00000010 ()) (01111100 module-name (00100111 (00000001 not?) (00000101 clause))))))
           ((00000010 ()) proofs))))
      )))

(00001011 advice-decision
  (00001000 (module-name clause)
    (00000111
      ((00000011 (00100011 module-name) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-module)) (00100111 (00000001 input) clause)))
      ((00000011 (knowledge-clause-valid? clause) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-clause)) (00100111 (00000001 input) clause)))
      ((00000010 ())
       (10011100 ((opposite (opposite-knowledge-head (00000101 clause)))
             (proofs (advice-conflict-proof module-name clause)))
         (00000111
           ((0100 (00000010 proofs)) (00100111 (00000001 accepted) (00100111 (00000001 module) module-name) (00100111 (00000001 knowledge) clause)))
           ((00000010 proofs)  (00100111 (00000001 accepted) (00100111 (00000001 module) module-name) (00100111 (00000001 knowledge) clause)))
           ((00000010 ())
            (00100111 (00000001 conflict)
                  (00100111 (00000001 new) clause)
                  (00100111 (00000001 existing) opposite)
                  (00100111 (00000001 proof) (00000101 proofs))))))))))

;; The accepted branch evaluates `def` in the caller's frame, then returns
;; the structured decision. A helper lambda would write into a disposable
;; child frame, so sequencing intentionally lives in the macro expansion.
;; Прийнята гілка виконує `def` у фреймі викликача й повертає структуроване
;; рішення. Допоміжна lambda писала б у тимчасовий дочірній фрейм, тому
;; послідовність навмисно міститься безпосередньо в macro expansion.
;; Der akzeptierte Zweig führt `def` im Frame des Aufrufers aus und gibt die
;; strukturierte Entscheidung zurück. Eine Hilfs-Lambda würde in einen
;; kurzlebigen Kind-Frame schreiben; daher liegt die Sequenz im Makro selbst.
(00001010 advise (module-name clause)
  (00100111 (00000001 cond)
        (00100111
          (00100111 (00000001 equal?)
                (00100111 (00000001 00000101) (00100111 (00000001 advice-decision) (00100111 (00000001 quote) module-name) clause))
                (00100111 (00000001 quote) (00000001 accepted)))
          (00100111 (00000001 second)
                (00100111 (00000001 list)
                      (00100111 (00000001 def) (00000001 *knowledge-journal*)
                            (00100111 (00000001 append)
                                  (00100111 (00000001 clauses->tell-events)
                                        (00100111 (00000001 quote) module-name)
                                        (00100111 (00000001 list) clause))
                                  (00000001 *knowledge-journal*)))
                      (00100111 (00000001 list)
                            (00100111 (00000001 quote) (00000001 accepted))
                            (00100111 (00000001 list)
                                  (00100111 (00000001 quote) (00000001 module))
                                  (00100111 (00000001 quote) module-name))
                            (00100111 (00000001 list) (00100111 (00000001 quote) (00000001 knowledge)) clause)))))
        (00100111 (00000001 t) (00100111 (00000001 advice-decision) (00100111 (00000001 quote) module-name) clause))))

;; `advise-all` is the transactional companion to `advise`. Translators often
;; produce several mutually dependent clauses, so validating and writing them
;; one at a time could leave half an answer in the journal. The whole batch is
;; checked against the module plus the proposed clauses; only one journal
;; replacement happens after every clause passes and no opposite is derivable.
;;
;; `advise-all` — транзакційний відповідник `advise`. Перекладачі часто
;; породжують кілька взаємозалежних clause, тому поелементна перевірка й запис
;; могли б лишити в журналі половину відповіді. Увесь пакет перевіряється проти
;; модуля разом із запропонованими clause; журнал змінюється один раз лише після
;; успішної перевірки всіх елементів і відсутності вивідної протилежності.
;;
;; `advise-all` ist das transaktionale Gegenstück zu `advise`. Übersetzer
;; erzeugen oft mehrere voneinander abhängige Clauses; eine elementweise
;; Prüfung könnte daher eine halbe Antwort im Journal hinterlassen. Das ganze
;; Paket wird gegen das Modul samt vorgeschlagenen Clauses geprüft; das Journal
;; wird erst einmalig ersetzt, wenn alles gültig und kein Gegenteil ableitbar
;; ist.
(00001001 knowledge-clauses-valid?
  (00001000 (clauses)
    (00000111
      ((0100 (00000010 clauses)) t)
      ((00000010 clauses)  (00000001 ()))
      ((00000010 clauses) 
       (00000111
         ((knowledge-clause-valid? (00000101 clauses))
          (knowledge-clauses-valid? (00000110 clauses)))
         )))))

(00001001 advice-negative-head-conflict
  (00001000 (rules all-rules)
    (00000111
      
      ((00000010 rules)  (00000001 ()))
      ((00000010 ())
       (10011100 ((head (00000101 (00000101 rules))))
         (00000111
           ((knowledge-not-head? (00000101 head))
            (10011100 ((positive (00101111 head)))
              (10011100 ((proofs (10000101 positive all-rules)))
                (00000111
                  ((0100 (00000010 proofs)) (advice-negative-head-conflict (00000110 rules) all-rules))
                  ((00000010 proofs)  (advice-negative-head-conflict (00000110 rules) all-rules))
                  ((00000010 ()) (00100111 head positive (00000101 proofs)))))))
           ((00000010 ()) (advice-negative-head-conflict (00000110 rules) all-rules))))))))

(00001001 advice-batch-conflict
  (00001000 (clauses remaining all-rules)
    (00000111
      ((0100 (00000010 remaining)) (10011100 ((global (advice-negative-head-conflict all-rules all-rules)))
         (00000111
           
           ((00000010 global)  (00000001 ()))
           ((00000010 ()) (00100111 (00000101 clauses) (00000101 global) (00110000 global))))))
      ((00000010 remaining)  (10011100 ((global (advice-negative-head-conflict all-rules all-rules)))
         (00000111
           
           ((00000010 global)  (00000001 ()))
           ((00000010 ()) (00100111 (00000101 clauses) (00000101 global) (00110000 global))))))
      ((00000010 ())
       (10011100 ((opposite (opposite-knowledge-head (00000101 (00000101 remaining)))))
         (10011100 ((proofs (10000101 opposite all-rules)))
           (00000111
             ((0100 (00000010 proofs)) (advice-batch-conflict clauses (00000110 remaining) all-rules))
             ((00000010 proofs)  (advice-batch-conflict clauses (00000110 remaining) all-rules))
             ((00000010 ()) (00100111 (00000101 remaining) opposite (00000101 proofs))))))))))

(00001001 advice-all-decision
  (00001000 (module-name clauses)
    (00000111
      ((00000011 (00100011 module-name) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-module)) (00100111 (00000001 input) clauses)))
      ((0100 (00000010 clauses)) (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000010 clauses)  (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-proper-list? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-clauses-valid? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-clause)) (00100111 (00000001 input) clauses)))
      ((00000010 ())
       (10011100 ((existing (00000111
                         ((01111110 module-name)
                          (01111111 module-name))
                         )))
         (10011100 ((conflict (advice-batch-conflict clauses clauses
                                                (00101001 clauses existing))))
           (00000111
             ((0100 (00000010 conflict)) (00100111 (00000001 accepted)
                    (00100111 (00000001 module) module-name)
                    (00100111 (00000001 knowledge) clauses)))
             ((00000010 conflict)  (00100111 (00000001 accepted)
                    (00100111 (00000001 module) module-name)
                    (00100111 (00000001 knowledge) clauses)))
             ((00000010 ())
              (00100111 (00000001 conflict)
                    (00100111 (00000001 new) (00000101 conflict))
                    (00100111 (00000001 existing) (00101111 conflict))
                    (00100111 (00000001 proof) (00110000 conflict)))))))))))

;; As with `advise`, sequencing stays in the macro so `def` updates the
;; caller's persistent frame rather than a helper lambda's temporary frame.
;; Як і в `advise`, послідовність лишається в макросі, щоб `def` оновлював
;; сталий фрейм викликача, а не тимчасовий фрейм допоміжної lambda.
;; Wie bei `advise` bleibt die Sequenz im Makro, damit `def` den dauerhaften
;; Aufrufer-Frame statt des temporären Frames einer Hilfs-Lambda aktualisiert.
(00001010 advise-all (module-name clauses)
  (00100111 (00000001 cond)
        (00100111
          (00100111 (00000001 equal?)
                (00100111 (00000001 00000101)
                      (00100111 (00000001 advice-all-decision)
                            (00100111 (00000001 quote) module-name) clauses))
                (00100111 (00000001 quote) (00000001 accepted)))
          (00100111 (00000001 second)
                (00100111 (00000001 list)
                      (00100111 (00000001 def) (00000001 *knowledge-journal*)
                            (00100111 (00000001 append)
                                  (00100111 (00000001 clauses->tell-events)
                                        (00100111 (00000001 quote) module-name) clauses)
                                  (00000001 *knowledge-journal*)))
                      (00100111 (00000001 list)
                            (00100111 (00000001 quote) (00000001 accepted))
                            (00100111 (00000001 list)
                                  (00100111 (00000001 quote) (00000001 module))
                                  (00100111 (00000001 quote) module-name))
                            (00100111 (00000001 list) (00100111 (00000001 quote) (00000001 knowledge)) clauses)))))
        (00100111 (00000001 t)
              (00100111 (00000001 advice-all-decision)
                    (00100111 (00000001 quote) module-name) clauses))))

;; --- Versioned knowledge-package interchange ---------------------------
;; A package is data, never executable code:
;; `((format . my-lisp-knowledge) (version 0 1) (module . astronomy)
;;   (clauses . (((planet earth)) ...)))`.
;; Keeping the envelope as an association list makes it readable by every
;; project that already understands S-expressions, while the independent
;; format version lets the envelope evolve without coupling it to a my-lisp
;; release or the language-contract version.
;;
;; Пакет є даними, а не виконуваним кодом. Association list читається кожним
;; проєктом, що вже розуміє S-вирази, а незалежна версія формату дозволяє
;; розвивати оболонку без прив'язки до релізу my-lisp чи language-contract.
;;
;; Ein Paket besteht aus Daten, niemals aus ausführbarem Code. Die
;; Assoziationsliste ist für jedes S-Ausdruck-Projekt lesbar; die unabhängige
;; Formatversion lässt die Hülle ohne Kopplung an my-lisp- oder
;; Sprachvertragsversionen wachsen.
(00001001 *knowledge-package-version* (00000001 (0 1)))

(00001001 knowledge-package-entries-valid?
  (00001000 (entries)
    (00000111
      ((0100 (00000010 entries)) t)
      ((00000010 entries)  (00000001 ()))
      ((00000010 entries) 
       (00000111
         
         ((00000010 (00000101 entries))  (00000001 ()))
         ((00100011 (00000101 (00000101 entries)))
          (knowledge-package-entries-valid? (00000110 entries)))
         )))))

(00001001 knowledge-package-field
  (00001000 (name package)
    (10011100 ((entry (00101101 name package)))
      (00000111 
            ((00000010 entry)  (00000001 ())) ((00000010 ()) (00000110 entry))))))

(00001001 make-knowledge-package
  (00001000 (module-name clauses)
    (00100111 (00000100 (00000001 format) (00000001 my-lisp-knowledge))
          (00000100 (00000001 version) *knowledge-package-version*)
          (00000100 (00000001 module) module-name)
          (00000100 (00000001 clauses) clauses))))

(00001001 knowledge-package-decision
  (00001000 (package)
    (00000111
      ((0100 (00000010 package)) (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-package)) (00100111 (00000001 input) package)))
      ((00000010 package)  (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-package)) (00100111 (00000001 input) package)))
      ((00000011 (knowledge-proper-list? package) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-package)) (00100111 (00000001 input) package)))
      ((00000011 (knowledge-package-entries-valid? package) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-package)) (00100111 (00000001 input) package)))
      ((00000011 (knowledge-package-field (00000001 format) package) (00000001 my-lisp-knowledge))
       (00000111
         ((00100010 (knowledge-package-field (00000001 version) package)
                  *knowledge-package-version*)
          (advice-all-decision (knowledge-package-field (00000001 module) package)
                               (knowledge-package-field (00000001 clauses) package)))
         ((00000010 ()) (00100111 (00000001 rejected)
                  (00100111 (00000001 reason) (00000001 unsupported-version))
                  (00100111 (00000001 version) (knowledge-package-field (00000001 version) package))))))
      ((00000010 ()) (00100111 (00000001 rejected)
               (00100111 (00000001 reason) (00000001 invalid-package))
               (00100111 (00000001 input) package))))))

;; Import uses the same atomic journal update as `advise-all`. The module name
;; is read from data at runtime, so this is a separate macro rather than a thin
;; call to `advise-all`, whose module argument is intentionally literal syntax.
;; Імпорт використовує те саме атомарне оновлення, що й `advise-all`; назва
;; модуля читається з даних під час виконання, тому це окремий макрос.
;; Der Import nutzt dasselbe atomare Journal-Update wie `advise-all`; der
;; Modulname kommt zur Laufzeit aus Daten, daher ist dies ein eigenes Makro.
(00001010 import-knowledge-package (package)
  (00100111 (00000001 cond)
        (00100111
          (00100111 (00000001 equal?)
                (00100111 (00000001 00000101) (00100111 (00000001 knowledge-package-decision) package))
                (00100111 (00000001 quote) (00000001 accepted)))
          (00100111 (00000001 second)
                (00100111 (00000001 list)
                      (00100111 (00000001 def) (00000001 *knowledge-journal*)
                            (00100111 (00000001 append)
                                  (00100111 (00000001 clauses->tell-events)
                                        (00100111 (00000001 knowledge-package-field)
                                              (00100111 (00000001 quote) (00000001 module)) package)
                                        (00100111 (00000001 knowledge-package-field)
                                              (00100111 (00000001 quote) (00000001 clauses)) package))
                                  (00000001 *knowledge-journal*)))
                      (00100111 (00000001 knowledge-package-decision) package))))
        (00100111 (00000001 t) (00100111 (00000001 knowledge-package-decision) package))))

(00001010 import-knowledge-file (path)
  (00100111 (00000001 import-knowledge-package)
        (00100111 (00000001 01001010) (00100111 (00000001 read-file) path))))

;; Export is deliberately a plain function: unlike import it does not mutate
;; the knowledge journal. It validates the module and clauses, serializes the
;; canonical package with `write-to-string`, and writes exactly one expression.
;; Експорт не змінює журнал: перевіряє дані, канонічно серіалізує й записує.
;; Export verändert das Journal nicht: prüfen, kanonisch serialisieren, schreiben.
(00001001 write-knowledge-package
  (00001000 (path module-name clauses)
    (00000111
      ((00000011 (00100011 module-name) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-module)) (00100111 (00000001 input) module-name)))
      ((0100 (00000010 clauses)) (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000010 clauses)  (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-proper-list? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-clauses-valid? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-clause)) (00100111 (00000001 input) clauses)))
      ((00000010 ())
       (10011100 ((package (make-knowledge-package module-name clauses)))
         (00101111 (00100111 (10100111 path (01001100 package)) package)))))))

;; TCP transport uses one package per connection and EOF as the frame boundary.
;; TCP may split one write into many reads, so the receiver drains every chunk
;; before parsing exactly one S-expression. The sender closes only after
;; `tcp-write` succeeds. No received bytes are ever passed to `eval`.
;; TCP-транспорт: один пакет на з'єднання, EOF — межа; отримане ніколи не `eval`.
;; TCP-Transport: ein Paket pro Verbindung, EOF als Grenze; Empfang nie per `eval`.
(00001001 tcp-read-to-eof
  (00001000 (connection accumulated)
    (10011100 ((chunk (10100011 connection)))
      (00000111
        ((00111100 chunk) accumulated)
        ((00000010 ()) (tcp-read-to-eof connection
                            (00111010 accumulated chunk)))))))

(00001001 send-knowledge-package
  (00001000 (connection module-name clauses)
    (00000111
      ((00000011 (00100011 module-name) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-module)) (00100111 (00000001 input) module-name)))
      ((0100 (00000010 clauses)) (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000010 clauses)  (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-proper-list? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-clauses-valid? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-clause)) (00100111 (00000001 input) clauses)))
      ((00000010 ())
       (10011100 ((package (make-knowledge-package module-name clauses)))
         (00110000 (00100111 (10100100 connection (01001100 package))
                      (tcp-close connection)
                      package)))))))

(00001010 receive-knowledge-package (connection)
  (00100111 (00000001 second)
        (00100111 (00000001 list)
              (00100111 (00000001 def) (00000001 *received-knowledge-package*)
                    (00100111 (00000001 01001010) (00100111 (00000001 tcp-read-to-eof) connection "")))
              (00100111 (00000001 import-knowledge-package) (00000001 *received-knowledge-package*)))))

;; A newline-framed request/receipt protocol keeps the connection open long
;; enough for the receiver to answer with the structured import decision.
;; `write-to-string` escapes newlines inside string values, so a literal LF is
;; an unambiguous frame boundary. One request and one receipt per connection
;; means no unread suffix has to survive between calls.
;; Протокол із LF-frame лишає з'єднання відкритим для структурованої квитанції.
;; LF-gerahmtes Protokoll hält die Verbindung für eine strukturierte Quittung offen.
(00001001 string-through-line
  (00001000 (text accumulated)
    (00000111
      ((00111100 text) (00000001 ()))
      ((00000011 (00111111 text) "\n") (00100111 accumulated))
      ((00000010 ()) (string-through-line
           (01000000 text)
           (00111010 accumulated (00111111 text)))))))

(00001001 tcp-read-frame
  (00001000 (connection accumulated)
    (10011100 ((chunk (10100011 connection)))
      (00000111
        ((00111100 chunk) (00000001 ()))
        ((00000010 ())
         (10011100 ((line (string-through-line
                       (00111010 accumulated chunk) "")))
           (00000111
             ((0100 (00000010 line)) (tcp-read-frame connection (00111010 accumulated chunk)))
             ((00000010 line)  (tcp-read-frame connection (00111010 accumulated chunk)))
             ((00000010 ()) (00000101 line)))))))))

(00001001 exchange-knowledge-package
  (00001000 (connection module-name clauses)
    (00000111
      ((00000011 (00100011 module-name) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-module)) (00100111 (00000001 input) module-name)))
      ((0100 (00000010 clauses)) (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000010 clauses)  (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-proper-list? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-batch)) (00100111 (00000001 input) clauses)))
      ((00000011 (knowledge-clauses-valid? clauses) (00000001 ()))
       (00100111 (00000001 rejected) (00100111 (00000001 reason) (00000001 invalid-clause)) (00100111 (00000001 input) clauses)))
      ((00000010 ())
       (10011100 ((package (make-knowledge-package module-name clauses)))
         (00110000
           (00100111
             (10100100 connection
                        (00111010 (01001100 package) "\n"))
             (00001001 *knowledge-receipt-text* (tcp-read-frame connection ""))
             (10011100 ((receipt (01001010 *knowledge-receipt-text*)))
               (00101111 (00100111 (tcp-close connection) receipt))))))))))

(00001010 accept-knowledge-exchange (connection)
  (00100111 (00000001 second)
        (00100111 (00000001 list)
              (00100111 (00000001 def) (00000001 *received-knowledge-package*)
                    (00100111 (00000001 01001010) (00100111 (00000001 tcp-read-frame) connection "")))
              (00100111 (00000001 let)
                    (00100111 (00100111 (00000001 decision)
                                (00100111 (00000001 import-knowledge-package)
                                      (00000001 *received-knowledge-package*))))
                    (00100111 (00000001 second)
                          (00100111 (00000001 list)
                                (00100111 (00000001 tcp-write) connection
                                      (00100111 (00000001 string-append)
                                            (00100111 (00000001 write-to-string) (00000001 decision))
                                            "\n"))
                                (00100111 (00000001 second)
                                      (00100111 (00000001 list)
                                            (00100111 (00000001 tcp-close) connection)
                                            (00000001 decision)))))))))

;; --- "atom as concept entry point" ------------------------------------
;; A bare symbol like `earth` doesn't mean anything by itself — its meaning
;; comes from the facts we've recorded around it. `describe` turns a symbol
;; into an entry point into everything currently known about it: every fact
;; in a module that mentions the symbol, collected as-is. Not a new kind of
;; storage — the same flat facts already stored by `defmodule`/`tell-knowledge`,
;; just queried from a symbol outward instead of from a goal downward.

;; contains-atom? checks whether `item` occurs among the elements of a fact's
;; argument list, e.g. `apple` in `(has-mass apple)`. `eq` only accepts atoms,
;; so non-atom elements (like a `(var x)` term inside a rule head) are simply
;; skipped rather than compared — `describe` only ever looks at facts, but
;; this keeps the helper safe to reuse against rule heads too.
(00001001 contains-atom?
  (00001000 (item lst)
    (00000111
      
      ((00000010 lst)  (00000001 ()))
      ((0100 (00000010 (00000101 lst))) (00000111
         ((00000011 (00000101 lst) item) t)
         ((00000010 ()) (01111010 item (00000110 lst)))))
      ((00000010 (00000101 lst))  (00000111
         ((00000011 (00000101 lst) item) t)
         ((00000010 ()) (01111010 item (00000110 lst)))))
      ((00000010 ()) (01111010 item (00000110 lst))))))

;; is-fact? answers the knowledge-domain question explicitly. The structural
;; shape of the clause body is mechanism: an empty body means a fact, while a
;; non-empty proper body means a rule. Do not leak atom's structural record as
;; the public answer and do not collapse the distinction into historical t/().
(00001001 is-fact?
  (00001000 (clause)
    (00000111
      ((0100 (00000010 (00000110 clause)))
       (00100111 (00000001 clause-kind) (00000001 fact)))
      ((00000010 (00000110 clause)) 
       (00100111 (00000001 clause-kind) (00000001 rule))))))

;; collect-facts-about consumes the explicit clause-domain result. Its list
;; traversal and the legacy contains-atom? compatibility result are also
;; dispatched explicitly, so no generic truthiness decides whether a clause is
;; a fact worth reporting.
(00001001 collect-facts-about
  (00001000 (item clauses)
    (00000111
      
      ((00000010 clauses)  (00000001 ()))
      ((00000010 clauses) 
       (10011100 ((clause (00000101 clauses)))
         (10011100 ((head (00000101 clause)))
           (00000111
             ((01110111 clause) 
              (01111001 item (00000110 clauses)))
             ((01110111 clause) 
              (10011100 ((contains (01111010 item head)))
                (00000111
                  ((00000011 contains (00000001 ())) 
                   (01111001 item (00000110 clauses)))
                  ((00000011 contains (00000001 ())) 
                   (00000100 head (01111001 item (00000110 clauses))))))))))))))

;; describe returns every known fact about `item` within `module-name`,
;; or `Module-not-found` for consistency with `reason-in`.
(00001001 describe
  (00001000 (item module-name)
    (00000111
      ((01111110 module-name) (01111001 item (01111111 module-name)))
      ((00000010 ()) (00000001 Module-not-found)))))

;; --- usage tracking (which knowledge is actually alive) ----------------
;; A per-fact/per-rule usage counter, cheap enough to make "is this module
;; still being reasoned over, or has it gone Cyc-style dead" a measurable
;; question instead of a guess. `*usage-counts*` follows the same top-level
;; `def`-rebinding pattern as `*knowledge-base*` above — `def` only mutates
;; the frame it runs in, so accumulation has to happen at the call site
;; (top level), not inside a nested lambda call like `prove-rule`. That's
;; why `record-usage!` is a macro: it expands to a `(def *usage-counts* ...)`
;; form in the caller's own frame, the same trick `tell-knowledge` uses.
;;
;; Лічильник використання на факт/правило, достатньо дешевий, щоб "чи це
;; знання ще живе, чи вже стало мертвим у стилі Cyc" стало вимірюваним
;; питанням, а не здогадкою. `*usage-counts*` слідує тому самому
;; top-level `def`-паттерну перезапису, що й `*knowledge-base*` вище —
;; `def` мутує лише той фрейм, у якому виконується, тож накопичення має
;; відбуватись у місці виклику (на верхньому рівні), а не всередині
;; вкладеного виклику lambda типу `prove-rule`. Тому `record-usage!` —
;; макрос: він розгортається у форму `(def *usage-counts* ...)` у фреймі
;; викликача, той самий прийом, що й `tell-knowledge`.
;;
;; Ein Nutzungszähler pro Fakt/Regel, billig genug, um "lebt dieses Wissen
;; noch, oder ist es im Cyc-Stil tot" zu einer messbaren Frage statt einer
;; Vermutung zu machen. `*usage-counts*` folgt demselben Top-Level
;; `def`-Umbindungsmuster wie `*knowledge-base*` oben — `def` mutiert nur
;; den Frame, in dem es läuft, daher muss die Akkumulation am Aufrufort
;; (Top-Level) stattfinden, nicht innerhalb eines verschachtelten
;; Lambda-Aufrufs wie `prove-rule`. Deshalb ist `record-usage!` ein Makro:
;; es entfaltet sich zu einer `(def *usage-counts* ...)`-Form im Frame des
;; Aufrufers, derselbe Trick wie bei `tell-knowledge`.
(00001001 *usage-counts* (00000001 ()))

(00001010 record-usage! (proof)
  (00100111 (00000001 def) (00000001 *usage-counts*)
        (00100111 (00000001 merge-usage) (00100111 (00000001 count-usage) proof) (00000001 *usage-counts*))))

(00001001 usage-of
  (00001000 (rule-head)
    (10011100 ((entry (00101101 rule-head *usage-counts*)))
      (00000111
        
        ((00000010 entry)  0)
        ((00000010 ()) (00000110 entry))))))
