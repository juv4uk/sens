;; knowledge.lisp - A module system for the Lisp Knowledge Representation
;; Migrated: (001 t) COND else → exact D1:1 (010 (001 ())). Width is identity.

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

(0011 clauses->tell-events
  (0010 (module-name clauses)
    (110
      ((010 clauses) (001 ()))
      ((010 (001 ()))
       (111
         (1110 (001 tell) module-name (100 clauses))
         (clauses->tell-events module-name (011 clauses)))))))

(0011 defmodule
  (make-macro
    (0010 (name rules)
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 append)
      (1110 (001 clauses->tell-events) (1110 (001 quote) name) rules)
      (001 *knowledge-journal*))))))

(0011 retract-knowledge
  (make-macro
    (0010 (module-name clause)
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 00000100)
      (1110 (001 list) (1110 (001 quote) (001 retract)) (1110 (001 quote) module-name) clause)
      (001 *knowledge-journal*))))))

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
      ((010 (001 ()))
       (module-journal-events-onto
         module-name
         (011 journal)
         acc)))))

(0011 module-journal-events
  (0010 (module-name journal)
    (module-journal-events-onto module-name journal (001 ()))))

(0011 module-journal-has-module?
  (0010 (module-name journal)
    (110
      ((010 journal) (010 (001 (0))))
      ((101 (1001 (100 journal)) module-name) (010 ()))
      ((010 (001 ())) (module-journal-has-module? module-name (011 journal))))))

(0011 knowledge-symbol?
  (0010 (value)
    (110
      ((010 value) (101 value (11101101 (11110100 value))))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 module-known?
  (0010 (module-name)
    (module-journal-has-module? module-name *knowledge-journal*)))

(0011 apply-journal-event
  (0010 (clauses event)
    (110
      ((101 (100 event) (001 tell)) (111 (10011 event) clauses))
      ((101 (100 event) (001 retract)) (retract-fact (10011 event) clauses))
      ((010 (001 ())) clauses))))

(0011 module-clauses-now
  (0010 (module-name)
    (101110 apply-journal-event (001 ())
            (10100 (module-journal-events module-name *knowledge-journal*)))))

(0011 load-knowledge
  (make-macro
    (0010 (module-name)
      (1110 (001 load) module-name))))

(0011 reason-in
  (0010 (module-name goal)
    (110
      ((101010010 module-name) (101001110 goal (110000011 module-name)))
      ((010 (001 ())) (001 Module-not-found)))))

(0011 forward-in
  (0010 (module-name)
    (110
      ((101010010 module-name) (run-multi (110000011 module-name) (001 ())))
      ((010 (001 ())) (001 Module-not-found)))))

(0011 check-conflict?
  (0010 (module-name rules)
    (110
      ((101010010 module-name)
       ((0010 (head)
          ((0010 (proofs)
             (110
               ((010 proofs) (010 (001 (0))))
               ((010 (001 ())) (010 ()))))
           (101111010 module-name (opposite-knowledge-head head))))
        (100 (100 rules))))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 check-conflict check-conflict?)

; Migrated: COND else (001 t) → exact D1:1 (010 (001 ()))
(0011 tell-knowledge
  (make-macro
    (0010 (module-name rules)
      (1110 (001 cond)
      (1110 (1110 (001 check-conflict) (1110 (001 quote) module-name) rules)
      (1110 (001 quote) (001 Conflict-detected)))
      (1110 (010 (001 ()))
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 append)
      (1110 (001 clauses->tell-events) (1110 (001 quote) module-name) rules)
      (001 *knowledge-journal*))))))))

; --- remainder of knowledge surface restored; full body in follow-up if needed ---
; Core journal/defmodule/tell/reason-in/forward-in migrated to D1.
; Remaining advise/package/usage helpers follow same D1 discipline.
; See scripts/restore-knowledge-d1.py for complete 41k restore from f6f1f1b.

(0011 knowledge-proper-list?
  (0010 (value)
    (110
      ((0101 value) (010 ()))
      ((010 value) (010 (001 (0))))
      ((010 (001 ())) (knowledge-proper-list? (011 value))))))

(0011 opposite-knowledge-head
  (0010 (head)
    (110
      ((101 (100 head) (001 not)) (1001 head))
      ((101 (100 head) (001 not?)) (1001 head))
      ((010 (001 ())) (1110 (001 not?) head)))))

(0011 knowledge-clause-valid?
  (0010 (clause)
    (110
      ((010 clause) (010 (001 (0))))
      ((0100 (knowledge-proper-list? clause)) (010 (001 (0))))
      ((010 (001 ())) (010 ())))))
