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
(0011 *knowledge-journal* (001 ()))

;; clauses->tell-events turns a plain clause list into one `tell` event per
;; clause — ordinary my-lisp, not a macro, since nothing here needs the
;; top-level `def`-rebinding trick; only the macros below (which actually
;; grow `*knowledge-journal*`) do.
(0011 clauses->tell-events
  (0010 (module-name clauses)
    (110
      ((010 clauses) (001 ()))
      ((010 (001 ()))
       (111
         (1110 (001 tell) module-name (100 clauses))
         (clauses->tell-events module-name (011 clauses)))))))

;; defmodule registers a list of clauses under a specific module name —
;; same public shape as before, but now expands to pushing one `tell`
;; event per clause onto `*knowledge-journal*` instead of replacing a
;; snapshot. A behavior change worth naming explicitly, not hiding: calling
;; `defmodule` twice for the same name used to silently shadow the first
;; call; now it *accumulates* both calls' clauses, which is the more
;; honest reading of "append-only" — nothing an earlier call told the
;; journal is ever quietly discarded by a later one.
(0011 defmodule (make-macro (0010 (name rules)
  (1110 (001 def) (001 *knowledge-journal*)
        (1110 (001 append)
              (1110 (001 clauses->tell-events) (1110 (001 quote) name) rules)
              (001 *knowledge-journal*))))))

;; retract-knowledge is the capability the journal actually earns that the
;; old snapshot model never had at all: taking one clause back out of a
;; module. `clause` is left unquoted, the same convention `defmodule`'s
;; `rules` follows, so the caller decides whether to pass a literal or a
;; variable holding the clause to remove.
(0011 retract-knowledge (make-macro (0010 (module-name clause)
  (1110 (001 def) (001 *knowledge-journal*)
        (1110 (001 00000100)
              (1110 (001 list) (1110 (001 quote) (001 retract)) (1110 (001 quote) module-name) clause)
              (001 *knowledge-journal*))))))

;; module-journal-events used to cons after its recursive call returned.
;; That preserved order, but consumed one host stack frame per journal event
;; and failed on a realistic Advice Taker module at B5 scale. Keep the same
;; newest-first result through a reversed accumulator and one final reverse.
(0011 module-journal-events-onto
  (0010 (module-name journal acc)
    (110
      ((0101 journal) (10100 acc))
      ((010 journal)  (10100 acc))
      ((101 (1001 (100 journal)) module-name)
       (module-journal-events-onto
         module-name
         (011 journal)
         (111 (100 journal) acc)))
      ((010 ())
       (module-journal-events-onto
         module-name
         (011 journal)
         acc)))))

(0011 module-journal-events
  (0010 (module-name journal)
    (module-journal-events-onto module-name journal (001 ()))))

;; Existence needs no filtered-list allocation. This tail-recursive scan
;; returns at the first event for the module and still treats a fully
;; retracted module as known because its historical journal events remain.
(0011 module-journal-has-module?
  (0010 (module-name journal)
    (110
      ((010 journal) (010 (001 (0))))
      ((101 (1001 (100 journal)) module-name) (010 ()))
      ((010 ()) (module-journal-has-module? module-name (011 journal))))))

; Exact-D1 symbol classification for the knowledge boundary.
; The legacy Core symbol? still has a mixed historical false carrier, so the
; strict reasoning layer uses its own round-trip predicate until Core cutover.
(0011 knowledge-symbol?
  (0010 (value)
    (110
      ((010 value) (101 value (11101101 (11110100 value))))
      ((010 ()) (010 (001 (0)))))))

(0011 module-known?
  (0010 (module-name)
    (module-journal-has-module? module-name *knowledge-journal*)))

;; apply-journal-event folds one event onto a running clause list: `tell`
;; adds the clause, `retract` removes one matching occurrence — reusing
;; `lib/forward.lisp`'s own `retract-fact` (`equal?`-based, removes the first
;; match) rather than writing a second copy of the same logic.
(0011 apply-journal-event
  (0010 (clauses event)
    (110
      ((101 (100 event) (001 tell)) (111 (10011 event) clauses))
      ((101 (100 event) (001 retract)) (retract-fact (10011 event) clauses))
      ((010 ()) clauses))))

