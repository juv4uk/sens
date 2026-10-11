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

(0011 make-world
  (0010 (parent journal metadata)
    (1110 (001 world) parent journal metadata)))

(0011 empty-world
  (0010 ()
    (make-world (001 ()) (001 ()) (001 ()))))

(0011 world?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((101 (100 value) (001 world)) t)
      )))

(0011 world-parent (0010 (world) (1001 world)))
(0011 world-journal (0010 (world) (10011 world)))
(0011 world-metadata (0010 (world) (100111 world)))

;; Events intentionally have the same data shape as `lib/knowledge.lisp`'s
;; journal, so a later migration can reuse packages and projections unchanged.
;; Події навмисно мають ту саму форму, що й журнал `lib/knowledge.lisp`.
;; Ereignisse haben absichtlich dieselbe Form wie in `lib/knowledge.lisp`.
(0011 world-record
  (0010 (world event)
    (make-world world
                (111 event (world-journal world))
                (world-metadata world))))

(0011 world-tell
  (0010 (world module-name clause)
    (world-record world (1110 (001 tell) module-name clause))))

(0011 world-retract
  (0010 (world module-name clause)
    (world-record world (1110 (001 retract) module-name clause))))

(0011 world-module-events
  (0010 (world module-name)
    (101001 (0010 (event) (11110111 (1001 event) module-name))
            (world-journal world))))

(0011 world-remove-first
  (0010 (value values)
    (110
      
      ((010 values)  (001 ()))
      ((11110111 value (100 values)) (011 values))
      ((11110111
        (11110111 value (100 values))
        (11110111 (001 d1-no-left) (001 d1-no-right)))
       (111 (100 values) (world-remove-first value (011 values)))))))

(0011 world-apply-event
  (0010 (clauses event)
    (110
      ((101 (100 event) (001 tell)) (111 (10011 event) clauses))
      ((101 (100 event) (001 retract))
       (world-remove-first (10011 event) clauses))
      ((11110111
        (101 (100 event) (001 retract))
        (11110111 (001 d1-no-left) (001 d1-no-right)))
       clauses))))

(0011 world-module-known?
  (0010 (world module-name)
    (111 (010 (world-module-events world module-name)))))

(0011 world-module-missing?
  (0010 (world module-name)
    (010 (world-module-events world module-name))))

(0011 world-clauses
  (0010 (world module-name)
    (101110 world-apply-event (001 ())
            (10100 (world-module-events world module-name)))))

;; Pure reasoning adapters: the answer depends only on the explicit world,
;; module, and goal. They deliberately do not inspect `*knowledge-journal*`.
;; Чисті reasoning-адаптери: відповідь залежить лише від явно переданих світу,
;; модуля й цілі; глобальний `*knowledge-journal*` вони не читають.
;; Reine Schlussfolgerungsadapter: Die Antwort hängt nur von der expliziten
;; Welt, dem Modul und dem Ziel ab; `*knowledge-journal*` wird nicht gelesen.
(0011 reason-in-world
  (0010 (world module-name goal)
    (110
      ((world-module-known? world module-name)
       (101001110 goal (world-clauses world module-name)))
      ((world-module-missing? world module-name)
       (001 Module-not-found)))))

(0011 forward-in-world
  (0010 (world module-name)
    (110
      ((world-module-known? world module-name)
       (run-multi (world-clauses world module-name) (001 ())))
      ((world-module-missing? world module-name)
       (001 Module-not-found)))))

(0011 advice-decision-in-world
  (0010 (world module-name clause)
    (110
      ((101 (110101100 module-name) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) clause)))
      ((101 (knowledge-clause-valid? clause) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clause)))
      ((010 ())
       (001000 ((opposite (opposite-knowledge-head (100 clause))))
         (001000 ((proofs (110
                         ((world-module-known? world module-name)
                          (reason-in-world world module-name opposite))
                         )))
           (110
             
             ((010 proofs)  (1110 (001 accepted)
                    (1110 (001 module) module-name)
                    (1110 (001 knowledge) clause)))
             ((010 ())
              (1110 (001 conflict)
                    (1110 (001 new) clause)
                    (1110 (001 existing) opposite)
                    (1110 (001 proof) (100 proofs)))))))))))

