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

(00001001 make-world
  (00001000 (parent journal metadata)
    (list (00000001 world) parent journal metadata)))

(00001001 empty-world
  (00001000 ()
    (make-world (00000001 ()) (00000001 ()) (00000001 ()))))

(00001001 world?
  (00001000 (value)
    (00000111
      ((00000010 value) (00000001 ()))
      ((00000011 (00000101 value) (00000001 world)) t)
      (t (00000001 ())))))

(00001001 world-parent (00001000 (world) (second world)))
(00001001 world-journal (00001000 (world) (third world)))
(00001001 world-metadata (00001000 (world) (fourth world)))

;; Events intentionally have the same data shape as `lib/knowledge.lisp`'s
;; journal, so a later migration can reuse packages and projections unchanged.
;; Події навмисно мають ту саму форму, що й журнал `lib/knowledge.lisp`.
;; Ereignisse haben absichtlich dieselbe Form wie in `lib/knowledge.lisp`.
(00001001 world-record
  (00001000 (world event)
    (make-world world
                (00000100 event (world-journal world))
                (world-metadata world))))

(00001001 world-tell
  (00001000 (world module-name clause)
    (world-record world (list (00000001 tell) module-name clause))))

(00001001 world-retract
  (00001000 (world module-name clause)
    (world-record world (list (00000001 retract) module-name clause))))

(00001001 world-module-events
  (00001000 (world module-name)
    (filter (00001000 (event) (equal? (second event) module-name))
            (world-journal world))))

(00001001 world-remove-first
  (00001000 (value values)
    (00000111
      ((00000010 values) (00000001 ()))
      ((equal? value (00000101 values)) (00000110 values))
      (t (00000100 (00000101 values) (world-remove-first value (00000110 values)))))))

(00001001 world-apply-event
  (00001000 (clauses event)
    (00000111
      ((00000011 (00000101 event) (00000001 tell)) (00000100 (third event) clauses))
      ((00000011 (00000101 event) (00000001 retract))
       (world-remove-first (third event) clauses))
      (t clauses))))

(00001001 world-module-known?
  (00001000 (world module-name)
    (00000111
      ((00000010 (world-module-events world module-name)) (00000001 ()))
      (t t))))

(00001001 world-clauses
  (00001000 (world module-name)
    (reduce world-apply-event (00000001 ())
            (reverse (world-module-events world module-name)))))

;; Pure reasoning adapters: the answer depends only on the explicit world,
;; module, and goal. They deliberately do not inspect `*knowledge-journal*`.
;; Чисті reasoning-адаптери: відповідь залежить лише від явно переданих світу,
;; модуля й цілі; глобальний `*knowledge-journal*` вони не читають.
;; Reine Schlussfolgerungsadapter: Die Antwort hängt nur von der expliziten
;; Welt, dem Modul und dem Ziel ab; `*knowledge-journal*` wird nicht gelesen.
(00001001 reason-in-world
  (00001000 (world module-name goal)
    (00000111
      ((world-module-known? world module-name)
       (reason goal (world-clauses world module-name)))
      (t (00000001 Module-not-found)))))

(00001001 forward-in-world
  (00001000 (world module-name)
    (00000111
      ((world-module-known? world module-name)
       (run-multi (world-clauses world module-name) (00000001 ())))
      (t (00000001 Module-not-found)))))