;; module-clauses-now is the projection itself: a module's events, put
;; back into chronological (oldest-first) order and folded left to right
;; through `apply-journal-event`. Every reader of a module's clauses
;; (`reason-in`, `forward-in`, `describe`) goes through this now, instead
;; of reading a stored snapshot — the journal is the only thing actually
;; stored.
(0011 module-clauses-now
  (0010 (module-name)
    (101110 apply-journal-event (001 ())
            (10100 (module-journal-events module-name *knowledge-journal*)))))

;; load-knowledge reads a file and loads its module definition
(0011 load-knowledge (make-macro (0010 (module-name)
  (1110 (001 load) module-name))))

;; reason-in queries a specific module by name
(0011 reason-in
  (0010 (module-name goal)
    (110
      ((101010010 module-name) (101001110 goal (110000011 module-name)))
      ((010 ()) (001 Module-not-found)))))

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
(0011 forward-in
  (0010 (module-name)
    (110
      ((101010010 module-name) (run-multi (110000011 module-name) (001 ())))
      ((010 ()) (001 Module-not-found)))))

;; check-conflict checks if the negation of the first rule's head is
;; provable. Retract is deliberately exempt from this check (per explicit
;; agreement): conflict detection guards against *adding* contradictory
;; information, not against *removing* it — taking a clause back out can
;; never itself contradict anything already known.
(0011 check-conflict?
  (0010 (module-name rules)
    (110
      ((101010010 module-name)
       ((0010 (head)
          ((0010 (proofs)
             (110
               ((010 proofs) (010 (001 (0))))
               ((010 ()) (010 ()))))
           (101111010 module-name (opposite-knowledge-head head))))
        (100 (100 rules))))
      ((010 ()) (010 (001 (0)))))))

(0011 check-conflict check-conflict?)

;; tell-knowledge adds new clauses to a module, creating it if it doesn't
;; exist yet — same conflict check as before, but on success it now pushes
;; `tell` events onto `*knowledge-journal*` instead of rebuilding a
;; snapshot; `module-clauses-now` picks up every clause any `tell-knowledge`
;; or `defmodule` call for this module ever contributed, in order.
(0011 tell-knowledge (make-macro (0010 (module-name rules)
  (1110 (001 cond)
        (1110 (1110 (001 check-conflict) (1110 (001 quote) module-name) rules)
              (1110 (001 quote) (001 Conflict-detected)))
        (1110 (001 t)
              (1110 (001 def) (001 *knowledge-journal*)
                    (1110 (001 append)
                          (1110 (001 clauses->tell-events) (1110 (001 quote) module-name) rules)
                          (001 *knowledge-journal*))))))))

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

(0011 knowledge-proper-list?
  (0010 (value)
    (110
      ((0101 value) (010 ()))
      ((010 value) (010 (001 (0))))
      ((010 ()) (knowledge-proper-list? (011 value))))))

(0011 knowledge-terms-valid?
  (0010 (terms)
    (110
      ((0101 terms) (010 ()))
      ((010 terms) (010 (001 (0))))
      ((knowledge-term-valid? (100 terms))
       (knowledge-terms-valid? (011 terms)))
      ((010 ()) (010 (001 (0)))))))

(0011 knowledge-term-valid?
  (0010 (term)
    (110
      ((010 term) (010 ()))
      ((010 (100 term))
       (110
         ((101 (100 term) (001 var))
          (110
            ; (var name) is unary: D3 ATOM checks cdr/cddr directly.
            ; No D6 LENGTH or unqualified numeric arity literal is needed.
            ((010 (011 term)) (010 (001 (0))))
            ((010 (011 (011 term))) (knowledge-symbol? (1001 term)))
            ((010 ()) (010 (001 (0))))))
         ((010 ()) (knowledge-terms-valid? term))))
      ((010 ()) (knowledge-terms-valid? term)))))

(0011 knowledge-not-head?
  (0010 (head)
    (110
      ((101 head (001 not?)) (010 ()))
      ((101 head (001 not)) (010 ()))
      ((010 ()) (010 (001 (0)))))))