(0011 advise-world
  (0010 (world module-name clause)
    (001000 ((decision (advice-decision-in-world world module-name clause)))
      (110
        ((101 (100 decision) (001 accepted))
         (1110 decision (world-tell world module-name clause)))
        ((010 ()) (1110 decision world))))))

;; The batch form creates exactly one child world after the whole proposed
;; knowledge set validates and proves conflict-free. Proposed rules can support
;; or contradict one another during the check; no prefix can leak on failure.
;; Пакетна форма створює рівно один дочірній світ лише після validation усього
;; набору й перевірки конфліктів; жоден префікс не просочується при помилці.
;; Die Stapelform erzeugt genau eine Kindwelt erst nach vollständiger Prüfung;
;; bei einem Fehler kann kein Präfix des Pakets durchsickern.
(0011 advice-all-decision-in-world
  (0010 (world module-name clauses)
    (110
      ((101 (110101100 module-name) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) clauses)))
      
      ((010 clauses)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((101 (knowledge-proper-list? clauses) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
      ((101 (knowledge-clauses-valid? clauses) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-clause)) (1110 (001 input) clauses)))
      ((010 ())
       (001000 ((existing (110
                         ((world-module-known? world module-name)
                          (world-clauses world module-name))
                         )))
         (001000 ((conflict (advice-batch-conflict
                           clauses clauses (1111 clauses existing))))
           (110
             
             ((010 conflict)  (1110 (001 accepted)
                    (1110 (001 module) module-name)
                    (1110 (001 knowledge) clauses)))
             ((010 ())
              (1110 (001 conflict)
                    (1110 (001 new) (100 conflict))
                    (1110 (001 existing) (1001 conflict))
                    (1110 (001 proof) (10011 conflict)))))))))))

