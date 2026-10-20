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
  (функція (батько журнал метадані)
    (список (як-є world) батько журнал метадані)))

(визначити порожній-світ
  (функція ()
    (створити-світ (як-є ()) (як-є ()) (як-є ()))))

(визначити світ?
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      ((тотожне? (перше значення) (як-є world))
       (за-умовою
         ; Exact shape: (world parent journal metadata).
         ; D3 ATOM/CDR tests required tails; D4 NULL rejects an extra field.
         ; No D6 LENGTH, numeric arity literal, or host-side list checker.
         ((атом? (решта значення)) ні)
         ((атом? (решта (решта значення))) ні)
         ((атом? (решта (решта (решта значення)))) ні)
         ((порожній? (решта (решта (решта (решта значення))))) (атом? ()))
         (так ні)))
      (так ні))))

(визначити світ-батько (функція (світ) (друге світ)))
(визначити світ-журнал (функція (світ) (третє світ)))
; D6:100111 CADDDR has no admitted evaluator mechanism; derive the
; same fourth-field projection as exact D5:10011 CADDR after D3:011 CDR.
(визначити світ-метадані (функція (світ) (третє (решта світ))))

;; Events intentionally have the same data shape as `lib/knowledge.lisp`'s
;; journal, so a later migration can reuse packages and projections unchanged.
;; Події навмисно мають ту саму форму, що й журнал `lib/knowledge.lisp`.
;; Ereignisse haben absichtlich dieselbe Form wie in `lib/knowledge.lisp`.
(визначити світ-запис
  (функція (світ подія)
    (створити-світ світ
                (сполучити подія (світ-журнал світ))
                (світ-метадані світ))))

(визначити світ-повідомити
  (функція (світ назва-модуля клауза)
    (світ-запис світ (список (як-є tell) назва-модуля клауза))))

(визначити світ-відкликати
  (функція (світ назва-модуля клауза)
    (світ-запис світ (список (як-є retract) назва-модуля клауза))))

; D6 FILTER (101001) has no admitted evaluator mechanism. Select a
; module's event records directly by exact D3 atom/pair and D3 EQ on the
; atomic module-name field, preserving the original event order.
(визначити внутрішні-події-модуля
  (функція (назва-модуля події)
    (за-умовою
      ((порожній? події) (як-є ()))
      ((атом? події) (як-є ()))
      ((тотожне? (друге (перше події)) назва-модуля)
       (сполучити (перше події) (внутрішні-події-модуля назва-модуля (решта події))))
      (так (внутрішні-події-модуля назва-модуля (решта події))))))

(визначити світ-модуль-події
  (функція (світ назва-модуля)
    (внутрішні-події-модуля назва-модуля (світ-журнал світ))))

; Retract the first structurally equal clause; both atoms and nested
; pairs are compared with the locally-derived exact D1 equality law.
(визначити внутрішній-світ-прибрати-перше
  (функція (значення значення-списку)
    (за-умовою
      ((порожній? значення-списку) (як-є ()))
      ((атом? значення-списку) (як-є ()))
      ((внутрішня-рівність-версій значення (перше значення-списку)) (решта значення-списку))
      (так (сполучити (перше значення-списку) (внутрішній-світ-прибрати-перше значення (решта значення-списку)))))))

; Сумісна назва лишається лише на межі старого API.
(визначити world-remove-first внутрішній-світ-прибрати-перше)

(визначити внутрішній-світ-застосувати-подію
  (функція (клаузи подія)
    (за-умовою
      ((тотожне? (перше подія) (як-є tell)) (сполучити (третє подія) клаузи))
      ((тотожне? (перше подія) (як-є retract))
       (внутрішній-світ-прибрати-перше (третє подія) клаузи))
      (так клаузи))))

(визначити world-apply-event внутрішній-світ-застосувати-подію)

; D4 NOT of the D3 ATOM predicate: a module is known only when its
; event stream is a nonempty pair. D3 CONS cannot be a one-argument NOT.
(визначити світ-модуль-відомий?
  (функція (світ назва-модуля)
    (хибне? (атом? (світ-модуль-події світ назва-модуля)))))