(0011 knowledge-goal-valid?
  (0010 (goal)
    (110
      ((010 goal) (010 (001 (0))))
      ((0100 (knowledge-proper-list? goal)) (010 (001 (0))))
      ((0100 (knowledge-symbol? (100 goal))) (010 (001 (0))))
      ((knowledge-not-head? (100 goal))
       (110
         ; (not? goal) and (not goal) accept exactly one argument.
         ; D3 ATOM/CDR distinguish zero, one, and excess arguments.
         ((010 (011 goal)) (010 (001 (0))))
         ((010 (011 (011 goal))) (knowledge-goal-valid? (1001 goal)))
         ((010 ()) (010 (001 (0))))))
      ((010 ()) (knowledge-terms-valid? (011 goal))))))

(0011 knowledge-goals-valid?
  (0010 (goals)
    (110
      ((0101 goals) (010 ()))
      ((010 goals) (010 (001 (0))))
      ((knowledge-goal-valid? (100 goals))
       (knowledge-goals-valid? (011 goals)))
      ((010 ()) (010 (001 (0)))))))

(0011 knowledge-clause-valid?
  (0010 (clause)
    (110
      ((010 clause) (010 (001 (0))))
      ((0100 (knowledge-proper-list? clause)) (010 (001 (0))))
      ((0100 (knowledge-goal-valid? (100 clause))) (010 (001 (0))))
      ((010 ()) (knowledge-goals-valid? (011 clause))))))

;; Explicit opposites operate on heads, not whole clauses: a rule and a fact
;; may derive the same head, and either is sufficient evidence.
;; Явні протилежності працюють із головами, не з цілими clause: правило і
;; факт можуть вивести ту саму голову, і кожного достатньо як доказу.
;; Explizite Gegensätze arbeiten mit Köpfen statt ganzen Clauses: Regel und
;; Fakt können denselben Kopf ableiten; jeder ist als Beleg ausreichend.
(0011 opposite-knowledge-head
  (0010 (head)
    (110
      ((knowledge-not-head? (100 head)) (1001 head))
      ((010 ()) (1110 (001 not?) head)))))

(0011 advice-conflict-proof
  (0010 (module-name clause)
    (110
      ((101010010 module-name)
       ((0010 (proofs) (110
           ((0100 (010 proofs)) (110
              ((101 (100 (100 clause)) (001 not)) (001 ()))
              ((101 (100 (100 clause)) (001 not?)) (001 ()))
              ((010 ()) (101111010 module-name (1110 (001 not?) (100 clause))))))
           ((010 proofs)  (110
              ((101 (100 (100 clause)) (001 not)) (001 ()))
              ((101 (100 (100 clause)) (001 not?)) (001 ()))
              ((010 ()) (101111010 module-name (1110 (001 not?) (100 clause))))))
           ((010 ()) proofs))) (101111010 module-name (opposite-knowledge-head (100 clause)))))
      )))

(0011 advice-decision
  (0010 (module-name clause)
    (110
      ((0100 (knowledge-symbol? module-name))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) clause)))
      ((101 (knowledge-clause-valid? clause) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clause)))
      ((010 ())
       ((0010 (opposite proofs) (110
           ((0100 (010 proofs)) (1110 (001 accepted) (1110 (001 module) module-name) (1110 (001 knowledge) clause)))
           ((010 proofs)  (1110 (001 accepted) (1110 (001 module) module-name) (1110 (001 knowledge) clause)))
           ((010 ())
            (1110 (001 conflict)
                  (1110 (001 new) clause)
                  (1110 (001 existing) opposite)
                  (1110 (001 proof) (100 proofs)))))) (opposite-knowledge-head (100 clause)) (advice-conflict-proof module-name clause))))))

