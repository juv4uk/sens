;; An immutable world is ordinary my-lisp data:
;;   (world parent newest-first-knowledge-journal metadata)
;; Every transition returns a new value. The previous world remains its parent,
;; and the new journal shares the complete old journal as its cons tail. No
;; mutable host object or Rust primitive is needed.
;;
;; Незмінний світ — це звичайні дані my-lisp:
;;   (world батько журнал-знань-від-нових-до-старих метадані)
;; Кожен перехід повертає нове значення. Попередній світ лишається батьком,
;; а новий журнал структурно ділить увесь старий журнал як хвіст cons. Жодного
;; мутабельного об'єкта хоста чи нового Rust-примітива не потрібно.
;;
;; Eine unveränderliche Welt besteht aus gewöhnlichen my-lisp-Daten:
;;   (world vorgänger wissenjournal-neueste-zuerst metadaten)
;; Jeder Übergang liefert einen neuen Wert. Die vorige Welt bleibt ihr
;; Vorgänger, und das neue Journal teilt das vollständige alte Journal als
;; Cons-Ende. Kein veränderliches Hostobjekt und kein Rust-Primitiv ist nötig.

(визначити створити-світ
  (функція (parent journal metadata)
    (список (як-є world) parent journal metadata)))

(визначити порожній-світ
  (функція ()
    (створити-світ (як-є ()) (як-є ()) (як-є ()))))

(визначити world?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      ((тотожне? (перше value) (як-є world))
       (за-умовою
         ; Exact shape: (world parent journal metadata).
         ; D3 ATOM/CDR tests required tails; D4 NULL rejects an extra field.
         ; No D6 LENGTH, numeric arity literal, or host-side list checker.
         ((атом? (решта value)) ні)
         ((атом? (решта (решта value))) ні)
         ((атом? (решта (решта (решта value)))) ні)
         ((порожній? (решта (решта (решта (решта value))))) (атом? ()))
         (так ні)))
      (так ні))))

(визначити світ-батько (функція (world) (друге world)))
(визначити світ-журнал (функція (world) (третє world)))
; D6:100111 CADDDR has no admitted evaluator mechanism; derive the
; same fourth-field projection as exact D5:10011 CADDR after D3:011 CDR.
(визначити світ-метадані (функція (world) (третє (решта world))))

;; Events intentionally have the same data shape as `lib/knowledge.lisp`'s
;; journal, so a later migration can reuse packages and projections unchanged.
;; Події навмисно мають ту саму форму, що й журнал `lib/knowledge.lisp`.
;; Ereignisse haben absichtlich dieselbe Form wie in `lib/knowledge.lisp`.
(визначити світ-запис
  (функція (world event)
    (створити-світ world
                (сполучити event (світ-журнал world))
                (світ-метадані world))))

(визначити світ-повідомити
  (функція (world module-name clause)
    (світ-запис world (список (як-є tell) module-name clause))))

(визначити світ-відкликати
  (функція (world module-name clause)
    (світ-запис world (список (як-є retract) module-name clause))))

; D6 FILTER (101001) has no admitted evaluator mechanism. Select a
; module's event records directly by exact D3 atom/pair and D3 EQ on the
; atomic module-name field, preserving the original event order.
(визначити внутрішні-події-модуля
  (функція (module-name events)
    (за-умовою
      ((порожній? events) (як-є ()))
      ((атом? events) (як-є ()))
      ((тотожне? (друге (перше events)) module-name)
       (сполучити (перше events) (внутрішні-події-модуля module-name (решта events))))
      (так (внутрішні-події-модуля module-name (решта events))))))

(визначити world-module-events
  (функція (world module-name)
    (внутрішні-події-модуля module-name (світ-журнал world))))

; Retract the first structurally equal clause; both atoms and nested
; pairs are compared with the locally-derived exact D1 equality law.
(визначити world-remove-first
  (функція (value values)
    (за-умовою
      ((порожній? values) (як-є ()))
      ((атом? values) (як-є ()))
      ((внутрішня-рівність-версій value (перше values)) (решта values))
      (так (сполучити (перше values) (world-remove-first value (решта values)))))))