;; `advise-world` keeps the established Advice Taker decision vocabulary but
;; makes the state transition explicit. Its result is always `(decision world)`:
;; accepted input carries a newly extended world; rejected or conflicting input
;; carries the exact original world. Validation helpers are shared with
;; `lib/knowledge.lisp`, so the global convenience API and this pure API cannot
;; silently develop different clause languages.
;;
;; `advise-world` зберігає чинний словник рішень Advice Taker, але робить
;; перехід стану явним. Результат завжди `(рішення світ)`: прийнятий ввід несе
;; новий розширений світ, відхилений або конфліктний — точно початковий світ.
;; Валідатори спільні з `lib/knowledge.lisp`, тому обидва API не розійдуться.
;;
;; `advise-world` behält das bestehende Entscheidungsvokabular des Advice
;; Takers bei, macht den Zustandsübergang jedoch explizit. Das Ergebnis ist
;; immer `(entscheidung welt)`: Akzeptierte Eingabe enthält eine neue Welt,
;; abgelehnte oder widersprüchliche Eingabe exakt die ursprüngliche Welt.
(00001001 advice-decision-in-world
  (00001000 (world module-name clause)
    (00000111
      ((00000011 (symbol? module-name) (00000001 ()))
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-module)) (list (00000001 input) clause)))
      ((00000011 (knowledge-clause-valid? clause) (00000001 ()))
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-clause)) (list (00000001 input) clause)))
      (t
       (let ((opposite (opposite-knowledge-head (00000101 clause))))
         (let ((proofs (00000111
                         ((world-module-known? world module-name)
                          (reason-in-world world module-name opposite))
                         (t (00000001 ())))))
           (00000111
             ((00000010 proofs)
              (list (00000001 accepted)
                    (list (00000001 module) module-name)
                    (list (00000001 knowledge) clause)))
             (t
              (list (00000001 conflict)
                    (list (00000001 new) clause)
                    (list (00000001 existing) opposite)
                    (list (00000001 proof) (00000101 proofs)))))))))))

(00001001 advise-world
  (00001000 (world module-name clause)
    (let ((decision (advice-decision-in-world world module-name clause)))
      (00000111
        ((00000011 (00000101 decision) (00000001 accepted))
         (list decision (world-tell world module-name clause)))
        (t (list decision world))))))

;; The batch form creates exactly one child world after the whole proposed
;; knowledge set validates and proves conflict-free. Proposed rules can support
;; or contradict one another during the check; no prefix can leak on failure.
;; Пакетна форма створює рівно один дочірній світ лише після validation усього
;; набору й перевірки конфліктів; жоден префікс не просочується при помилці.
;; Die Stapelform erzeugt genau eine Kindwelt erst nach vollständiger Prüfung;
;; bei einem Fehler kann kein Präfix des Pakets durchsickern.
(00001001 advice-all-decision-in-world
  (00001000 (world module-name clauses)
    (00000111
      ((00000011 (symbol? module-name) (00000001 ()))
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-module)) (list (00000001 input) clauses)))
      ((00000010 clauses)
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-batch)) (list (00000001 input) clauses)))
      ((00000011 (knowledge-proper-list? clauses) (00000001 ()))
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-batch)) (list (00000001 input) clauses)))
      ((00000011 (knowledge-clauses-valid? clauses) (00000001 ()))
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-clause)) (list (00000001 input) clauses)))
      (t
       (let ((existing (00000111
                         ((world-module-known? world module-name)
                          (world-clauses world module-name))
                         (t (00000001 ())))))
         (let ((conflict (advice-batch-conflict
                           clauses clauses (append clauses existing))))
           (00000111
             ((00000010 conflict)
              (list (00000001 accepted)
                    (list (00000001 module) module-name)
                    (list (00000001 knowledge) clauses)))
             (t
              (list (00000001 conflict)
                    (list (00000001 new) (00000101 conflict))
                    (list (00000001 existing) (second conflict))
                    (list (00000001 proof) (third conflict)))))))))))

(00001001 world-tell-all
  (00001000 (world module-name clauses)
    (make-world world
                (append (clauses->tell-events module-name clauses)
                        (world-journal world))
                (world-metadata world))))

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
(defmacro defmodule (name rules)
  (list (00000001 def) (00000001 *knowledge-journal*)
        (list (00000001 world-journal)
              (list (00000001 world-tell-all)
                    (list (00000001 make-world) (00000001 ()) (00000001 *knowledge-journal*) (00000001 ()))
                    (list (00000001 quote) name)
                    rules))))

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
(defmacro tell-knowledge (module-name rules)
  (list (00000001 cond)
        (list (list (00000001 check-conflict) (list (00000001 quote) module-name) rules)
              (list (00000001 quote) (00000001 Conflict-detected)))
        (list (00000001 t)
              (list (00000001 def) (00000001 *knowledge-journal*)
                    (list (00000001 world-journal)
                          (list (00000001 world-tell-all)
                                (list (00000001 make-world) (00000001 ()) (00000001 *knowledge-journal*) (00000001 ()))
                                (list (00000001 quote) module-name)
                                rules))))))

