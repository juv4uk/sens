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
(0011 істина t)
(0011 хиба (001 ()))

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Arithmetic (status: stable)
;; Арифметика
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 0104, 1001–1003: `додати`, `відняти`, `помножити`,
; `поділити`, їхні Sanskrit peers і symbolic notation встановлюються runtime
; напряму на ті самі callable values. Жодна людська поверхня не є мостом.
(0011 модуль abs)
(0011 найменше min)
(0011 найбільше max)
(0011 остача mod)
(0011 частка quotient)
(0011 корінь sqrt)
(0011 цілий-корінь isqrt)
(0011 найменше-у-списку min-list)
(0011 найбільше-у-списку max-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Comparisons (status: stable)
;; Порівняння
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: `менше?`, `більше?`, `рівне?`, їхні
; Sanskrit peers і symbolic notation є прямими runtime bindings.
(0011 не-більше? <=)
(0011 не-менше? >=)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Predicates (status: stable)
;; Предикати
;; ═══════════════════════════════════════════════════════════════

(0011 однакові? equal?)
(0011 символ? symbol?)
(0011 текст-передує? string<?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Lists (status: stable)
;; Списки
;; ═══════════════════════════════════════════════════════════════

(0011 список list)
(0011 довжина length)
(0011 приєднати append)
(0011 зворот reverse)
(0011 елемент-списку-за-індексом nth)
(0011 значення-у-списку? member?)
(0011 знайти-за-ключем assoc)
(0011 пара pair)
(0011 друге second)
(0011 третє third)
(0011 четверте fourth)
(0011 п'яте fifth)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Higher-order functions (status: stable)
;; Функції вищого порядку
;; ═══════════════════════════════════════════════════════════════

(0011 відобразити map)
(0011 відсіяти filter)
(0011 згорнути reduce)

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
(0011 число-у-текст number->string)

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

(0011 без-змін identity)
(0011 та and)
(0011 або or)
(0011 нехай let)
(0011 нехай* let*)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent map (status: stable)
;; Сталі асоціативні карти
;; User-facing API only; AVL internals (node-*, rotate-*, balance-*) excluded.
;; ═══════════════════════════════════════════════════════════════

(0011 порожня-карта map-empty)
(0011 отримати-з-карти map-get)
(0011 вставити-в-карту map-insert)
(0011 ключ-у-карті? map-contains?)
(0011 карта-у-список map->list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent vector (status: stable)
;; Сталі вектори
;; User-facing API only; RRB-tree internals (vnode-*, vrotate-*, vbalance-*) excluded.
;; ═══════════════════════════════════════════════════════════════

(0011 порожній-вектор vec-empty)
(0011 додати-до-вектора vec-conj)
(0011 розмір-вектора vec-count)
(0011 елемент-вектора-за-індексом vec-nth)
(0011 вектор-у-список vec->list)
(0011 вектор-із-списку vec-from-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Time library (status: stable)
;; Бібліотека часу
;; ═══════════════════════════════════════════════════════════════

(0011 поточний-всч utc-now)
(0011 всч-із-юнікс utc-from-unix)
(0011 юнікс-спостереження-у-всч unix-time-observation->utc)
(0011 мілісекунди-із-наносекунд milliseconds-from-nanoseconds)
(0011 монотонний-мс mono-ms)
(0011 назва-часового-поясу timezone-name)
(0011 визначити-часовий-пояс timezone-detect)
(0011 зміщення-часового-поясу-в-секундах timezone-offset-seconds)
(0011 дедлайн-досягнуто? deadline-reached?)
(0011 дедлайн-досягнуто-на-момент? deadline-reached-at?)
(0011 минуло-нс elapsed-ns)
(0011 дедлайн-від deadline-from)
(0011 дедлайн-через-нс deadline-after-ns)
(0011 запитати-інтернет-час internet-time-sync)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Knowledge/Reasoning (status: stable)
;; База знань та логічний висновок
;; User-facing API only; indexing internals excluded.
;; ═══════════════════════════════════════════════════════════════

(0011 факт? is-fact?)
(0011 описати describe)
(0011 зібрати-факти-про collect-facts-about)
(0011 атом-у-списку? contains-atom?)
(0011 пряме-виведення forward-in)
(0011 логічний-висновок reason-in)
; Публічний предикат читається як питання; стара дієслівна назва лишається
; compatibility alias, щоб наявні українські програми не ламалися.
(0011 конфлікт? check-conflict)
(0011 перевірити-конфлікт check-conflict)
(0011 модуль-відомий? module-known?)
(0011 поточні-клаузи-модуля module-clauses-now)

; Reasoning engine
(0011 довести-мету prove-goal)
(0011 довести-мети prove-goals)
(0011 пояснити-доведення explain-proof)
(0011 джерело-доведення source-of)
(0011 походження provenance)
(0011 міркування reason)
(0011 пояснити-міркування reason-explain)

; Unification
(0011 уніфікувати unify)
(0011 логічна-змінна logic-var)
(0011 змінна? var?)
(0011 підставити apply-subst)
(0011 розіменувати walk)
; Occurs-check є питанням t/(), тому preferred-назва має ?. Стара назва
; збережена як compatibility alias.
(0011 змінна-зустрічається? occurs-check)
(0011 перевірити-зустрічання occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Epistemic (status: stable)
;; Епістемічні структури
;; ═══════════════════════════════════════════════════════════════

(0011 твердження? claim?)
(0011 зміст-твердження claim-statement)
(0011 стан-розгляду-твердження claim-review)
(0011 доказ? evidence?)
(0011 метод-доказу evidence-method)
(0011 результат-доказу evidence-outcome)
(0011 спостереження? observation?)
(0011 зміст-спостереження observation-statement)
(0011 намір? intent?)
(0011 мета-наміру intent-goal)
(0011 підтримувальний-доказ supporting-evidence)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Missing UK fill (status: stable)
;; ═══════════════════════════════════════════════════════════════

(0011 генерувати-символ gensym)

;; ═══════════════════════════════════════════════════════════════
;; Сумісність назв після смислового аудиту 2026-09-08
;; Preferred-назви вище є основними для нових програм; старі назви
;; лишаються alias-ами тієї самої семантичної тотожності.
;; ═══════════════════════════════════════════════════════════════

; M8: compatibility aliases несуть exact SENS напряму.
; EN/UK людські імена лишаються boundary projections; alias value не відновлює
; runtime name authority ні для host primitive, ні для Lisp-owned callable.
(0011 текст-менше? 00100101)
(0011 за-номером 00101011)
(0011 перший-знак 00111111)
(0011 решта-знаків 01000000)
(0011 встановити-вектор! 01010011)
(0011 монотонний-час 01011010)
(0011 юнікс-із-спостереження 01100000)
(0011 часовий-пояс-назва 01100011)
(0011 часовий-пояс-виявити 01100100)
(0011 часовий-пояс-зміщення 01100101)
(0011 дедлайн-досягнуто-о? 01100111)
(0011 дедлайн-з 01101001)
(0011 інтернет-час-синхронізація 01101011)
(0011 карта-порожня 01101100)
(0011 карта-отримати 01101101)
(0011 карта-вставити 01101110)
(0011 вектор-порожній 01110001)
(0011 вектор-додати 01110010)
(0011 вектор-розмір 01110011)
(0011 вектор-за-номером 01110100)
(0011 вперед-висновок 01111011)
(0011 модуль-умови-зараз 01111111)
(0011 обґрунтувати-доведення 10000010)
(0011 міркування-пояснити 10000110)
(0011 відшукати 10001011)
(0011 твердження-текст 10001110)
(0011 твердження-відгук 10001111)
(0011 доказ-метод 10010001)
(0011 доказ-результат 10010010)
(0011 спостереження-текст 10010100)
(0011 намір-мета 10010110)
(0011 підтримуючий-доказ 10010111)

(0011 містить? 00101100)
(0011 текст-починається? 00111101)
(0011 містить-текст? 00111110)
(0011 код-у-текст 01000100)
(0011 текст-у-код 01000101)
(0011 у-текст 01001100)
(0011 юнікс-час-зараз 01011011)
(0011 дедлайн-після-нс 01101010)
(0011 карта-містить? 01101111)
(0011 містить-атом? 01111010)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — SA missing fill (Sanskrit surface for previously missing)
;; These are Sanskrit aliases loaded from uk.lisp context for reference.
;; The actual SA bindings are in sa.lisp; these UK lines ensure UK
;; coverage for gensym and env which were previously missing.
;; ═══════════════════════════════════════════════════════════════