;; LEGACY_MIGRATION_DEBT #5605 / owner prohibition #5789: old #d1:0/#d1:1
;; are NOT current SENS literals. Do not introduce any new literal carrier.
;; The old parse() path is legacy provenance, not permission or language law.
;; Retire only with positional D1 reader, positive/negative native SENS
;; witnesses and exact physical Zig T5 round-trip; never numeric substitution.
;; knowledge.lisp - A module system for the Lisp Knowledge Representation
;; Direct predicates use exact D1:1/D1:0; D3 ATOM only tests actual shapes.

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
      (#d1:1
       (111
         (1110 (001 tell) module-name (100 clauses))
         (перетворити-клаузи-на-події-повідомлення module-name (решта clauses)))))))

(0011 defmodule
  (make-macro
    (0010 (name rules)
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 append)
      (список (як-є перетворити-клаузи-на-події-повідомлення) (список (як-є quote) name) rules)
      (001 *knowledge-journal*))))))

; Вилучено спадкову SID8-ідентичність 00000100: це НЕ D3 CONS.
; За ратифікованою таблицею D8:00000100 = PROG1, D3:111 = CONS.
; У цитованому AST макросу зберігаємо саме точний D3:111 (3 біти).
(0011 retract-knowledge
  (make-macro
    (0010 (module-name clause)
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 111)
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
      (#d1:1
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
      ((010 journal) #d1:0)
      ((101 (1001 (100 journal)) module-name) #d1:1)
      (так (журнал-містить-записи-модуля? module-name (решта journal))))))

; One symbol law is owned by Core; do not duplicate historical blank W8 slots.
(0011 knowledge-symbol?
  (0010 (value)
    (symbol? value)))

(0011 module-known?
  (0010 (module-name)
    (журнал-містить-записи-модуля? module-name *knowledge-journal*)))

(0011 apply-journal-event
  (0010 (clauses event)
    (110
      ((101 (100 event) (001 tell)) (111 (10011 event) clauses))
      ((101 (100 event) (001 retract)) (retract-fact (10011 event) clauses))
      (#d1:1 clauses))))

(0011 module-clauses-now
  (0010 (module-name)
    (101110 apply-journal-event (001 ())
            (зворот (отримати-події-журналу-окремого-модуля module-name *knowledge-journal*)))))

(0011 load-knowledge
  (make-macro
    (0010 (module-name)
      (1110 (001 load) module-name))))

(0011 reason-in
  (0010 (module-name goal)
    (110
      ((101010010 module-name) (101001110 goal (110000011 module-name)))
      (#d1:1 (001 Module-not-found)))))

(0011 forward-in
  (0010 (module-name)
    (110
      ((101010010 module-name) (run-multi (110000011 module-name) (001 ())))
      (#d1:1 (001 Module-not-found)))))

(0011 check-conflict?
  (0010 (module-name rules)
    (110
      ((101010010 module-name)
       ((0010 (head)
          ((0010 (proofs)
             (110
               ((010 proofs) #d1:0)
               (#d1:1 #d1:1)))
           (міркувати-у module-name (отримати-протилежну-голову-твердження-знання head))))
        (1000 rules)))
      (#d1:1 #d1:0))))

(0011 check-conflict check-conflict?)

; COND macro expansion now carries its W1 guard directly, without ATOM.
(0011 tell-knowledge
  (make-macro
    (0010 (module-name rules)
      (1110 (001 cond)
      (1110 (1110 (001 check-conflict) (1110 (001 quote) module-name) rules)
      (1110 (001 quote) (001 Conflict-detected)))
      (1110 #d1:1
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 append)
      (список (як-є перетворити-клаузи-на-події-повідомлення) (список (як-є quote) module-name) rules)
      (001 *knowledge-journal*))))))))

; Валідатори термів і цілей відновлено окремим доказовим зрізом.
; Інші заархівовані API не вмикаються цим патчем: кожен потребує власного
; SENS-закону й залишається fail-closed до такого доказу.

(0011 knowledge-proper-list?
  (0010 (value)
    (110
      ((0101 value) #d1:1)
      ((010 value) #d1:0)
      (так (правильно-структурований-список-знань? (решта value))))))

(0011 opposite-knowledge-head
  (0010 (head)
    (110
      ((101 (100 head) (001 not)) (1001 head))
      ((101 (100 head) (001 not?)) (1001 head))
      (#d1:1 (1110 (001 not?) head)))))

(0011 knowledge-clause-valid?
  (0010 (clause)
    (110
      ((010 clause) #d1:0)
      ((хибне? (правильно-структурований-список-знань? clause)) ні)
      ((хибне? (ціль-бази-знань-коректна? (перше clause))) ні)
      (так (цілі-бази-знань-коректні? (решта clause))))))

;; Точна арність змінної (var ім'я) та заперечення (not?/not goal):
;; D3 ATOM/CDR + D4 CADR/NOT, без D6 LENGTH і некваліфікованого числа 2.
;; Очікування семантики лежать у tests/semantic/knowledge-exact-arity-structure.bits.

(0011 knowledge-not-head?
  (0010 (head)
    (110
      ((101 head (001 not?)) #d1:1)
      ((101 head (001 not)) #d1:1)
      (#d1:1 #d1:0))))

(0011 knowledge-terms-valid?
  (0010 (terms)
    (110
      ((0101 terms) #d1:1)
      ((010 terms) #d1:0)
      ((терм-бази-знань-коректний? (перше terms))
       (терми-бази-знань-коректні? (решта terms)))
      (#d1:1 #d1:0))))

(0011 knowledge-term-valid?
  (0010 (term)
    (110
      ((010 term) #d1:1)
      ((010 (100 term))
       (110
         ((101 (100 term) (001 var))
          (110
            ; (var ім'я): нуль аргументів відхиляємо; один перевіряємо,
            ; пару після CDDR відхиляємо. Жодного числового LENGTH.
            ((010 (011 term)) #d1:0)
            ((010 (011 (011 term))) (knowledge-symbol? (1001 term)))
            (#d1:1 #d1:0)))
         (так (терми-бази-знань-коректні? term))))
      (так (терми-бази-знань-коректні? term)))))

(0011 knowledge-goal-valid?
  (0010 (goal)
    (110
      ((010 goal) #d1:0)
      ((хибне? (правильно-структурований-список-знань? goal)) ні)
      ((0100 (knowledge-symbol? (100 goal))) #d1:0)
      ((голова-твердження-знань-заперечена? (перше goal))
       (110
         ; (not? goal) та (not goal) мають мати рівно один аргумент.
         ((010 (011 goal)) #d1:0)
         ((атом? (решта (решта goal))) (ціль-бази-знань-коректна? (друге goal)))
         (#d1:1 #d1:0)))
      (так (терми-бази-знань-коректні? (решта goal))))))

(0011 knowledge-goals-valid?
  (0010 (goals)
    (110
      ((0101 goals) #d1:1)
      ((010 goals) #d1:0)
      ((ціль-бази-знань-коректна? (перше goals))
       (цілі-бази-знань-коректні? (решта goals)))
      (#d1:1 #d1:0))))

(0011 knowledge-clauses-valid?
  (0010 (clauses)
    (110
      ((0101 clauses) #d1:1)
      ((010 clauses) #d1:0)
      ((клауза-бази-знань-коректна? (перше clauses))
       (клаузи-бази-знань-коректні? (решта clauses)))
      (#d1:1 #d1:0))))

; Повернено історичний пакетний закон із lib/knowledge.lisp @ 327b51ca,
; не новий host-shim. Первинна міграція D4 DEFINE/LAMBDA, D3 COND/CAR/CDR,
; D4 NULL, D9:101001110 REASON; рішення про наявність доказу — D1.
; Десятибітні координати цих похідних функцій не оголошуються викличними:
; лише SENS-DEFINE встановлює їхні локальні Lisp-зв'язування.
; Нуль доказів = D4 NULL(()) -> продовжити; наявний доказ -> конфлікт.
(0011 advice-negative-head-conflict
  (0010 (rules all-rules)
    (110
      ((0101 rules) (001 ()))
      ((010 rules) (001 ()))
      (#d1:1
       ((0010 (head)
          (110
            ((голова-твердження-знань-заперечена? (перше head))
             ((0010 (positive)
                ((0010 (proofs)
                   (110
                     ((0101 proofs)
                      (суперечність-запереченій-голові-правила (решта rules) all-rules))
                     (#d1:1 (1110 head positive (100 proofs)))))
                 (101001110 positive all-rules)))
              (1001 head)))
            (#d1:1
             (суперечність-запереченій-голові-правила (решта rules) all-rules))))
        (100 (100 rules)))))))

; Фіксуємо один з трьох доказів конфлікту: нова клауза, протилежна
; голова, перший доказ. Спочатку весь пакет, тоді чинні світові правила.
; Якщо жодна пара не суперечить — точний порожній список, без host truth.
(0011 advice-batch-conflict
  (0010 (clauses remaining all-rules)
    (110
      ((0101 remaining)
       ((0010 (global)
          (110
            ((0101 global) (001 ()))
            (#d1:1
             (1110 (100 clauses) (100 global) (10011 global)))))
        (суперечність-запереченій-голові-правила all-rules all-rules)))
      ((010 remaining) (001 ()))
      (#d1:1
       ((0010 (opposite)
          ((0010 (proofs)
             (110
               ((0101 proofs)
                (advice-batch-conflict clauses (011 remaining) all-rules))
               (#d1:1
                (1110 (100 remaining) opposite (100 proofs)))))
           (101001110 opposite all-rules)))
        (отримати-протилежну-голову-твердження-знання (перше (перше remaining))))))))

; Ратифікований D4:1000 = CAR(CAR), D4:0110 = CDR(CAR).
; Точна бітність та однобітний негатив: tests/semantic/knowledge-d4-selectors-*.bits.
(0011 knowledge-package-field
  (0010 (name package)
    (110
      ((010 package) (001 ()))
      ((101 name (1000 package)) (0110 package))
      (так (отримати-поле-пакета-знань name (решта package))))))

; Історичний пакет знань 0.1 відновлений з lib/knowledge.lisp @ 327b51ca1f.
; Дані пакета не eval. Назви полів належать цитованим даним, не D7-функціям.
; Умови: пряма D1-бітність; D4:1000 CAAR; D3:111 CONS; D4:1110 LIST.
; Ні SID8-псевдонімів, ні D10-ратифікації чи нових примітивів.
(0011 *knowledge-package-version* (001 (0 1)))

(0011 knowledge-package-entries-valid?
  (0010 (entries)
    (110
      ((0101 entries) #d1:1)
      ((010 entries) #d1:0)
      ((010 (100 entries)) #d1:0)
      ((knowledge-symbol? (1000 entries))
       (записи-пакета-знань-коректні? (решта entries)))
      (#d1:1 #d1:0))))

(0011 make-knowledge-package
  (0010 (module-name clauses)
    (1110 (111 (001 format) (001 my-lisp-knowledge))
          (111 (001 version) *knowledge-package-version*)
          (111 (001 module) module-name)
          (111 (001 clauses) clauses))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити суперечність-запереченій-голові-правила advice-negative-head-conflict)
(визначити перетворити-клаузи-на-події-повідомлення clauses->tell-events)
(визначити клауза-бази-знань-коректна? knowledge-clause-valid?)
(визначити клаузи-бази-знань-коректні? knowledge-clauses-valid?)
(визначити ціль-бази-знань-коректна? knowledge-goal-valid?)
(визначити цілі-бази-знань-коректні? knowledge-goals-valid?)
(визначити голова-твердження-знань-заперечена? knowledge-not-head?)
(визначити записи-пакета-знань-коректні? knowledge-package-entries-valid?)
(визначити отримати-поле-пакета-знань knowledge-package-field)
(визначити правильно-структурований-список-знань? knowledge-proper-list?)
(визначити терм-бази-знань-коректний? knowledge-term-valid?)
(визначити терми-бази-знань-коректні? knowledge-terms-valid?)
(визначити отримати-події-журналу-окремого-модуля module-journal-events)
(визначити журнал-містить-записи-модуля? module-journal-has-module?)
(визначити отримати-протилежну-голову-твердження-знання opposite-knowledge-head)
