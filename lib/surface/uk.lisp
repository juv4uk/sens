; Ukrainian surface for necessary evaluator forms and derived vocabulary.
; Українська поверхня для необхідних форм та похідного словника.
;
; Canon 0+7 names are NOT defined here. The immutable Canon resolver owns the
; ratified Ukrainian spellings directly, before ordinary lexical lookup.
; Everything below Canon remains language-owned vocabulary over the same
; semantic environment, except identities migrated under ADR-007/008. Necessary
; forms 0010/0011 are resolved directly by evaluator identity; migrated ordinary
; peer spellings are direct runtime bindings rather than cross-surface aliases.
;
; Principle: one semantic implementation, multiple human surfaces.
;           одна семантична реалізація, кілька людських поверхонь.
;
; Full-profile loading order: macro.lisp → core.lisp → unify.lisp → reason.lisp →
; forward.lisp → knowledge.lisp → persistent-map.lisp → persistent-vector.lisp →
; time.lisp → epistemic.lisp → uk.lisp (this file).

;; ═══════════════════════════════════════════════════════════════
;; Necessary evaluator forms — direct semantic peer spellings
;; Необхідні форми — прямі назви одних семантичних тотожностей
;; ═══════════════════════════════════════════════════════════════

; 0010: `lambda` / `функція` and 0011: `define` / `визначити` are owned by
; the evaluator's necessary-form identity resolver. They are intentionally NOT
; redefined here as macros and neither spelling expands through the other.
; Sanskrit rows remain explicitly missing until ratified.

; 0012: `defmacro` / `визначити-макрос` is a language-owned first-class
; Macro value derived by macro.lisp and bound directly to both public spellings by
; the bootstrap loader. It is not redefined here through an English surface.
; Sanskrit remains explicitly missing until ratified.

;; ═══════════════════════════════════════════════════════════════
;; Canon 0+7 — owned by immutable resolver (status: stable)
;; Канон 0+7 — належить незмінному resolver-у (статус: stable)
;; ═══════════════════════════════════════════════════════════════

; як-є, атом?, тотожне?, сполучити, перше, решта, за-умовою
; не є звичайними bindings і навмисно не можуть бути перевизначені тут.