(визначити внутрішній-світ-модуль-відсутній?
  (функція (світ назва-модуля)
    (атом? (світ-модуль-події світ назва-модуля))))

(визначити world-module-missing? внутрішній-світ-модуль-відсутній?)

; D5 REVERSE and D6 REDUCE are ratified names but cannot be presumed
; callable; derive the chronological event fold from D3 list structure.
(визначити внутрішній-зворот-подій
  (функція (події накопичувач)
    (за-умовою
      ((порожній? події) накопичувач)
      ((атом? події) накопичувач)
      (так (внутрішній-зворот-подій (решта події) (сполучити (перше події) накопичувач))))))

(визначити внутрішнє-згортання-подій
  (функція (події клаузи)
    (за-умовою
      ((порожній? події) клаузи)
      ((атом? події) клаузи)
      (так (внутрішнє-згортання-подій
                  (решта події)
                  (внутрішній-світ-застосувати-подію клаузи (перше події)))))))

(визначити світ-клаузи
  (функція (світ назва-модуля)
    (внутрішнє-згортання-подій
      (внутрішній-зворот-подій (світ-модуль-події світ назва-модуля) (як-є ()))
      (як-є ()))))

;; Pure reasoning adapters: the answer depends only on the explicit world,
;; module, and goal. They deliberately do not inspect `*knowledge-journal*`.
;; Чисті reasoning-адаптери: відповідь залежить лише від явно переданих світу,
;; модуля й цілі; глобальний `*knowledge-journal*` вони не читають.
;; Reine Schlussfolgerungsadapter: Die Antwort hängt nur von der expliziten
;; Welt, dem Modul und dem Ziel ab; `*knowledge-journal*` wird nicht gelesen.
(визначити міркувати-у-світ
  (функція (світ назва-модуля мета)
    (за-умовою
      ((світ-модуль-відомий? світ назва-модуля)
       (міркувати мета (світ-клаузи світ назва-модуля)))
      ((внутрішній-світ-модуль-відсутній? світ назва-модуля)
       (як-є Module-not-found)))))

(визначити вперед-у-світ
  (функція (світ назва-модуля)
    (за-умовою
      ((світ-модуль-відомий? світ назва-модуля)
       (виконати-багатоваріантне-виведення (світ-клаузи світ назва-модуля) (як-є ())))
      ((внутрішній-світ-модуль-відсутній? світ назва-модуля)
       (як-є Module-not-found)))))

; Derived D1 symbol predicate for world module names. This is a Lisp
; law over ATOM/NULL/EQ and exact D8 write+string-to-symbol mechanisms,
; not a native admission of the unrelated D9:110101100 coordinate.
(визначити внутрішній-символ?
  (функція (значення)
    (за-умовою
      ((порожній? значення) (порожній? (як-є (ні))))
      ((хибне? (атом? значення)) (порожній? (як-є (ні))))
      ((тотожне? значення (текст-у-символ (значення-у-текст значення))) (порожній? (як-є ())))
      (так (порожній? (як-є (ні)))))))

(визначити порада-рішення-у-світ
  (функція (світ назва-модуля клауза)
    (за-умовою
      ((хибне? (внутрішній-символ? назва-модуля))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-module)) (список (як-є input) клауза)))
      ((тотожне? (клауза-бази-знань-коректна? клауза) (як-є ()))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-clause)) (список (як-є input) клауза)))
      (так
       (нехай-похідне ((протилежне (отримати-протилежну-голову-твердження-знання (перше клауза))))
         (нехай-похідне ((докази (за-умовою
                         ((світ-модуль-відомий? світ назва-модуля)
                          (міркувати-у-світ світ назва-модуля протилежне))
                         )))
           (за-умовою
             
             ((атом? докази)  (список (як-є accepted)
                    (список (як-є module) назва-модуля)
                    (список (як-є knowledge) клауза)))
             (так
              (список (як-є conflict)
                    (список (як-є new) клауза)
                    (список (як-є existing) протилежне)
                    (список (як-є proof) (перше докази)))))))))))

(визначити порадити-світ
  (функція (світ назва-модуля клауза)
    (нехай-похідне ((рішення (порада-рішення-у-світ світ назва-модуля клауза)))
      (за-умовою
        ((тотожне? (перше рішення) (як-є accepted))
         (список рішення (світ-повідомити світ назва-модуля клауза)))
        (так (список рішення світ))))))