(визначити world-apply-event
  (функція (clauses event)
    (за-умовою
      ((тотожне? (перше event) (як-є tell)) (сполучити (третє event) clauses))
      ((тотожне? (перше event) (як-є retract))
       (world-remove-first (третє event) clauses))
      (так clauses))))

; D4 NOT of the D3 ATOM predicate: a module is known only when its
; event stream is a nonempty pair. D3 CONS cannot be a one-argument NOT.
(визначити world-module-known?
  (функція (world module-name)
    (хибне? (атом? (світ-модуль-події world module-name)))))

(визначити world-module-missing?
  (функція (world module-name)
    (атом? (світ-модуль-події world module-name))))

; D5 REVERSE and D6 REDUCE are ratified names but cannot be presumed
; callable; derive the chronological event fold from D3 list structure.
(визначити внутрішній-зворот-подій
  (функція (events acc)
    (за-умовою
      ((порожній? events) acc)
      ((атом? events) acc)
      (так (внутрішній-зворот-подій (решта events) (сполучити (перше events) acc))))))

(визначити внутрішнє-згортання-подій
  (функція (events clauses)
    (за-умовою
      ((порожній? events) clauses)
      ((атом? events) clauses)
      (так (внутрішнє-згортання-подій
                  (решта events)
                  (world-apply-event clauses (перше events)))))))

(визначити world-clauses
  (функція (world module-name)
    (внутрішнє-згортання-подій
      (внутрішній-зворот-подій (світ-модуль-події world module-name) (як-є ()))
      (як-є ()))))

;; Pure reasoning adapters: the answer depends only on the explicit world,
;; module, and goal. They deliberately do not inspect `*knowledge-journal*`.
;; Чисті reasoning-адаптери: відповідь залежить лише від явно переданих світу,
;; модуля й цілі; глобальний `*knowledge-journal*` вони не читають.
;; Reine Schlussfolgerungsadapter: Die Antwort hängt nur von der expliziten
;; Welt, dem Modul und dem Ziel ab; `*knowledge-journal*` wird nicht gelesen.
(визначити reason-in-world
  (функція (world module-name goal)
    (за-умовою
      ((світ-модуль-відомий? world module-name)
       (міркувати goal (світ-клаузи world module-name)))
      ((world-module-missing? world module-name)
       (як-є Module-not-found)))))

(визначити forward-in-world
  (функція (world module-name)
    (за-умовою
      ((світ-модуль-відомий? world module-name)
       (виконати-багатоваріантне-виведення (світ-клаузи world module-name) (як-є ())))
      ((world-module-missing? world module-name)
       (як-є Module-not-found)))))

; Derived D1 symbol predicate for world module names. This is a Lisp
; law over ATOM/NULL/EQ and exact D8 write+string-to-symbol mechanisms,
; not a native admission of the unrelated D9:110101100 coordinate.
(визначити внутрішній-символ?
  (функція (value)
    (за-умовою
      ((порожній? value) (порожній? (як-є (ні))))
      ((хибне? (атом? value)) (порожній? (як-є (ні))))
      ((тотожне? value (текст-у-символ (значення-у-текст value))) (порожній? (як-є ())))
      (так (порожній? (як-є (ні)))))))

(визначити advice-decision-in-world
  (функція (world module-name clause)
    (за-умовою
      ((хибне? (внутрішній-символ? module-name))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-module)) (список (як-є input) clause)))
      ((тотожне? (клауза-бази-знань-коректна? clause) (як-є ()))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-clause)) (список (як-є input) clause)))
      (так
       (нехай-похідне ((opposite (отримати-протилежну-голову-твердження-знання (перше clause))))
         (нехай-похідне ((proofs (за-умовою
                         ((світ-модуль-відомий? world module-name)
                          (міркувати-у-світ world module-name opposite))
                         )))
           (за-умовою
             
             ((атом? proofs)  (список (як-є accepted)
                    (список (як-є module) module-name)
                    (список (як-є knowledge) clause)))
             (так
              (список (як-є conflict)
                    (список (як-є new) clause)
                    (список (як-є existing) opposite)
                    (список (як-є proof) (перше proofs)))))))))))