;; The accepted branch evaluates `def` in the caller's frame, then returns
;; the structured decision. A helper lambda would write into a disposable
;; child frame, so sequencing intentionally lives in the macro expansion.
;; Прийнята гілка виконує `def` у фреймі викликача й повертає структуроване
;; рішення. Допоміжна lambda писала б у тимчасовий дочірній фрейм, тому
;; послідовність навмисно міститься безпосередньо в macro expansion.
;; Der akzeptierte Zweig führt `def` im Frame des Aufrufers aus und gibt die
;; strukturierte Entscheidung zurück. Eine Hilfs-Lambda würde in einen
;; kurzlebigen Kind-Frame schreiben; daher liegt die Sequenz im Makro selbst.
(0011 advise (make-macro (0010 (module-name clause)
  (1110 (001 cond)
        (1110
          (1110 (001 equal?)
                (1110 (001 00000101) (1110 (001 advice-decision) (1110 (001 quote) module-name) clause))
                (1110 (001 quote) (001 accepted)))
          (1110 (001 second)
                (1110 (001 list)
                      (1110 (001 def) (001 *knowledge-journal*)
                            (1110 (001 append)
                                  (1110 (001 clauses->tell-events)
                                        (1110 (001 quote) module-name)
                                        (1110 (001 list) clause))
                                  (001 *knowledge-journal*)))
                      (1110 (001 list)
                            (1110 (001 quote) (001 accepted))
                            (1110 (001 list)
                                  (1110 (001 quote) (001 module))
                                  (1110 (001 quote) module-name))
                            (1110 (001 list) (1110 (001 quote) (001 knowledge)) clause)))))
        (1110 (001 t) (1110 (001 advice-decision) (1110 (001 quote) module-name) clause))))))

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
(0011 knowledge-clauses-valid?
  (0010 (clauses)
    (110
      ((0101 clauses) (010 ()))
      ((010 clauses) (010 (001 (0))))
      ((knowledge-clause-valid? (100 clauses))
       (knowledge-clauses-valid? (011 clauses)))
      ((010 ()) (010 (001 (0)))))))

(0011 advice-negative-head-conflict
  (0010 (rules all-rules)
    (110
      
      ((010 rules)  (001 ()))
      ((010 ())
       ((0010 (head) (110
           ((knowledge-not-head? (100 head))
            ((0010 (positive) ((0010 (proofs) (110
                  ((0100 (010 proofs)) (advice-negative-head-conflict (011 rules) all-rules))
                  ((010 proofs)  (advice-negative-head-conflict (011 rules) all-rules))
                  ((010 ()) (1110 head positive (100 proofs))))) (101001110 positive all-rules))) (1001 head)))
           ((010 ()) (advice-negative-head-conflict (011 rules) all-rules)))) (100 (100 rules)))))))

(0011 advice-batch-conflict
  (0010 (clauses remaining all-rules)
    (110
      ((0100 (010 remaining)) ((0010 (global) (110
           
           ((010 global)  (001 ()))
           ((010 ()) (1110 (100 clauses) (100 global) (10011 global))))) (advice-negative-head-conflict all-rules all-rules)))
      ((010 remaining)  ((0010 (global) (110
           
           ((010 global)  (001 ()))
           ((010 ()) (1110 (100 clauses) (100 global) (10011 global))))) (advice-negative-head-conflict all-rules all-rules)))
      ((010 ())
       ((0010 (opposite) ((0010 (proofs) (110
             ((0100 (010 proofs)) (advice-batch-conflict clauses (011 remaining) all-rules))
             ((010 proofs)  (advice-batch-conflict clauses (011 remaining) all-rules))
             ((010 ()) (1110 (100 remaining) opposite (100 proofs))))) (101001110 opposite all-rules))) (opposite-knowledge-head (100 (100 remaining))))))))

(0011 advice-all-decision
  (0010 (module-name clauses)
    (110
      ((0100 (knowledge-symbol? module-name))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) clauses)))
      ((0100 (010 clauses)) (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((010 clauses)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-proper-list? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-clauses-valid? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clauses)))
      ((010 ())
       ((0010 (existing) ((0010 (conflict) (110
             ((0100 (010 conflict)) (1110 (001 accepted)
                    (1110 (001 module) module-name)
                    (1110 (001 knowledge) clauses)))
             ((010 conflict)  (1110 (001 accepted)
                    (1110 (001 module) module-name)
                    (1110 (001 knowledge) clauses)))
             ((010 ())
              (1110 (001 conflict)
                    (1110 (001 new) (100 conflict))
                    (1110 (001 existing) (1001 conflict))
                    (1110 (001 proof) (10011 conflict)))))) (advice-batch-conflict clauses clauses
                                                (1111 clauses existing)))) (110
                         ((101010010 module-name)
                          (110000011 module-name))
                         ))))))