;; The batch form creates exactly one child world after the whole proposed
;; knowledge set validates and proves conflict-free. Proposed rules can support
;; or contradict one another during the check; no prefix can leak on failure.
;; Пакетна форма створює рівно один дочірній світ лише після validation усього
;; набору й перевірки конфліктів; жоден префікс не просочується при помилці.
;; Die Stapelform erzeugt genau eine Kindwelt erst nach vollständiger Prüfung;
;; bei einem Fehler kann kein Präfix des Pakets durchsickern.
(визначити порада-всі-рішення-у-світ
  (функція (світ назва-модуля клаузи)
    (за-умовою
      ((хибне? (внутрішній-символ? назва-модуля))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-module)) (список (як-є input) клаузи)))
      
      ((атом? клаузи)  (список (як-є rejected) (список (як-є reason) (як-є invalid-batch)) (список (як-є input) клаузи)))
      ((тотожне? (правильно-структурований-список-знань? клаузи) (як-є ()))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-batch)) (список (як-є input) клаузи)))
      ((тотожне? (клаузи-бази-знань-коректні? клаузи) (як-є ()))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-clause)) (список (як-є input) клаузи)))
      (так
       (нехай-похідне ((наявні (за-умовою
                         ((світ-модуль-відомий? світ назва-модуля)
                          (світ-клаузи світ назва-модуля))
                         )))
         (нехай-похідне ((суперечність (виявити-суперечність-у-групі-порад
                           клаузи клаузи (приєднати клаузи наявні))))
           (за-умовою
             
             ((атом? суперечність)  (список (як-є accepted)
                    (список (як-є module) назва-модуля)
                    (список (як-є knowledge) клаузи)))
             (так
              (список (як-є conflict)
                    (список (як-є new) (перше суперечність))
                    (список (як-є existing) (друге суперечність))
                    (список (як-є proof) (третє суперечність)))))))))))