(визначити advise-world
  (функція (world module-name clause)
    (нехай-похідне ((decision (порада-рішення-у-світ world module-name clause)))
      (за-умовою
        ((тотожне? (перше decision) (як-є accepted))
         (список decision (світ-повідомити world module-name clause)))
        (так (список decision world))))))

;; The batch form creates exactly one child world after the whole proposed
;; knowledge set validates and proves conflict-free. Proposed rules can support
;; or contradict one another during the check; no prefix can leak on failure.
;; Пакетна форма створює рівно один дочірній світ лише після validation усього
;; набору й перевірки конфліктів; жоден префікс не просочується при помилці.
;; Die Stapelform erzeugt genau eine Kindwelt erst nach vollständiger Prüfung;
;; bei einem Fehler kann kein Präfix des Pakets durchsickern.
(визначити advice-all-decision-in-world
  (функція (world module-name clauses)
    (за-умовою
      ((хибне? (внутрішній-символ? module-name))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-module)) (список (як-є input) clauses)))
      
      ((атом? clauses)  (список (як-є rejected) (список (як-є reason) (як-є invalid-batch)) (список (як-є input) clauses)))
      ((тотожне? (правильно-структурований-список-знань? clauses) (як-є ()))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-batch)) (список (як-є input) clauses)))
      ((тотожне? (клаузи-бази-знань-коректні? clauses) (як-є ()))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-clause)) (список (як-є input) clauses)))
      (так
       (нехай-похідне ((existing (за-умовою
                         ((світ-модуль-відомий? world module-name)
                          (світ-клаузи world module-name))
                         )))
         (нехай-похідне ((conflict (виявити-суперечність-у-групі-порад
                           clauses clauses (приєднати clauses existing))))
           (за-умовою
             
             ((атом? conflict)  (список (як-є accepted)
                    (список (як-є module) module-name)
                    (список (як-є knowledge) clauses)))
             (так
              (список (як-є conflict)
                    (список (як-є new) (перше conflict))
                    (список (як-є existing) (друге conflict))
                    (список (як-є proof) (третє conflict)))))))))))

(визначити world-tell-all
  (функція (world module-name clauses)
    (створити-світ world
                (приєднати (перетворити-клаузи-на-події-повідомлення module-name clauses)
                        (світ-журнал world))
                (світ-метадані world))))