; Українські імена тих самих канонічних значень істини й хиби.
; Це не нові логічні об'єкти: істина є тим самим символом t, а хиба — тим
; самим Canon 0 `()`. Шар подання показує t як `істина` лише в українському REPL.
(00001001 істина t)
(00001001 хиба (00000001 ()))

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Arithmetic (status: stable)
;; Арифметика
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 0104, 1001–1003: `додати`, `відняти`, `помножити`,
; `поділити`, їхні Sanskrit peers і symbolic notation встановлюються runtime
; напряму на ті самі callable values. Жодна людська поверхня не є мостом.
(00001001 модуль abs)
(00001001 найменше min)
(00001001 найбільше max)
(00001001 остача mod)
(00001001 частка quotient)
(00001001 корінь sqrt)
(00001001 цілий-корінь isqrt)
(00001001 найменше-у-списку min-list)
(00001001 найбільше-у-списку max-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Comparisons (status: stable)
;; Порівняння
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: `менше?`, `більше?`, `рівне?`, їхні
; Sanskrit peers і symbolic notation є прямими runtime bindings.
(00001001 не-більше? <=)
(00001001 не-менше? >=)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Predicates (status: stable)
;; Предикати
;; ═══════════════════════════════════════════════════════════════

(00001001 однакові? equal?)
(00001001 символ? symbol?)
(00001001 текст-передує? string<?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Lists (status: stable)
;; Списки
;; ═══════════════════════════════════════════════════════════════

(00001001 список list)
(00001001 довжина length)
(00001001 приєднати append)
(00001001 зворот reverse)
(00001001 елемент-списку-за-індексом nth)
(00001001 значення-у-списку? member?)
(00001001 знайти-за-ключем assoc)
(00001001 пара pair)
(00001001 друге second)
(00001001 третє third)
(00001001 четверте fourth)
(00001001 п'яте fifth)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Higher-order functions (status: stable)
;; Функції вищого порядку
;; ═══════════════════════════════════════════════════════════════

(00001001 відобразити map)
(00001001 відсіяти filter)
(00001001 згорнути reduce)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Strings (status: stable)
;; Рядки
;; ═══════════════════════════════════════════════════════════════

; 1043: `string-append` / `зчепити` встановлюються як registry-driven direct peers.
; 1044: `string-length` / `довжина-тексту` встановлюються як registry-driven direct peers.
; 1045: `string-empty?` / `текст-порожній?` / `порожній-текст?` встановлюються як registry-driven direct peers.
; 1046: `string-prefix?` / `префікс-тексту?` встановлюються як registry-driven direct peers.
; 1047: `string-contains?` / `фрагмент-у-тексті?` встановлюються як registry-driven direct peers.
; 1048: `string-first` / `перший-символ-тексту` встановлюються як registry-driven direct peers.
; 1049: `string-rest` / `решта-символів-тексту` встановлюються як registry-driven direct peers.
; 1050: `string-slice` / `відрізати` встановлюються як registry-driven direct peers.
; 1051: `symbol->string` / `символ-у-текст` встановлюються як registry-driven direct peers.
; 1052: `string->symbol` / `текст-у-символ` встановлюються як registry-driven direct peers.
(00001001 число-у-текст number->string)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — I/O (status: stable)
;; Ввід/вивід
;; ═══════════════════════════════════════════════════════════════


;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Vectors (status: stable)
;; Вектори
;; ═══════════════════════════════════════════════════════════════


; vector-set! є мутацією — тому знак ! зберігається і в українській назві.

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Time (status: stable)
;; Час
;; ═══════════════════════════════════════════════════════════════


;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Other (status: stable)
;; Інше
;; ═══════════════════════════════════════════════════════════════

(00001001 без-змін identity)
(00001001 та and)
(00001001 або or)
(00001001 нехай let)
(00001001 нехай* let*)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent map (status: stable)
;; Сталі асоціативні карти
;; User-facing API only; AVL internals (node-*, rotate-*, balance-*) excluded.
;; ═══════════════════════════════════════════════════════════════

(00001001 порожня-карта map-empty)
(00001001 отримати-з-карти map-get)
(00001001 вставити-в-карту map-insert)
(00001001 ключ-у-карті? map-contains?)
(00001001 карта-у-список map->list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent vector (status: stable)
;; Сталі вектори
;; User-facing API only; RRB-tree internals (vnode-*, vrotate-*, vbalance-*) excluded.
;; ═══════════════════════════════════════════════════════════════

(00001001 порожній-вектор vec-empty)
(00001001 додати-до-вектора vec-conj)
(00001001 розмір-вектора vec-count)
(00001001 елемент-вектора-за-індексом vec-nth)
(00001001 вектор-у-список vec->list)
(00001001 вектор-із-списку vec-from-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Time library (status: stable)
;; Бібліотека часу
;; ═══════════════════════════════════════════════════════════════

(00001001 поточний-всч utc-now)
(00001001 всч-із-юнікс utc-from-unix)
(00001001 юнікс-спостереження-у-всч unix-time-observation->utc)
(00001001 мілісекунди-із-наносекунд milliseconds-from-nanoseconds)
(00001001 монотонний-мс mono-ms)
(00001001 назва-часового-поясу timezone-name)
(00001001 визначити-часовий-пояс timezone-detect)
(00001001 зміщення-часового-поясу-в-секундах timezone-offset-seconds)
(00001001 дедлайн-досягнуто? deadline-reached?)
(00001001 дедлайн-досягнуто-на-момент? deadline-reached-at?)
(00001001 минуло-нс elapsed-ns)
(00001001 дедлайн-від deadline-from)
(00001001 дедлайн-через-нс deadline-after-ns)
(00001001 запитати-інтернет-час internet-time-sync)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Knowledge/Reasoning (status: stable)
;; База знань та логічний висновок
;; User-facing API only; indexing internals excluded.
;; ═══════════════════════════════════════════════════════════════

(00001001 факт? is-fact?)
(00001001 описати describe)
(00001001 зібрати-факти-про collect-facts-about)
(00001001 атом-у-списку? contains-atom?)
(00001001 пряме-виведення forward-in)
(00001001 логічний-висновок reason-in)
; Публічний предикат читається як питання; стара дієслівна назва лишається
; compatibility alias, щоб наявні українські програми не ламалися.
(00001001 конфлікт? check-conflict)
(00001001 перевірити-конфлікт check-conflict)
(00001001 модуль-відомий? module-known?)
(00001001 поточні-клаузи-модуля module-clauses-now)

; Reasoning engine
(00001001 довести-мету prove-goal)
(00001001 довести-мети prove-goals)
(00001001 пояснити-доведення explain-proof)
(00001001 джерело-доведення source-of)
(00001001 походження provenance)
(00001001 міркування reason)
(00001001 пояснити-міркування reason-explain)

; Unification
(00001001 уніфікувати unify)
(00001001 логічна-змінна logic-var)
(00001001 змінна? var?)
(00001001 підставити apply-subst)
(00001001 розіменувати walk)
; Occurs-check є питанням t/(), тому preferred-назва має ?. Стара назва
; збережена як compatibility alias.
(00001001 змінна-зустрічається? occurs-check)
(00001001 перевірити-зустрічання occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Epistemic (status: stable)
;; Епістемічні структури
;; ═══════════════════════════════════════════════════════════════

(00001001 твердження? claim?)
(00001001 зміст-твердження claim-statement)
(00001001 стан-розгляду-твердження claim-review)
(00001001 доказ? evidence?)
(00001001 метод-доказу evidence-method)
(00001001 результат-доказу evidence-outcome)
(00001001 спостереження? observation?)
(00001001 зміст-спостереження observation-statement)
(00001001 намір? intent?)
(00001001 мета-наміру intent-goal)
(00001001 підтримувальний-доказ supporting-evidence)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Missing UK fill (status: stable)
;; ═══════════════════════════════════════════════════════════════

(00001001 генерувати-символ gensym)

;; ═══════════════════════════════════════════════════════════════
;; Сумісність назв після смислового аудиту 2026-09-08
;; Preferred-назви вище є основними для нових програм; старі назви
;; лишаються alias-ами тієї самої семантичної тотожності.
;; ═══════════════════════════════════════════════════════════════

; M8: примітиви нижче вже не матеріалізуються як bare English runtime values.
; Alias несе exact SENS напряму; людське ім'я лишається boundary projection.
(00001001 текст-менше? string<?)
(00001001 за-номером nth)
(00001001 перший-знак 00111111)
(00001001 решта-знаків 01000000)
(00001001 встановити-вектор! 01010011)
(00001001 монотонний-час 01011010)
(00001001 юнікс-із-спостереження unix-time-observation->utc)
(00001001 часовий-пояс-назва timezone-name)
(00001001 часовий-пояс-виявити timezone-detect)
(00001001 часовий-пояс-зміщення timezone-offset-seconds)
(00001001 дедлайн-досягнуто-о? deadline-reached-at?)
(00001001 дедлайн-з deadline-from)
(00001001 інтернет-час-синхронізація internet-time-sync)
(00001001 карта-порожня map-empty)
(00001001 карта-отримати map-get)
(00001001 карта-вставити map-insert)
(00001001 вектор-порожній vec-empty)
(00001001 вектор-додати vec-conj)
(00001001 вектор-розмір vec-count)
(00001001 вектор-за-номером vec-nth)
(00001001 вперед-висновок forward-in)
(00001001 модуль-умови-зараз module-clauses-now)
(00001001 обґрунтувати-доведення explain-proof)
(00001001 міркування-пояснити reason-explain)
(00001001 відшукати walk)
(00001001 твердження-текст claim-statement)
(00001001 твердження-відгук claim-review)
(00001001 доказ-метод evidence-method)
(00001001 доказ-результат evidence-outcome)
(00001001 спостереження-текст observation-statement)
(00001001 намір-мета intent-goal)
(00001001 підтримуючий-доказ supporting-evidence)

(00001001 містить? member?)
(00001001 текст-починається? 00111101)
(00001001 містить-текст? 00111110)
(00001001 код-у-текст 01000100)
(00001001 текст-у-код 01000101)
(00001001 у-текст 01001100)
(00001001 юнікс-час-зараз 01011011)
(00001001 дедлайн-після-нс deadline-after-ns)
(00001001 карта-містить? map-contains?)
(00001001 містить-атом? contains-atom?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — SA missing fill (Sanskrit surface for previously missing)
;; These are Sanskrit aliases loaded from uk.lisp context for reference.
;; The actual SA bindings are in sa.lisp; these UK lines ensure UK
;; coverage for gensym and env which were previously missing.
;; ═══════════════════════════════════════════════════════════════