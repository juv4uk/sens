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
(визначити *knowledge-journal* (як-є ()))

(визначити clauses->tell-events
  (функція (module-name clauses)
    (за-умовою
      ((атом? clauses) (як-є ()))
      (так
       (сполучити
         (список (як-є tell) module-name (перше clauses))
         (перетворити-клаузи-на-події-повідомлення module-name (решта clauses)))))))

(визначити defmodule
  (макрос
    (функція (name rules)
      (список (як-є def) (як-є *knowledge-journal*)
      (список (як-є append)
      (список (як-є перетворити-клаузи-на-події-повідомлення) (список (як-є quote) name) rules)
      (як-є *knowledge-journal*))))))

; Вилучено спадкову SID8-ідентичність 00000100: це НЕ D3 CONS.
; За ратифікованою таблицею D8:00000100 = PROG1, D3:111 = CONS.
; У цитованому AST макросу зберігаємо саме точний D3:111 (3 біти).
(визначити retract-knowledge
  (макрос
    (функція (module-name clause)
      (список (як-є def) (як-є *knowledge-journal*)
      (список (як-є 111)
      (список (як-є list) (список (як-є quote) (як-є retract)) (список (як-є quote) module-name) clause)
      (як-є *knowledge-journal*))))))

(визначити module-journal-events-onto
  (функція (назва-модуля журнал накопичувач)
    (за-умовою
      ((порожній? журнал) (зворот накопичувач))
      ((атом? журнал)  (зворот накопичувач))
      ((тотожне? (друге (перше журнал)) назва-модуля)
       (module-journal-events-onto
         назва-модуля
         (решта журнал)
         (сполучити (перше журнал) накопичувач)))
      (так
       (module-journal-events-onto
         назва-модуля
         (решта журнал)
         накопичувач)))))

(визначити module-journal-events
  (функція (назва-модуля журнал)
    (module-journal-events-onto назва-модуля журнал (як-є ()))))

(визначити module-journal-has-module?
  (функція (назва-модуля журнал)
    (за-умовою
      ((атом? журнал) ні)
      ((тотожне? (друге (перше журнал)) назва-модуля) так)
      (так (журнал-містить-записи-модуля? назва-модуля (решта журнал))))))

; One symbol law is owned by Core; do not duplicate historical blank W8 slots.
(визначити knowledge-symbol?
  (функція (значення)
    (символ? значення)))

(визначити module-known?
  (функція (назва-модуля)
    (журнал-містить-записи-модуля? назва-модуля *knowledge-journal*)))

(визначити apply-journal-event
  (функція (клаузи подія)
    (за-умовою
      ((тотожне? (перше подія) (як-є tell)) (сполучити (третє подія) клаузи))
      ((тотожне? (перше подія) (як-є retract)) (відкликати-факт (третє подія) клаузи))
      (так клаузи))))

(визначити module-clauses-now
  (функція (module-name)
    (згорнути apply-journal-event (як-є ())
            (зворот (отримати-події-журналу-окремого-модуля module-name *knowledge-journal*)))))

(визначити load-knowledge
  (макрос
    (функція (module-name)
      (список (як-є load) module-name))))

(визначити reason-in
  (функція (module-name goal)
    (за-умовою
      ((модуль-відомий? module-name) (міркувати goal (модуль-клаузи-зараз module-name)))
      (так (як-є Module-not-found)))))

(визначити forward-in
  (функція (module-name)
    (за-умовою
      ((модуль-відомий? module-name) (виконати-багатоваріантне-виведення (модуль-клаузи-зараз module-name) (як-є ())))
      (так (як-є Module-not-found)))))

(визначити check-conflict?
  (функція (module-name rules)
    (за-умовою
      ((модуль-відомий? module-name)
       ((функція (head)
          ((функція (proofs)
             (за-умовою
               ((атом? proofs) ні)
               (так так)))
           (міркувати-у module-name (отримати-протилежну-голову-твердження-знання head))))
        (перше-першого rules)))
      (так ні))))

(визначити check-conflict check-conflict?)