;; Once `lib/world.lisp` is loaded, the legacy `defmodule` surface becomes a
;; thin compatibility wrapper over the explicit World transition. It rebuilds
;; only the legacy journal binding from the returned world, so existing
;; `reason-in`/`forward-in` callers keep exactly their old contract while the
;; write semantics now have one implementation: `world-tell-all`. The wrapper
;; can disappear after the remaining global writers migrate.
;;
;; Після завантаження `lib/world.lisp` старий `defmodule` стає тонкою сумісною
;; обгорткою над явним переходом World. Із поверненого світу він перевизначає
;; лише старий journal-binding: чинні `reason-in`/`forward-in` не змінюють
;; контракт, а семантика запису вже має одну реалізацію — `world-tell-all`.
;; Обгортку можна буде прибрати після міграції решти глобальних writer-ів.
;;
;; Sobald `lib/world.lisp` geladen ist, wird die alte `defmodule`-Oberfläche zu
;; einer dünnen Kompatibilitätshülle um den expliziten World-Übergang. Aus der
;; gelieferten Welt bindet sie nur das alte Journal neu; bestehende
;; `reason-in`/`forward-in`-Aufrufer behalten ihren Vertrag, während
;; `world-tell-all` die einzige Schreibsemantik liefert. Nach der Migration der
;; übrigen globalen Writer kann diese Hülle entfallen.
(визначити defmodule
  (make-macro
    (функція (name rules)
  (список (як-є def) (як-є *knowledge-journal*)
        (список (як-є світ-журнал)
              (список (як-є світ-повідомити-всі)
                    (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
                    (список (як-є quote) name)
                    rules))))))

;; The other two legacy journal macros follow the same bridge. `tell-knowledge`
;; deliberately keeps its established pre-write conflict check and delegates
;; only the accepted transition; `retract-knowledge` remains unconditional
;; because removing knowledge cannot introduce a contradiction. Both rebuild
;; the compatibility journal from a returned immutable World.
;;
;; Інші два legacy journal-макроси переходять тим самим мостом.
;; `tell-knowledge` зберігає чинну перевірку конфлікту перед записом і делегує
;; лише прийнятий перехід; `retract-knowledge` лишається безумовним, бо
;; вилучення знання не створює суперечності. Обидва відновлюють compatibility-
;; журнал із поверненого незмінного World.
;;
;; Die beiden anderen alten Journal-Makros nutzen dieselbe Brücke.
;; `tell-knowledge` behält seine Konfliktprüfung vor dem Schreiben und
;; delegiert nur den akzeptierten Übergang; `retract-knowledge` bleibt
;; bedingungslos, weil Wissensentzug keinen Widerspruch erzeugen kann. Beide
;; gewinnen das Kompatibilitätsjournal aus einer unveränderlichen World zurück.
(визначити tell-knowledge
  (make-macro
    (функція (module-name rules)
  (список (як-є cond)
        (список (список (як-є check-conflict) (список (як-є quote) module-name) rules)
              (список (як-є quote) (як-є Conflict-detected)))
        (список (як-є так)
              (список (як-є def) (як-є *knowledge-journal*)
                    (список (як-є світ-журнал)
                          (список (як-є світ-повідомити-всі)
                                (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
                                (список (як-є quote) module-name)
                                rules))))))))

(визначити retract-knowledge
  (make-macro
    (функція (module-name clause)
  (список (як-є def) (як-є *knowledge-journal*)
        (список (як-є світ-журнал)
              (список (як-є world-retract)
                    (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
                    (список (як-є quote) module-name)
                    clause))))))

(визначити advise-all-world
  (функція (world module-name clauses)
    (нехай-похідне ((decision (порада-всі-рішення-у-світ world module-name clauses)))
      (за-умовою
        ((тотожне? (перше decision) (як-є accepted))
         (список decision (світ-повідомити-всі world module-name clauses)))
        (так (список decision world))))))

;; A guarded compatibility transition must be evaluated exactly once. `let`
;; cannot hold it because `def` would then update a disposable lambda frame, so
;; this expansion uses one explicit top-level scratch binding. The argument and
;; pure World transition run once; only accepted results rebind the journal.
;; Guarded compatibility-перехід обчислюється рівно раз. `let` не підходить, бо
;; `def` оновив би тимчасовий lambda-frame, тому expansion має одне явне
;; top-level scratch binding. Аргумент і World-перехід виконуються один раз.
;; Ein geschützter Kompatibilitätsübergang wird genau einmal ausgewertet. `let`
;; eignet sich nicht, da `def` sonst einen temporären Lambda-Frame ändert; diese
;; Expansion nutzt daher eine ausdrückliche Top-Level-Zwischenbindung.
; Чинне похідне SENS-правило: теги рішення порівнюються тільки
; точним D3:101 EQ після D4:1000 CAAR. Макрос генерує виклик за назвою,
; а не цитує двійкові коди як десяткові числа і не змінює граматику.
; Guard у згенерованому AST має бути цитованою D1-тотожністю:
; голий #d1:1 тут передчасно обчислюється, а тоді стає числом 1 при reparse.
(визначити внутрішній-прийнято-перехід?
  (функція (transition)
    (тотожне? (перше-першого transition) (як-є accepted))))

; Тільки похідний SENS-селектор. D3:100 CAR витягає рішення
; з (decision world); числовий 00000101 не може бути викликом CAR.
(визначити внутрішнє-рішення-переходу
  (функція (transition)
    (перше transition)))

(визначити legacy-world-transition-expansion
  (функція (transition)
    (список (як-є second)
          (список (як-є list)
                (список (як-є def) (як-є *legacy-knowledge-transition*) transition)
                (список (як-є cond)
                      (список
                        ; Generate a SENS-defined D1 predicate call. Its body
                        ; performs exact D3 EQ / D4 CAAR, not a legacy W8
                        ; equality producing a structural list (1).
                        (список (як-є внутрішній-прийнято-перехід?)
                              (як-є *legacy-knowledge-transition*))
                        (список (як-є second)
                              (список (як-є list)
                                    (список (як-є def) (як-є *knowledge-journal*)
                                          (список (як-є світ-журнал)
                                                (список (як-є second)
                                                      (як-є *legacy-knowledge-transition*))))
                                    (список (як-є внутрішнє-рішення-переходу) (як-є *legacy-knowledge-transition*)))))
                      (список (як-є так)
                            (список (як-є внутрішнє-рішення-переходу) (як-є *legacy-knowledge-transition*))))))))

(визначити advise
  (make-macro
    (функція (module-name clause)
  (legacy-world-transition-expansion
    (список (як-є advise-world)
          (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
          (список (як-є quote) module-name)
          clause)))))

(визначити advise-all
  (make-macro
    (функція (module-name clauses)
  (legacy-world-transition-expansion
    (список (як-є порадити-всі-світ)
          (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
          (список (як-є quote) module-name)
          clauses)))))

;; World interchange reuses the established, versioned `my-lisp-knowledge`
;; envelope. Export reads one explicit snapshot. Import validates the envelope
;; as data and then delegates the only possible transition to
;; `advise-all-world`; received data is never evaluated as code.
;; World-обмін перевикористовує чинну версіоновану оболонку
;; `my-lisp-knowledge`. Експорт читає явний snapshot, імпорт передає єдиний
;; можливий перехід в `advise-all-world`; отримані дані ніколи не eval-код.
;; Der World-Austausch nutzt die bestehende versionierte Hülle
;; `my-lisp-knowledge`. Export liest einen expliziten Schnappschuss, Import
;; delegiert den einzigen Übergang an `advise-all-world`; Daten werden nie evaluiert.
(визначити make-world-knowledge-package
  (функція (world module-name)
    (за-умовою
      ((хибне? (внутрішній-символ? module-name))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-module)) (список (як-є input) module-name)))
      ((world-module-missing? world module-name)
       (список (як-є rejected) (список (як-є reason) (як-є Module-not-found)) (список (як-є input) module-name)))
      ((світ-модуль-відомий? world module-name)
       (нехай-похідне ((clauses (світ-клаузи world module-name)))
         (за-умовою
           
           ((атом? clauses)  (список (як-є rejected) (список (як-є reason) (як-є invalid-batch)) (список (як-є input) clauses)))
           (так (створити-пакет-структурованих-знань module-name clauses))))))))

; The knowledge package version is structured data (0 1), not an
; atom. Compare recursively with exact D1 results, never W8 EQUAL on pairs.
(визначити внутрішня-рівність-версій
  (функція (left right)
    (за-умовою
      ((порожній? left) (порожній? right))
      ((порожній? right) (порожній? (як-є (ні))))
      ((атом? left)
       (за-умовою
         ((атом? right) (тотожне? left right))
         (так (порожній? (як-є (ні))))))
      ((атом? right) (порожній? (як-є (ні))))
      ((внутрішня-рівність-версій (перше left) (перше right))
       (внутрішня-рівність-версій (решта left) (решта right)))
      (так (порожній? (як-є (ні)))))))

(визначити import-knowledge-package-world
  (функція (world package)
    (за-умовою
      
      ((атом? package)  (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) package))
             world))
      ((хибне? (правильно-структурований-список-знань? package))
       (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) package))
             world))
      ((хибне? (записи-пакета-знань-коректні? package))
       (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) package))
             world))
      ((тотожне? (отримати-поле-пакета-знань (як-є format) package) (як-є my-lisp-knowledge))
       (за-умовою
         ((внутрішня-рівність-версій (отримати-поле-пакета-знань (як-є version) package)
                  *knowledge-package-version*)
          (порадити-всі-світ world
                            (отримати-поле-пакета-знань (як-є module) package)
                            (отримати-поле-пакета-знань (як-є clauses) package)))
         (так
          (список (список (як-є rejected)
                      (список (як-є reason) (як-є unsupported-version))
                      (список (як-є version)
                            (отримати-поле-пакета-знань (як-є version) package)))
                world))))
      (так
       (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) package))
             world)))))