(defmacro retract-knowledge (module-name clause)
  (list (00000001 def) (00000001 *knowledge-journal*)
        (list (00000001 world-journal)
              (list (00000001 world-retract)
                    (list (00000001 make-world) (00000001 ()) (00000001 *knowledge-journal*) (00000001 ()))
                    (list (00000001 quote) module-name)
                    clause))))

(00001001 advise-all-world
  (00001000 (world module-name clauses)
    (let ((decision (advice-all-decision-in-world world module-name clauses)))
      (00000111
        ((00000011 (00000101 decision) (00000001 accepted))
         (list decision (world-tell-all world module-name clauses)))
        (t (list decision world))))))

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
(00001001 legacy-world-transition-expansion
  (00001000 (transition)
    (list (00000001 second)
          (list (00000001 list)
                (list (00000001 def) (00000001 *legacy-knowledge-transition*) transition)
                (list (00000001 cond)
                      (list
                        (list (00000001 equal?)
                              (list (00000001 car)
                                    (list (00000001 car) (00000001 *legacy-knowledge-transition*)))
                              (list (00000001 quote) (00000001 accepted)))
                        (list (00000001 second)
                              (list (00000001 list)
                                    (list (00000001 def) (00000001 *knowledge-journal*)
                                          (list (00000001 world-journal)
                                                (list (00000001 second)
                                                      (00000001 *legacy-knowledge-transition*))))
                                    (list (00000001 car) (00000001 *legacy-knowledge-transition*)))))
                      (list (00000001 t)
                            (list (00000001 car) (00000001 *legacy-knowledge-transition*))))))))

(defmacro advise (module-name clause)
  (legacy-world-transition-expansion
    (list (00000001 advise-world)
          (list (00000001 make-world) (00000001 ()) (00000001 *knowledge-journal*) (00000001 ()))
          (list (00000001 quote) module-name)
          clause)))

(defmacro advise-all (module-name clauses)
  (legacy-world-transition-expansion
    (list (00000001 advise-all-world)
          (list (00000001 make-world) (00000001 ()) (00000001 *knowledge-journal*) (00000001 ()))
          (list (00000001 quote) module-name)
          clauses)))

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
(00001001 make-world-knowledge-package
  (00001000 (world module-name)
    (00000111
      ((00000011 (symbol? module-name) (00000001 ()))
       (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-module)) (list (00000001 input) module-name)))
      ((00000011 (world-module-known? world module-name) (00000001 ())) (00000001 Module-not-found))
      (t
       (let ((clauses (world-clauses world module-name)))
         (00000111
           ((00000010 clauses)
            (list (00000001 rejected) (list (00000001 reason) (00000001 invalid-batch)) (list (00000001 input) clauses)))
           (t (make-knowledge-package module-name clauses))))))))