;; As with `advise`, sequencing stays in the macro so `def` updates the
;; caller's persistent frame rather than a helper lambda's temporary frame.
;; Як і в `advise`, послідовність лишається в макросі, щоб `def` оновлював
;; сталий фрейм викликача, а не тимчасовий фрейм допоміжної lambda.
;; Wie bei `advise` bleibt die Sequenz im Makro, damit `def` den dauerhaften
;; Aufrufer-Frame statt des temporären Frames einer Hilfs-Lambda aktualisiert.
(0011 advise-all (make-macro (0010 (module-name clauses)
  (1110 (001 cond)
        (1110
          (1110 (001 equal?)
                (1110 (001 00000101)
                      (1110 (001 advice-all-decision)
                            (1110 (001 quote) module-name) clauses))
                (1110 (001 quote) (001 accepted)))
          (1110 (001 second)
                (1110 (001 list)
                      (1110 (001 def) (001 *knowledge-journal*)
                            (1110 (001 append)
                                  (1110 (001 clauses->tell-events)
                                        (1110 (001 quote) module-name) clauses)
                                  (001 *knowledge-journal*)))
                      (1110 (001 list)
                            (1110 (001 quote) (001 accepted))
                            (1110 (001 list)
                                  (1110 (001 quote) (001 module))
                                  (1110 (001 quote) module-name))
                            (1110 (001 list) (1110 (001 quote) (001 knowledge)) clauses)))))
        (1110 (001 t)
              (1110 (001 advice-all-decision)
                    (1110 (001 quote) module-name) clauses))))))

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
(0011 *knowledge-package-version* (001 (0 1)))

(0011 knowledge-package-entries-valid?
  (0010 (entries)
    (110
      ((0101 entries) (010 ()))
      ((010 entries) (010 (001 (0))))
      ((010 (100 entries)) (010 (001 (0))))
      ((knowledge-symbol? (100 (100 entries)))
       (knowledge-package-entries-valid? (011 entries)))
      ((010 ()) (010 (001 (0)))))))

(0011 knowledge-package-field
  (0010 (name package)
    (110
      ((010 package) (001 ()))
      ((101 name (100 (100 package))) (011 (100 package)))
      ((010 ()) (knowledge-package-field name (011 package))))))

(0011 make-knowledge-package
  (0010 (module-name clauses)
    (1110 (111 (001 format) (001 my-lisp-knowledge))
          (111 (001 version) *knowledge-package-version*)
          (111 (001 module) module-name)
          (111 (001 clauses) clauses))))

(0011 knowledge-package-decision
  (0010 (package)
    (110
      ((010 package)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-package)) (1110 (001 input) package)))
      ((0100 (knowledge-proper-list? package))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-package)) (1110 (001 input) package)))
      ((0100 (knowledge-package-entries-valid? package))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-package)) (1110 (001 input) package)))
      ((101 (knowledge-package-field (001 format) package) (001 my-lisp-knowledge))
       (110
         ((unify-equal? (knowledge-package-field (001 version) package)
                  *knowledge-package-version*)
          (advice-all-decision (knowledge-package-field (001 module) package)
                               (knowledge-package-field (001 clauses) package)))
         ((010 ()) (1110 (001 rejected)
                  (1110 (001 reason) (001 unsupported-version))
                  (1110 (001 version) (knowledge-package-field (001 version) package))))))
      ((010 ()) (1110 (001 rejected)
               (1110 (001 reason) (001 invalid-package))
               (1110 (001 input) package))))))