;; Package import completes the writer migration. The legacy macro delegates
;; validation, version handling, conflict detection, and the atomic transition
;; to the data-only World importer; only an accepted result rebinds the journal.
;; Імпорт пакетів завершує міграцію writer-ів: validation, version handling,
;; конфлікти й атомарний перехід делеговано data-only World-імпортеру; журнал
;; перевизначається лише для accepted.
;; Der Paketimport schließt die Writer-Migration ab: Prüfung, Versionierung,
;; Konflikte und atomarer Übergang liegen beim datenreinen World-Importer; nur
;; ein akzeptiertes Ergebnis bindet das Journal neu.
(визначити import-knowledge-package
  (make-macro
    (функція (package)
  (legacy-world-transition-expansion
    (список (як-є import-knowledge-package-world)
          (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
          package)))))

;; History navigation is derived from parent links, not timestamps. Depth is
;; absolute from the root (`empty-world` = 0). `world-diff from to` returns the
;; chronological event list only when `from` is an ancestor of `to`; divergent
;; branches return `World-not-ancestor` until an explicit merge law exists.
;;
;; Навігація історією спирається на батьківські зв'язки, не timestamps. Глибина
;; абсолютна від кореня (`empty-world` = 0). `world-diff from to` повертає
;; хронологічні події лише для предка; різні гілки дають `World-not-ancestor`,
;; доки не визначено чесний закон merge.
;;
;; Geschichtsnavigation folgt Vorgängerlinks statt Zeitstempeln. Die Tiefe ist
;; absolut ab der Wurzel (`empty-world` = 0). `world-diff from to` liefert
;; chronologische Ereignisse nur für einen Vorfahren; getrennte Zweige ergeben
;; `World-not-ancestor`, bis ein ausdrückliches Merge-Gesetz definiert ist.
(визначити world-depth
  (функція (world)
    (за-умовою
      
      ((атом? (світ-батько world))  0)
      (так (додати 1 (світ-глибина (світ-батько world)))))))

(визначити world-at-depth-from
  (функція (world current-depth target-depth)
    (за-умовою
      ((тотожне? current-depth target-depth)  world)
      (так (як-є World-not-found))
      
      ((атом? (світ-батько world))  (як-є World-not-found))
      (так (отримати-світ-на-заданій-глибині-від-поточного (світ-батько world)
                              (відняти current-depth 1)
                              target-depth)))))

(визначити world-at-depth
  (функція (world target-depth)
    (за-умовою
      ((менше? target-depth 0)  (як-є World-not-found))
      (так (отримати-світ-на-заданій-глибині-від-поточного world (світ-глибина world) target-depth)))))

(визначити world-journal-prefix
  (функція (journal old-journal)
    (за-умовою
      ((внутрішня-рівність-версій journal old-journal) (як-є ()))
      
      ((атом? journal)  (як-є World-not-ancestor))
      (так
       (нехай-похідне ((rest (отримати-префікс-журналу-світу (решта journal) old-journal)))
         (за-умовою
           ((цей-світ-не-є-предком-іншого? rest) rest)
           (так (сполучити (перше journal) rest))))))))

(визначити world-not-ancestor?
  (функція (value)
    (за-умовою
      
      ((атом? value)  (тотожне? value (як-є World-not-ancestor)))
      )))

(визначити world-diff
  (функція (from to)
    (за-умовою
      ((внутрішня-рівність-версій from to) (як-є ()))
      
      ((атом? (світ-батько to))  (як-є World-not-ancestor))
      (так
       (нехай-похідне ((earlier (світ-різниця from (світ-батько to))))
         (за-умовою
           ((цей-світ-не-є-предком-іншого? earlier) earlier)
           (так
            (нехай-похідне ((transition
                    (отримати-префікс-журналу-світу
                      (світ-журнал to)
                      (світ-журнал (світ-батько to)))))
              (за-умовою
                ((цей-світ-не-є-предком-іншого? transition) transition)
                (так (приєднати earlier transition)))))))))))

;; Branch comparison stops before merge policy. First align both histories to
;; the same absolute depth, then walk parents together until their values are
;; equal. Since worlds are immutable values, structurally equal histories are
;; the same semantic world even if reconstructed independently from a package.
;; `world-branch-diff` exposes the common base plus both chronological deltas.
;;
;; Порівняння гілок зупиняється до merge-policy. Історії вирівнюються за
;; абсолютною глибиною й разом ідуть до рівного предка. Для immutable-значень
;; структурно рівні історії — той самий семантичний світ. `world-branch-diff`
;; показує спільну базу та обидві хронологічні дельти.
;;
;; Der Zweigvergleich endet vor einer Merge-Policy. Beide Geschichten werden
;; auf gleiche Tiefe gebracht und gemeinsam bis zum gleichen Vorfahren verfolgt.
;; Bei unveränderlichen Werten sind strukturell gleiche Geschichten dieselbe
;; semantische Welt. `world-branch-diff` zeigt Basis und beide Zeitdeltas.
(визначити world-climb-to-depth
  (функція (world current-depth target-depth)
    (за-умовою
      ((тотожне? current-depth target-depth)  world)
      (так (піднятись-ланцюгом-світу-до-заданої-глибини (світ-батько world)
                               (відняти current-depth 1)
                               target-depth)))))

(визначити world-common-ancestor-aligned
  (функція (left right)
    (за-умовою
      ((внутрішня-рівність-версій left right) left)
      ((атом? left) (як-є World-no-common-ancestor))
      ((атом? right) (як-є World-no-common-ancestor))
      ((атом? (світ-батько left)) (як-є World-no-common-ancestor))
      ((атом? (світ-батько right)) (як-є World-no-common-ancestor))
      (так
       (вирівняний-спільний-предок-двох-світів (світ-батько left)
                                      (світ-батько right))))))

; An ancestor is found by walking immutable parents. Its SENS verdict
; is a D1 predicate, never a numeric depth or an historical W8 EQ value.
(визначити внутрішній-предок-світу?
  (функція (candidate world)
    (за-умовою
      ((атом? world) ні)
      ((внутрішня-рівність-версій candidate world) так)
      ((атом? (світ-батько world)) ні)
      (так
       (внутрішній-предок-світу? candidate (світ-батько world))))))

; The first ancestor of left occurring in right's ancestry is the deepest
; common world. This is pure SENS structure, independent of D24+ arithmetic.
(визначити world-common-ancestor
  (функція (left right)
    (за-умовою
      ((атом? left) (як-є World-no-common-ancestor))
      ((атом? right) (як-є World-no-common-ancestor))
      ((внутрішній-предок-світу? left right) left)
      ((атом? (світ-батько left)) (як-є World-no-common-ancestor))
      (так (світ-спільний-предок (світ-батько left) right)))))

(визначити world-no-common-ancestor?
  (функція (value)
    (за-умовою
      ((атом? value) (тотожне? value (як-є World-no-common-ancestor)))
      (так ні))))

(визначити world-branch-diff
  (функція (left right)
    (нехай-похідне ((base (світ-спільний-предок left right)))
      (за-умовою
        ((світи-не-мають-спільного-предка? base) base)
        (так
         (список (список (як-є base) base)
               (список (як-є left) (світ-різниця base left))
               (список (як-є right) (світ-різниця base right))))))))

;; Content identity starts with a canonical address, not a premature hash
;; primitive. `write-to-string` is deterministic and read-back-safe, so equal
;; knowledge has exactly the same address on every conforming implementation.
;; A world's address covers its complete event journal plus metadata; parent is
;; omitted because the journal already contains the whole history, avoiding a
;; recursively duplicated serialization. This is an exact key, not a fixed-size
;; cryptographic digest. A future SHA layer may hash this key without changing
;; what identity means.
;;
;; Content-ідентичність починається з канонічної адреси, не передчасного hash-
;; примітива. `write-to-string` детермінований і read-back-safe, тому рівне
;; знання має ту саму адресу в кожній conforming-реалізації. Адреса світу
;; охоплює весь журнал подій і metadata; parent не дублюється рекурсивно.
;; Це точний ключ, не криптографічний digest; майбутній SHA лише стисне ключ.
;;
;; Inhaltsidentität beginnt mit einer kanonischen Adresse statt einem
;; voreiligen Hash-Primitiv. `write-to-string` ist deterministisch und
;; rücklesbar, daher hat gleiches Wissen in jeder konformen Implementierung
;; dieselbe Adresse. Die Weltadresse umfasst Journal und Metadaten; der
;; Vorgänger wird nicht rekursiv dupliziert. Dies ist ein exakter Schlüssel,
;; kein kryptographischer Digest; ein späteres SHA kann diesen Schlüssel kürzen.
(визначити знання-вміст-адреса
  (функція (knowledge)
    (значення-у-текст knowledge)))

(визначити світ-адреса-вміст
  (функція (world)
    (список (як-є world-history)
            (світ-журнал world)
            (світ-метадані world))))

(визначити світ-вміст-адреса
  (функція (world)
    (знання-вміст-адреса (світ-адреса-вміст world))))

; opt-in повна укр-поверхня: первинні D9-визначення в цьому блоці названі укр.
(визначити порадити-всі-світ advise-all-world)
(визначити knowledge-content-address знання-вміст-адреса)
(визначити make-world створити-світ)
(визначити world-address-content світ-адреса-вміст)
(визначити отримати-світ-на-заданій-глибині-від-поточного world-at-depth-from)
(визначити світ-клаузи world-clauses)
(визначити піднятись-ланцюгом-світу-до-заданої-глибини world-climb-to-depth)
(визначити світ-спільний-предок world-common-ancestor)
(визначити вирівняний-спільний-предок-двох-світів world-common-ancestor-aligned)
(визначити світ-глибина world-depth)
(визначити світ-різниця world-diff)
(визначити world-journal світ-журнал)
(визначити world-metadata світ-метадані)
(визначити світ-модуль-події world-module-events)
(визначити світ-модуль-відомий? world-module-known?)
(визначити світи-не-мають-спільного-предка? world-no-common-ancestor?)
(визначити цей-світ-не-є-предком-іншого? world-not-ancestor?)
(визначити world-parent світ-батько)
(визначити world-record світ-запис)
(визначити world-tell світ-повідомити)
(визначити світ-повідомити-всі world-tell-all)

(визначити empty-world порожній-світ)
(визначити world-retract світ-відкликати)
(визначити world-content-address світ-вміст-адреса)
; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити перетворити-клаузи-на-події-повідомлення clauses->tell-events)
(визначити клауза-бази-знань-коректна? knowledge-clause-valid?)
(визначити клаузи-бази-знань-коректні? knowledge-clauses-valid?)
(визначити записи-пакета-знань-коректні? knowledge-package-entries-valid?)
(визначити отримати-поле-пакета-знань knowledge-package-field)
(визначити правильно-структурований-список-знань? knowledge-proper-list?)
(визначити створити-пакет-структурованих-знань make-knowledge-package)
(визначити виконати-багатоваріантне-виведення run-multi)