(00001001 import-knowledge-package-world
  (00001000 (world package)
    (00000111
      ((00000010 package)
       (list (list (00000001 rejected)
                   (list (00000001 reason) (00000001 invalid-package))
                   (list (00000001 input) package))
             world))
      ((00000011 (knowledge-proper-list? package) (00000001 ()))
       (list (list (00000001 rejected)
                   (list (00000001 reason) (00000001 invalid-package))
                   (list (00000001 input) package))
             world))
      ((00000011 (knowledge-package-entries-valid? package) (00000001 ()))
       (list (list (00000001 rejected)
                   (list (00000001 reason) (00000001 invalid-package))
                   (list (00000001 input) package))
             world))
      ((00000011 (knowledge-package-field (00000001 format) package) (00000001 my-lisp-knowledge))
       (00000111
         ((equal? (knowledge-package-field (00000001 version) package)
                  *knowledge-package-version*)
          (advise-all-world world
                            (knowledge-package-field (00000001 module) package)
                            (knowledge-package-field (00000001 clauses) package)))
         (t
          (list (list (00000001 rejected)
                      (list (00000001 reason) (00000001 unsupported-version))
                      (list (00000001 version)
                            (knowledge-package-field (00000001 version) package)))
                world))))
      (t
       (list (list (00000001 rejected)
                   (list (00000001 reason) (00000001 invalid-package))
                   (list (00000001 input) package))
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
(defmacro import-knowledge-package (package)
  (legacy-world-transition-expansion
    (list (00000001 import-knowledge-package-world)
          (list (00000001 make-world) (00000001 ()) (00000001 *knowledge-journal*) (00000001 ()))
          package)))

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
(00001001 world-depth
  (00001000 (world)
    (00000111
      ((00000010 (world-parent world)) 0)
      (t (00001100 1 (world-depth (world-parent world)))))))

(00001001 world-at-depth-from
  (00001000 (world current-depth target-depth)
    (00000111
      ((= current-depth target-depth) 1 world)
      ((< current-depth target-depth) 1 (00000001 World-not-found))
      ((00000010 (world-parent world)) (00000001 World-not-found))
      (t (world-at-depth-from (world-parent world)
                              (00001101 current-depth 1)
                              target-depth)))))

(00001001 world-at-depth
  (00001000 (world target-depth)
    (00000111
      ((< target-depth 0) 1 (00000001 World-not-found))
      (t (world-at-depth-from world (world-depth world) target-depth)))))

(00001001 world-journal-prefix
  (00001000 (journal old-journal)
    (00000111
      ((equal? journal old-journal) (00000001 ()))
      ((00000010 journal) (00000001 World-not-ancestor))
      (t
       (let ((rest (world-journal-prefix (00000110 journal) old-journal)))
         (00000111
           ((world-not-ancestor? rest) rest)
           (t (00000100 (00000101 journal) rest))))))))

(00001001 world-not-ancestor?
  (00001000 (value)
    (00000111
      ((00000010 value) (00000011 value (00000001 World-not-ancestor)))
      (t (00000001 ())))))

(00001001 world-diff
  (00001000 (from to)
    (00000111
      ((equal? from to) (00000001 ()))
      ((00000010 (world-parent to)) (00000001 World-not-ancestor))
      (t
       (let ((earlier (world-diff from (world-parent to))))
         (00000111
           ((world-not-ancestor? earlier) earlier)
           (t
            (let ((transition
                    (world-journal-prefix
                      (world-journal to)
                      (world-journal (world-parent to)))))
              (00000111
                ((world-not-ancestor? transition) transition)
                (t (append earlier transition)))))))))))

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
(00001001 world-climb-to-depth
  (00001000 (world current-depth target-depth)
    (00000111
      ((= current-depth target-depth) 1 world)
      (t (world-climb-to-depth (world-parent world)
                               (00001101 current-depth 1)
                               target-depth)))))

(00001001 world-common-ancestor-aligned
  (00001000 (left right)
    (00000111
      ((equal? left right) left)
      ((00000010 (world-parent left)) (00000001 World-no-common-ancestor))
      ((00000010 (world-parent right)) (00000001 World-no-common-ancestor))
      (t (world-common-ancestor-aligned (world-parent left)
                                        (world-parent right))))))

(00001001 world-common-ancestor
  (00001000 (left right)
    (let ((left-depth (world-depth left))
          (right-depth (world-depth right)))
      (let ((target-depth (00000111
                            ((< left-depth right-depth) 1 left-depth)
                            (t right-depth))))
        (world-common-ancestor-aligned
          (world-climb-to-depth left left-depth target-depth)
          (world-climb-to-depth right right-depth target-depth))))))

(00001001 world-no-common-ancestor?
  (00001000 (value)
    (00000111
      ((00000010 value) (00000011 value (00000001 World-no-common-ancestor)))
      (t (00000001 ())))))

(00001001 world-branch-diff
  (00001000 (left right)
    (let ((base (world-common-ancestor left right)))
      (00000111
        ((world-no-common-ancestor? base) base)
        (t
         (list (list (00000001 base) base)
               (list (00000001 left) (world-diff base left))
               (list (00000001 right) (world-diff base right))))))))

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
(00001001 knowledge-content-address
  (00001000 (knowledge)
    (write-to-string knowledge)))

(00001001 world-address-content
  (00001000 (world)
    (list (00000001 world-history)
          (world-journal world)
          (world-metadata world))))

(00001001 world-content-address
  (00001000 (world)
    (knowledge-content-address (world-address-content world))))