;; Import uses the same atomic journal update as `advise-all`. The module name
;; is read from data at runtime, so this is a separate macro rather than a thin
;; call to `advise-all`, whose module argument is intentionally literal syntax.
;; Імпорт використовує те саме атомарне оновлення, що й `advise-all`; назва
;; модуля читається з даних під час виконання, тому це окремий макрос.
;; Der Import nutzt dasselbe atomare Journal-Update wie `advise-all`; der
;; Modulname kommt zur Laufzeit aus Daten, daher ist dies ein eigenes Makro.
(0011 import-knowledge-package (make-macro (0010 (package)
  (1110 (001 cond)
        (1110
          (1110 (001 equal?)
                (1110 (001 00000101) (1110 (001 knowledge-package-decision) package))
                (1110 (001 quote) (001 accepted)))
          (1110 (001 second)
                (1110 (001 list)
                      (1110 (001 def) (001 *knowledge-journal*)
                            (1110 (001 append)
                                  (1110 (001 clauses->tell-events)
                                        (1110 (001 knowledge-package-field)
                                              (1110 (001 quote) (001 module)) package)
                                        (1110 (001 knowledge-package-field)
                                              (1110 (001 quote) (001 clauses)) package))
                                  (001 *knowledge-journal*)))
                      (1110 (001 knowledge-package-decision) package))))
        (1110 (001 t) (1110 (001 knowledge-package-decision) package))))))

(0011 import-knowledge-file (make-macro (0010 (path)
  (1110 (001 import-knowledge-package)
        (1110 (001 01001010) (1110 (001 read-file) path))))))

;; Export is deliberately a plain function: unlike import it does not mutate
;; the knowledge journal. It validates the module and clauses, serializes the
;; canonical package with `write-to-string`, and writes exactly one expression.
;; Експорт не змінює журнал: перевіряє дані, канонічно серіалізує й записує.
;; Export verändert das Journal nicht: prüfen, kanonisch serialisieren, schreiben.
(0011 write-knowledge-package
  (0010 (path module-name clauses)
    (110
      ((0100 (knowledge-symbol? module-name))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) module-name)))
      ((0100 (010 clauses)) (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((010 clauses)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-proper-list? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-clauses-valid? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clauses)))
      ((010 ())
       ((0010 (package) (1001 (1110 (110111100 path (11110100 package)) package))) (make-knowledge-package module-name clauses))))))

;; TCP transport uses one package per connection and EOF as the frame boundary.
;; TCP may split one write into many reads, so the receiver drains every chunk
;; before parsing exactly one S-expression. The sender closes only after
;; `tcp-write` succeeds. No received bytes are ever passed to `eval`.
;; TCP-транспорт: один пакет на з'єднання, EOF — межа; отримане ніколи не `eval`.
;; TCP-Transport: ein Paket pro Verbindung, EOF als Grenze; Empfang nie per `eval`.
(0011 tcp-read-to-eof
  (0010 (connection accumulated)
    ((0010 (chunk) (110
        ((110011100 chunk) accumulated)
        ((010 ()) (tcp-read-to-eof connection
                            (110011110 accumulated chunk))))) (110111110 connection))))

(0011 send-knowledge-package
  (0010 (connection module-name clauses)
    (110
      ((0100 (knowledge-symbol? module-name))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) module-name)))
      ((0100 (010 clauses)) (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((010 clauses)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-proper-list? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-clauses-valid? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clauses)))
      ((010 ())
       ((0010 (package) (10011 (1110 (110110011 connection (11110100 package))
                      (tcp-close connection)
                      package))) (make-knowledge-package module-name clauses))))))

(0011 receive-knowledge-package (make-macro (0010 (connection)
  (1110 (001 second)
        (1110 (001 list)
              (1110 (001 def) (001 *received-knowledge-package*)
                    (1110 (001 01001010) (1110 (001 tcp-read-to-eof) connection "")))
              (1110 (001 import-knowledge-package) (001 *received-knowledge-package*)))))))

;; A newline-framed request/receipt protocol keeps the connection open long
;; enough for the receiver to answer with the structured import decision.
;; `write-to-string` escapes newlines inside string values, so a literal LF is
;; an unambiguous frame boundary. One request and one receipt per connection
;; means no unread suffix has to survive between calls.
;; Протокол із LF-frame лишає з'єднання відкритим для структурованої квитанції.
;; LF-gerahmtes Protokoll hält die Verbindung für eine strukturierte Quittung offen.
(0011 string-through-line
  (0010 (text accumulated)
    (110
      ((110011100 text) (001 ()))
      ((101 (110101011 text) "\n") (1110 accumulated))
      ((010 ()) (string-through-line
           (110011101 text)
           (110011110 accumulated (110101011 text)))))))