(0011 world-tell-all
  (0010 (world module-name clauses)
    (make-world world
                (1111 (clauses->tell-events module-name clauses)
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
(00001010 defmodule (name rules)
  (1110 (001 def) (001 *knowledge-journal*)
        (1110 (001 world-journal)
              (1110 (001 world-tell-all)
                    (1110 (001 make-world) (001 ()) (001 *knowledge-journal*) (001 ()))
                    (1110 (001 quote) name)
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
(00001010 tell-knowledge (module-name rules)
  (1110 (001 cond)
        (1110 (1110 (001 check-conflict) (1110 (001 quote) module-name) rules)
              (1110 (001 quote) (001 Conflict-detected)))
        (1110 (001 t)
              (1110 (001 def) (001 *knowledge-journal*)
                    (1110 (001 world-journal)
                          (1110 (001 world-tell-all)
                                (1110 (001 make-world) (001 ()) (001 *knowledge-journal*) (001 ()))
                                (1110 (001 quote) module-name)
                                rules))))))

(00001010 retract-knowledge (module-name clause)
  (1110 (001 def) (001 *knowledge-journal*)
        (1110 (001 world-journal)
              (1110 (001 world-retract)
                    (1110 (001 make-world) (001 ()) (001 *knowledge-journal*) (001 ()))
                    (1110 (001 quote) module-name)
                    clause))))

(0011 advise-all-world
  (0010 (world module-name clauses)
    (001000 ((decision (advice-all-decision-in-world world module-name clauses)))
      (110
        ((101 (100 decision) (001 accepted))
         (1110 decision (world-tell-all world module-name clauses)))
        ((010 ()) (1110 decision world))))))

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
(0011 legacy-world-transition-expansion
  (0010 (transition)
    (1110 (001 second)
          (1110 (001 list)
                (1110 (001 def) (001 *legacy-knowledge-transition*) transition)
                (1110 (001 cond)
                      (1110
                        (1110 (001 equal?)
                              (1110 (001 00000101)
                                    (1110 (001 00000101) (001 *legacy-knowledge-transition*)))
                              (1110 (001 quote) (001 accepted)))
                        (1110 (001 second)
                              (1110 (001 list)
                                    (1110 (001 def) (001 *knowledge-journal*)
                                          (1110 (001 world-journal)
                                                (1110 (001 second)
                                                      (001 *legacy-knowledge-transition*))))
                                    (1110 (001 00000101) (001 *legacy-knowledge-transition*)))))
                      (1110 (001 t)
                            (1110 (001 00000101) (001 *legacy-knowledge-transition*))))))))

(00001010 advise (module-name clause)
  (legacy-world-transition-expansion
    (1110 (001 advise-world)
          (1110 (001 make-world) (001 ()) (001 *knowledge-journal*) (001 ()))
          (1110 (001 quote) module-name)
          clause)))

(00001010 advise-all (module-name clauses)
  (legacy-world-transition-expansion
    (1110 (001 advise-all-world)
          (1110 (001 make-world) (001 ()) (001 *knowledge-journal*) (001 ()))
          (1110 (001 quote) module-name)
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
(0011 make-world-knowledge-package
  (0010 (world module-name)
    (110
      ((101 (110101100 module-name) (001 ()))
       (1110 (001 rejected) (1110 (001 reason) (001 invalid-module)) (1110 (001 input) module-name)))
      ((world-module-missing? world module-name)
       (1110 (001 rejected) (1110 (001 reason) (001 Module-not-found)) (1110 (001 input) module-name)))
      ((world-module-known? world module-name)
       (001000 ((clauses (world-clauses world module-name)))
         (110
           
           ((010 clauses)  (1110 (001 rejected) (1110 (001 reason) (001 invalid-batch)) (1110 (001 input) clauses)))
           ((010 ()) (make-knowledge-package module-name clauses))))))))

; The knowledge package version is structured data (0 1), not an
; atom. Compare recursively with exact D1 results, never W8 EQUAL on pairs.
(0011 внутрішня-рівність-версій
  (0010 (left right)
    (110
      ((0101 left) (0101 right))
      ((0101 right) (0101 (001 (0))))
      ((010 left)
       (110
         ((010 right) (101 left right))
         ((010 ()) (0101 (001 (0))))))
      ((010 right) (0101 (001 (0))))
      ((внутрішня-рівність-версій (100 left) (100 right))
       (внутрішня-рівність-версій (011 left) (011 right)))
      ((010 ()) (0101 (001 (0)))))))

(0011 import-knowledge-package-world
  (0010 (world package)
    (110
      
      ((010 package)  (1110 (1110 (001 rejected)
                   (1110 (001 reason) (001 invalid-package))
                   (1110 (001 input) package))
             world))
      ((101 (knowledge-proper-list? package) (001 ()))
       (1110 (1110 (001 rejected)
                   (1110 (001 reason) (001 invalid-package))
                   (1110 (001 input) package))
             world))
      ((101 (knowledge-package-entries-valid? package) (001 ()))
       (1110 (1110 (001 rejected)
                   (1110 (001 reason) (001 invalid-package))
                   (1110 (001 input) package))
             world))
      ((101 (knowledge-package-field (001 format) package) (001 my-lisp-knowledge))
       (110
         ((внутрішня-рівність-версій (knowledge-package-field (001 version) package)
                  *knowledge-package-version*)
          (advise-all-world world
                            (knowledge-package-field (001 module) package)
                            (knowledge-package-field (001 clauses) package)))
         ((010 ())
          (1110 (1110 (001 rejected)
                      (1110 (001 reason) (001 unsupported-version))
                      (1110 (001 version)
                            (knowledge-package-field (001 version) package)))
                world))))
      ((010 ())
       (1110 (1110 (001 rejected)
                   (1110 (001 reason) (001 invalid-package))
                   (1110 (001 input) package))
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
(00001010 import-knowledge-package (package)
  (legacy-world-transition-expansion
    (1110 (001 import-knowledge-package-world)
          (1110 (001 make-world) (001 ()) (001 *knowledge-journal*) (001 ()))
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
(0011 world-depth
  (0010 (world)
    (110
      
      ((010 (world-parent world))  0)
      ((010 ()) (01010 1 (world-depth (world-parent world)))))))

(0011 world-at-depth-from
  (0010 (world current-depth target-depth)
    (110
      ((11110111 current-depth target-depth)  world)
      ((010 ()) (001 World-not-found))
      
      ((010 (world-parent world))  (001 World-not-found))
      ((010 ()) (world-at-depth-from (world-parent world)
                              (01011 current-depth 1)
                              target-depth)))))

(0011 world-at-depth
  (0010 (world target-depth)
    (110
      ((11010 target-depth 0)  (001 World-not-found))
      ((010 ()) (world-at-depth-from world (world-depth world) target-depth)))))

(0011 world-journal-prefix
  (0010 (journal old-journal)
    (110
      ((11110111 journal old-journal) (001 ()))
      
      ((010 journal)  (001 World-not-ancestor))
      ((010 ())
       (001000 ((rest (world-journal-prefix (011 journal) old-journal)))
         (110
           ((world-not-ancestor? rest) rest)
           ((010 ()) (111 (100 journal) rest))))))))

(0011 world-not-ancestor?
  (0010 (value)
    (110
      
      ((010 value)  (101 value (001 World-not-ancestor)))
      )))

(0011 world-diff
  (0010 (from to)
    (110
      ((11110111 from to) (001 ()))
      
      ((010 (world-parent to))  (001 World-not-ancestor))
      ((010 ())
       (001000 ((earlier (world-diff from (world-parent to))))
         (110
           ((world-not-ancestor? earlier) earlier)
           ((010 ())
            (001000 ((transition
                    (world-journal-prefix
                      (world-journal to)
                      (world-journal (world-parent to)))))
              (110
                ((world-not-ancestor? transition) transition)
                ((010 ()) (1111 earlier transition)))))))))))

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
(0011 world-climb-to-depth
  (0010 (world current-depth target-depth)
    (110
      ((11110111 current-depth target-depth)  world)
      ((010 ()) (world-climb-to-depth (world-parent world)
                               (01011 current-depth 1)
                               target-depth)))))

(0011 world-common-ancestor-aligned
  (0010 (left right)
    (110
      ((11110111 left right) left)
      
      ((010 ()) (001 World-no-common-ancestor))
      
      ((010 (world-parent right))  (001 World-no-common-ancestor))
      ((010 ()) (world-common-ancestor-aligned (world-parent left)
                                        (world-parent right))))))

(0011 world-common-ancestor
  (0010 (left right)
    (001000 ((left-depth (world-depth left))
          (right-depth (world-depth right)))
      (001000 ((target-depth (110
                            ((11010 left-depth right-depth)  left-depth)
                            ((010 ()) right-depth))))
        (world-common-ancestor-aligned
          (world-climb-to-depth left left-depth target-depth)
          (world-climb-to-depth right right-depth target-depth))))))

(0011 world-no-common-ancestor?
  (0010 (value)
    (110
      
      ((010 value)  (101 value (001 World-no-common-ancestor)))
      )))

(0011 world-branch-diff
  (0010 (left right)
    (001000 ((base (world-common-ancestor left right)))
      (110
        ((world-no-common-ancestor? base) base)
        ((010 ())
         (1110 (1110 (001 base) base)
               (1110 (001 left) (world-diff base left))
               (1110 (001 right) (world-diff base right))))))))

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
(0011 knowledge-content-address
  (0010 (knowledge)
    (11110100 knowledge)))

(0011 world-address-content
  (0010 (world)
    (1110 (001 world-history)
          (world-journal world)
          (world-metadata world))))

(0011 world-content-address
  (0010 (world)
    (knowledge-content-address (world-address-content world))))