(визначити світ-повідомити-всі
  (функція (світ назва-модуля клаузи)
    (створити-світ світ
                (приєднати (перетворити-клаузи-на-події-повідомлення назва-модуля клаузи)
                        (світ-журнал світ))
                (світ-метадані світ))))

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
(визначити визначити-модуль
  (макрос
    (функція (назва правила)
  (список (як-є def) (як-є *knowledge-journal*)
        (список (як-є світ-журнал)
              (список (як-є світ-повідомити-всі)
                    (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
                    (список (як-є quote) назва)
                    правила))))))

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
(визначити повідомити-знання
  (макрос
    (функція (назва-модуля правила)
  (список (як-є cond)
        (список (список (як-є check-conflict) (список (як-є quote) назва-модуля) правила)
              (список (як-є quote) (як-є Conflict-detected)))
        (список (як-є так)
              (список (як-є def) (як-є *knowledge-journal*)
                    (список (як-є світ-журнал)
                          (список (як-є світ-повідомити-всі)
                                (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
                                (список (як-є quote) назва-модуля)
                                правила))))))))

(визначити відкликати-знання
  (макрос
    (функція (назва-модуля клауза)
  (список (як-є def) (як-є *knowledge-journal*)
        (список (як-є світ-журнал)
              (список (як-є world-retract)
                    (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
                    (список (як-є quote) назва-модуля)
                    клауза))))))

(визначити порадити-всі-світ
  (функція (світ назва-модуля клаузи)
    (нехай-похідне ((рішення (порада-всі-рішення-у-світ світ назва-модуля клаузи)))
      (за-умовою
        ((тотожне? (перше рішення) (як-є accepted))
         (список рішення (світ-повідомити-всі світ назва-модуля клаузи)))
        (так (список рішення світ))))))

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
  (функція (перехід)
    (тотожне? (перше-першого перехід) (як-є accepted))))

; Тільки похідний SENS-селектор. D3:100 CAR витягає рішення
; з (decision world); числовий 00000101 не може бути викликом CAR.
(визначити внутрішнє-рішення-переходу
  (функція (перехід)
    (перше перехід)))

(визначити внутрішній-світ-розгорнути-історичний-перехід
  (функція (перехід)
    (список (як-є second)
          (список (як-є list)
                (список (як-є def) (як-є *legacy-knowledge-transition*) перехід)
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

(визначити legacy-world-transition-expansion внутрішній-світ-розгорнути-історичний-перехід)

(визначити порадити
  (макрос
    (функція (назва-модуля клауза)
  (внутрішній-світ-розгорнути-історичний-перехід
    (список (як-є порадити-світ)
          (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
          (список (як-є quote) назва-модуля)
          клауза)))))

(визначити порадити-всі
  (макрос
    (функція (назва-модуля клаузи)
  (внутрішній-світ-розгорнути-історичний-перехід
    (список (як-є порадити-всі-світ)
          (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
          (список (як-є quote) назва-модуля)
          клаузи)))))

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
(визначити створити-світ-знання-пакет
  (функція (світ назва-модуля)
    (за-умовою
      ((хибне? (внутрішній-символ? назва-модуля))
       (список (як-є rejected) (список (як-є reason) (як-є invalid-module)) (список (як-є input) назва-модуля)))
      ((внутрішній-світ-модуль-відсутній? світ назва-модуля)
       (список (як-є rejected) (список (як-є reason) (як-є Module-not-found)) (список (як-є input) назва-модуля)))
      ((світ-модуль-відомий? світ назва-модуля)
       (нехай-похідне ((клаузи (світ-клаузи світ назва-модуля)))
         (за-умовою
           
           ((атом? клаузи)  (список (як-є rejected) (список (як-є reason) (як-є invalid-batch)) (список (як-є input) клаузи)))
           (так (створити-пакет-структурованих-знань назва-модуля клаузи))))))))

; The knowledge package version is structured data (0 1), not an
; atom. Compare recursively with exact D1 results, never W8 EQUAL on pairs.
(визначити внутрішня-рівність-версій
  (функція (ліве праве)
    (за-умовою
      ((порожній? ліве) (порожній? праве))
      ((порожній? праве) (порожній? (як-є (ні))))
      ((атом? ліве)
       (за-умовою
         ((атом? праве) (тотожне? ліве праве))
         (так (порожній? (як-є (ні))))))
      ((атом? праве) (порожній? (як-є (ні))))
      ((внутрішня-рівність-версій (перше ліве) (перше праве))
       (внутрішня-рівність-версій (решта ліве) (решта праве)))
      (так (порожній? (як-є (ні)))))))

(визначити імпорт-знання-пакет-світ
  (функція (світ пакет)
    (за-умовою
      
      ((атом? пакет)  (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) пакет))
             світ))
      ((хибне? (правильно-структурований-список-знань? пакет))
       (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) пакет))
             світ))
      ((хибне? (записи-пакета-знань-коректні? пакет))
       (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) пакет))
             світ))
      ((тотожне? (отримати-поле-пакета-знань (як-є format) пакет) (як-є my-lisp-knowledge))
       (за-умовою
         ((внутрішня-рівність-версій (отримати-поле-пакета-знань (як-є version) пакет)
                  *knowledge-package-version*)
          (порадити-всі-світ світ
                            (отримати-поле-пакета-знань (як-є module) пакет)
                            (отримати-поле-пакета-знань (як-є clauses) пакет)))
         (так
          (список (список (як-є rejected)
                      (список (як-є reason) (як-є unsupported-version))
                      (список (як-є version)
                            (отримати-поле-пакета-знань (як-є version) пакет)))
                світ))))
      (так
       (список (список (як-є rejected)
                   (список (як-є reason) (як-є invalid-package))
                   (список (як-є input) пакет))
             світ)))))