(0011 tcp-read-frame
  (0010 (connection accumulated)
    ((0010 (chunk) (110
        ((110011100 chunk) (001 ()))
        ((010 ())
         ((0010 (line) (110
             ((0100 (010 line)) (tcp-read-frame connection (110011110 accumulated chunk)))
             ((010 line)  (tcp-read-frame connection (110011110 accumulated chunk)))
             ((010 ()) (100 line)))) (string-through-line
                       (110011110 accumulated chunk) ""))))) (110111110 connection))))

(0011 exchange-knowledge-package
  (0010 (connection module-name clauses)
    (110
      ((0100 (knowledge-symbol? module-name))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) module-name)))
      ((0100 (010 clauses)) (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((010 clauses)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-proper-list? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((0100 (knowledge-clauses-valid? clauses))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clauses)))
      ((010 ())
       ((0010 (package) (10011
           (1110
             (110110011 connection
                        (110011110 (11110100 package) "\n"))
             (0011 *knowledge-receipt-text* (tcp-read-frame connection ""))
             ((0010 (receipt) (1001 (1110 (tcp-close connection) receipt))) (11101010 *knowledge-receipt-text*))))) (make-knowledge-package module-name clauses))))))

(0011 accept-knowledge-exchange (make-macro (0010 (connection)
  (1110 (001 second)
        (1110 (001 list)
              (1110 (001 def) (001 *received-knowledge-package*)
                    (1110 (001 01001010) (1110 (001 tcp-read-frame) connection "")))
              (1110 (001 let)
                    (1110 (1110 (001 decision)
                                (1110 (001 import-knowledge-package)
                                      (001 *received-knowledge-package*))))
                    (1110 (001 second)
                          (1110 (001 list)
                                (1110 (001 tcp-write) connection
                                      (1110 (001 string-append)
                                            (1110 (001 write-to-string) (001 decision))
                                            "\n"))
                                (1110 (001 second)
                                      (1110 (001 list)
                                            (1110 (001 tcp-close) connection)
                                            (001 decision)))))))))))

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
(0011 contains-atom?
  (0010 (item lst)
    (110
      ((0101 lst) (010 (001 (0))))
      ((010 lst) (010 (001 (0))))
      ((010 (100 lst))
       (110
         ((101 (100 lst) item) (010 ()))
         ((010 ()) (contains-atom? item (011 lst)))))
      ((010 ()) (contains-atom? item (011 lst))))))

(0011 is-fact?
  (0010 (clause)
    (110
      ((0100 (010 (011 clause)))
       (1110 (001 clause-kind) (001 fact)))
      ((010 (011 clause)) 
       (1110 (001 clause-kind) (001 rule))))))

;; collect-facts-about consumes the explicit clause-domain result. Its list
;; traversal and the legacy contains-atom? compatibility result are also
;; dispatched explicitly, so no generic truthiness decides whether a clause is
;; a fact worth reporting.
(0011 collect-facts-about
  (0010 (item clauses)
    (110
      
      ((010 clauses)  (001 ()))
      ((010 clauses) 
       ((0010 (clause) ((0010 (head) (110
             ((101011111 clause) 
              (101011001 item (011 clauses)))
             ((101011111 clause) 
              ((0010 (contains) (110
                  ((101 contains (001 ())) 
                   (101011001 item (011 clauses)))
                  ((101 contains (001 ())) 
                   (111 head (101011001 item (011 clauses)))))) (101110011 item head))))) (100 clause))) (100 clauses))))))

;; describe returns every known fact about `item` within `module-name`,
;; or `Module-not-found` for consistency with `reason-in`.
(0011 describe
  (0010 (item module-name)
    (110
      ((101010010 module-name) (101011001 item (110000011 module-name)))
      ((010 ()) (001 Module-not-found)))))

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
(0011 *usage-counts* (001 ()))

(0011 record-usage! (make-macro (0010 (proof)
  (1110 (001 def) (001 *usage-counts*)
        (1110 (001 merge-usage) (1110 (001 count-usage) proof) (001 *usage-counts*))))))

(0011 usage-of
  (0010 (rule-head)
    ((0010 (entry) (110
        
        ((010 entry)  0)
        ((010 ()) (011 entry)))) (11100 rule-head *usage-counts*))))