; COND macro expansion now carries its W1 guard directly, without ATOM.
(визначити tell-knowledge
  (макрос
    (функція (module-name rules)
      (список (як-є cond)
      (список (список (як-є check-conflict) (список (як-є quote) module-name) rules)
      (список (як-є quote) (як-є Conflict-detected)))
      (список так
      (список (як-є def) (як-є *knowledge-journal*)
      (список (як-є append)
      (список (як-є перетворити-клаузи-на-події-повідомлення) (список (як-є quote) module-name) rules)
      (як-є *knowledge-journal*))))))))

; Валідатори термів і цілей відновлено окремим доказовим зрізом.
; Інші заархівовані API не вмикаються цим патчем: кожен потребує власного
; SENS-закону й залишається fail-closed до такого доказу.

(визначити knowledge-proper-list?
  (функція (value)
    (за-умовою
      ((порожній? value) так)
      ((атом? value) ні)
      (так (правильно-структурований-список-знань? (решта value))))))

(визначити opposite-knowledge-head
  (функція (head)
    (за-умовою
      ((тотожне? (перше head) (як-є not)) (друге head))
      ((тотожне? (перше head) (як-є not?)) (друге head))
      (так (список (як-є not?) head)))))

(визначити knowledge-clause-valid?
  (функція (clause)
    (за-умовою
      ((атом? clause) ні)
      ((хибне? (правильно-структурований-список-знань? clause)) ні)
      ((хибне? (ціль-бази-знань-коректна? (перше clause))) ні)
      (так (цілі-бази-знань-коректні? (решта clause))))))