;; Package import completes the writer migration. The legacy macro delegates
;; validation, version handling, conflict detection, and the atomic transition
;; to the data-only World importer; only an accepted result rebinds the journal.
;; Імпорт пакетів завершує міграцію writer-ів: validation, version handling,
;; конфлікти й атомарний перехід делеговано data-only World-імпортеру; журнал
;; перевизначається лише для accepted.
;; Der Paketimport schließt die Writer-Migration ab: Prüfung, Versionierung,
;; Konflikte und atomarer Übergang liegen beim datenreinen World-Importer; nur
;; ein akzeptiertes Ergebnis bindet das Journal neu.
(визначити імпортувати-пакет-знань
  (макрос
    (функція (пакет)
  (внутрішній-світ-розгорнути-історичний-перехід
    (список (як-є імпорт-знання-пакет-світ)
          (список (як-є створити-світ) (як-є ()) (як-є *knowledge-journal*) (як-є ()))
          пакет)))))

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
(визначити світ-глибина
  (функція (світ)
    (за-умовою
      
      ((атом? (світ-батько світ))  0)
      (так (додати 1 (світ-глибина (світ-батько світ)))))))

(визначити отримати-світ-на-заданій-глибині-від-поточного
  (функція (світ поточна-глибина цільова-глибина)
    (за-умовою
      ((тотожне? поточна-глибина цільова-глибина)  світ)
      (так (як-є World-not-found))
      
      ((атом? (світ-батько світ))  (як-є World-not-found))
      (так (отримати-світ-на-заданій-глибині-від-поточного (світ-батько світ)
                              (відняти поточна-глибина 1)
                              цільова-глибина)))))

(визначити світ-у-глибина
  (функція (світ цільова-глибина)
    (за-умовою
      ((менше? цільова-глибина 0)  (як-є World-not-found))
      (так (отримати-світ-на-заданій-глибині-від-поточного світ (світ-глибина світ) цільова-глибина)))))

(визначити отримати-префікс-журналу-світу
  (функція (журнал старий-журнал)
    (за-умовою
      ((внутрішня-рівність-версій журнал старий-журнал) (як-є ()))
      
      ((атом? журнал)  (як-є World-not-ancestor))
      (так
       (нехай-похідне ((залишок-подій (отримати-префікс-журналу-світу (решта журнал) старий-журнал)))
         (за-умовою
           ((цей-світ-не-є-предком-іншого? залишок-подій) залишок-подій)
           (так (сполучити (перше журнал) залишок-подій))))))))

(визначити цей-світ-не-є-предком-іншого?
  (функція (значення)
    (за-умовою
      
      ((атом? значення)  (тотожне? значення (як-є World-not-ancestor)))
      )))

(визначити світ-різниця
  (функція (звідки куди)
    (за-умовою
      ((внутрішня-рівність-версій звідки куди) (як-є ()))
      
      ((атом? (світ-батько куди))  (як-є World-not-ancestor))
      (так
       (нехай-похідне ((ранні-події (світ-різниця звідки (світ-батько куди))))
         (за-умовою
           ((цей-світ-не-є-предком-іншого? ранні-події) ранні-події)
           (так
            (нехай-похідне ((події-переходу
                    (отримати-префікс-журналу-світу
                      (світ-журнал куди)
                      (світ-журнал (світ-батько куди)))))
              (за-умовою
                ((цей-світ-не-є-предком-іншого? події-переходу) події-переходу)
                (так (приєднати ранні-події події-переходу)))))))))))

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
(визначити піднятись-ланцюгом-світу-до-заданої-глибини
  (функція (світ поточна-глибина цільова-глибина)
    (за-умовою
      ((тотожне? поточна-глибина цільова-глибина)  світ)
      (так (піднятись-ланцюгом-світу-до-заданої-глибини (світ-батько світ)
                               (відняти поточна-глибина 1)
                               цільова-глибина)))))

(визначити вирівняний-спільний-предок-двох-світів
  (функція (ліве праве)
    (за-умовою
      ((внутрішня-рівність-версій ліве праве) ліве)
      ((атом? ліве) (як-є World-no-common-ancestor))
      ((атом? праве) (як-є World-no-common-ancestor))
      ((атом? (світ-батько ліве)) (як-є World-no-common-ancestor))
      ((атом? (світ-батько праве)) (як-є World-no-common-ancestor))
      (так
       (вирівняний-спільний-предок-двох-світів (світ-батько ліве)
                                      (світ-батько праве))))))

; An ancestor is found by walking immutable parents. Its SENS verdict
; is a D1 predicate, never a numeric depth or an historical W8 EQ value.
(визначити внутрішній-предок-світу?
  (функція (кандидат світ)
    (за-умовою
      ((атом? світ) ні)
      ((внутрішня-рівність-версій кандидат світ) так)
      ((атом? (світ-батько світ)) ні)
      (так
       (внутрішній-предок-світу? кандидат (світ-батько світ))))))

; The first ancestor of left occurring in right's ancestry is the deepest
; common world. This is pure SENS structure, independent of D24+ arithmetic.
(визначити світ-спільний-предок
  (функція (ліве праве)
    (за-умовою
      ((атом? ліве) (як-є World-no-common-ancestor))
      ((атом? праве) (як-є World-no-common-ancestor))
      ((внутрішній-предок-світу? ліве праве) ліве)
      ((атом? (світ-батько ліве)) (як-є World-no-common-ancestor))
      (так (світ-спільний-предок (світ-батько ліве) праве)))))

(визначити світи-не-мають-спільного-предка?
  (функція (значення)
    (за-умовою
      ((атом? значення) (тотожне? значення (як-є World-no-common-ancestor)))
      (так ні))))

(визначити світ-гілка-різниця
  (функція (ліве праве)
    (нехай-похідне ((спільна-основа (світ-спільний-предок ліве праве)))
      (за-умовою
        ((світи-не-мають-спільного-предка? спільна-основа) спільна-основа)
        (так
         (список (список (як-є base) спільна-основа)
               (список (як-є left) (світ-різниця спільна-основа ліве))
               (список (як-є right) (світ-різниця спільна-основа праве))))))))

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
  (функція (знання)
    (значення-у-текст знання)))

(визначити світ-адреса-вміст
  (функція (світ)
    (список (як-є world-history)
            (світ-журнал світ)
            (світ-метадані світ))))

(визначити світ-вміст-адреса
  (функція (світ)
    (знання-вміст-адреса (світ-адреса-вміст світ))))

; opt-in повна укр-поверхня: первинні D9-визначення в цьому блоці названі укр.
(визначити advise-all-world порадити-всі-світ)
(визначити knowledge-content-address знання-вміст-адреса)
(визначити make-world створити-світ)
(визначити world-address-content світ-адреса-вміст)
(визначити world-at-depth-from отримати-світ-на-заданій-глибині-від-поточного)
(визначити world-clauses світ-клаузи)
(визначити world-climb-to-depth піднятись-ланцюгом-світу-до-заданої-глибини)
(визначити world-common-ancestor світ-спільний-предок)
(визначити world-common-ancestor-aligned вирівняний-спільний-предок-двох-світів)
(визначити world-depth світ-глибина)
(визначити world-diff світ-різниця)
(визначити world-journal світ-журнал)
(визначити world-metadata світ-метадані)
(визначити world-module-events світ-модуль-події)
(визначити world-module-known? світ-модуль-відомий?)
(визначити world-no-common-ancestor? світи-не-мають-спільного-предка?)
(визначити world-not-ancestor? цей-світ-не-є-предком-іншого?)
(визначити world-parent світ-батько)
(визначити world-record світ-запис)
(визначити world-tell світ-повідомити)
(визначити world-tell-all світ-повідомити-всі)

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

; Історичні англомовні назви — сумісні зв'язування, без дублювання функцій.
(визначити world? світ?)
(визначити reason-in-world міркувати-у-світ)
(визначити forward-in-world вперед-у-світ)
(визначити advice-decision-in-world порада-рішення-у-світ)
(визначити advise-world порадити-світ)
(визначити advice-all-decision-in-world порада-всі-рішення-у-світ)
(визначити defmodule визначити-модуль)
(визначити tell-knowledge повідомити-знання)
(визначити retract-knowledge відкликати-знання)
(визначити make-world-knowledge-package створити-світ-знання-пакет)
(визначити import-knowledge-package-world імпорт-знання-пакет-світ)
(визначити world-at-depth світ-у-глибина)
(визначити world-journal-prefix отримати-префікс-журналу-світу)
(визначити world-branch-diff світ-гілка-різниця)

; Історичні зовнішні імена — лише псевдоніми до українських макросів.
(визначити advise порадити)
(визначити advise-all порадити-всі)
(визначити import-knowledge-package імпортувати-пакет-знань)