;; Точна арність змінної (var ім'я) та заперечення (not?/not goal):
;; D3 ATOM/CDR + D4 CADR/NOT, без D6 LENGTH і некваліфікованого числа 2.
;; Очікування семантики лежать у tests/semantic/knowledge-exact-arity-structure.bits.

(визначити knowledge-not-head?
  (функція (head)
    (за-умовою
      ((тотожне? head (як-є not?)) так)
      ((тотожне? head (як-є not)) так)
      (так ні))))

(визначити knowledge-terms-valid?
  (функція (terms)
    (за-умовою
      ((порожній? terms) так)
      ((атом? terms) ні)
      ((терм-бази-знань-коректний? (перше terms))
       (терми-бази-знань-коректні? (решта terms)))
      (так ні))))

(визначити knowledge-term-valid?
  (функція (term)
    (за-умовою
      ((атом? term) так)
      ((атом? (перше term))
       (за-умовою
         ((тотожне? (перше term) (як-є var))
          (за-умовою
            ; (var ім'я): нуль аргументів відхиляємо; один перевіряємо,
            ; пару після CDDR відхиляємо. Жодного числового LENGTH.
            ((атом? (решта term)) ні)
            ((атом? (решта (решта term))) (knowledge-symbol? (друге term)))
            (так ні)))
         (так (терми-бази-знань-коректні? term))))
      (так (терми-бази-знань-коректні? term)))))

(визначити knowledge-goal-valid?
  (функція (goal)
    (за-умовою
      ((атом? goal) ні)
      ((хибне? (правильно-структурований-список-знань? goal)) ні)
      ((хибне? (knowledge-symbol? (перше goal))) ні)
      ((голова-твердження-знань-заперечена? (перше goal))
       (за-умовою
         ; (not? goal) та (not goal) мають мати рівно один аргумент.
         ((атом? (решта goal)) ні)
         ((атом? (решта (решта goal))) (ціль-бази-знань-коректна? (друге goal)))
         (так ні)))
      (так (терми-бази-знань-коректні? (решта goal))))))

(визначити knowledge-goals-valid?
  (функція (goals)
    (за-умовою
      ((порожній? goals) так)
      ((атом? goals) ні)
      ((ціль-бази-знань-коректна? (перше goals))
       (цілі-бази-знань-коректні? (решта goals)))
      (так ні))))

(визначити knowledge-clauses-valid?
  (функція (clauses)
    (за-умовою
      ((порожній? clauses) так)
      ((атом? clauses) ні)
      ((клауза-бази-знань-коректна? (перше clauses))
       (клаузи-бази-знань-коректні? (решта clauses)))
      (так ні))))

; Повернено історичний пакетний закон із lib/knowledge.lisp @ 327b51ca,
; не новий host-shim. Первинна міграція D4 DEFINE/LAMBDA, D3 COND/CAR/CDR,
; D4 NULL, D9:101001110 REASON; рішення про наявність доказу — D1.
; Десятибітні координати цих похідних функцій не оголошуються викличними:
; лише SENS-DEFINE встановлює їхні локальні Lisp-зв'язування.
; Нуль доказів = D4 NULL(()) -> продовжити; наявний доказ -> конфлікт.
(визначити advice-negative-head-conflict
  (функція (rules all-rules)
    (за-умовою
      ((порожній? rules) (як-є ()))
      ((атом? rules) (як-є ()))
      (так
       ((функція (head)
          (за-умовою
            ((голова-твердження-знань-заперечена? (перше head))
             ((функція (positive)
                ((функція (proofs)
                   (за-умовою
                     ((порожній? proofs)
                      (суперечність-запереченій-голові-правила (решта rules) all-rules))
                     (так (список head positive (перше proofs)))))
                 (міркувати positive all-rules)))
              (друге head)))
            (так
             (суперечність-запереченій-голові-правила (решта rules) all-rules))))
        (перше (перше rules)))))))

; Фіксуємо один з трьох доказів конфлікту: нова клауза, протилежна
; голова, перший доказ. Спочатку весь пакет, тоді чинні світові правила.
; Якщо жодна пара не суперечить — точний порожній список, без host truth.
(визначити advice-batch-conflict
  (функція (clauses remaining all-rules)
    (за-умовою
      ((порожній? remaining)
       ((функція (global)
          (за-умовою
            ((порожній? global) (як-є ()))
            (так
             (список (перше clauses) (перше global) (третє global)))))
        (суперечність-запереченій-голові-правила all-rules all-rules)))
      ((атом? remaining) (як-є ()))
      (так
       ((функція (opposite)
          ((функція (proofs)
             (за-умовою
               ((порожній? proofs)
                (виявити-суперечність-у-групі-порад clauses (решта remaining) all-rules))
               (так
                (список (перше remaining) opposite (перше proofs)))))
           (міркувати opposite all-rules)))
        (отримати-протилежну-голову-твердження-знання (перше (перше remaining))))))))

; Ратифікований D4:1000 = CAR(CAR), D4:0110 = CDR(CAR).
; Точна бітність та однобітний негатив: tests/semantic/knowledge-d4-selectors-*.bits.
(визначити knowledge-package-field
  (функція (name package)
    (за-умовою
      ((атом? package) (як-є ()))
      ((тотожне? name (перше-першого package)) (решта-першого package))
      (так (отримати-поле-пакета-знань name (решта package))))))

; Історичний пакет знань 0.1 відновлений з lib/knowledge.lisp @ 327b51ca1f.
; Дані пакета не eval. Назви полів належать цитованим даним, не D7-функціям.
; Умови: пряма D1-бітність; D4:1000 CAAR; D3:111 CONS; D4:1110 LIST.
; Ні SID8-псевдонімів, ні D10-ратифікації чи нових примітивів.
(визначити *knowledge-package-version* (як-є (ні 1)))

(визначити knowledge-package-entries-valid?
  (функція (entries)
    (за-умовою
      ((порожній? entries) так)
      ((атом? entries) ні)
      ((атом? (перше entries)) ні)
      ((knowledge-symbol? (перше-першого entries))
       (записи-пакета-знань-коректні? (решта entries)))
      (так ні))))

(визначити make-knowledge-package
  (функція (module-name clauses)
    (список (сполучити (як-є format) (як-є my-lisp-knowledge))
          (сполучити (як-є version) *knowledge-package-version*)
          (сполучити (як-є module) module-name)
          (сполучити (як-є clauses) clauses))))

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

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити відкликати-факт retract-fact)
(визначити виконати-багатоваріантне-виведення run-multi)
(визначити символ? symbol?)
