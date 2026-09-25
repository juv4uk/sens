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
(define істина t)
(define хиба (quote ()))

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Arithmetic (status: stable)
;; Арифметика
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 0104, 1001–1003: `додати`, `відняти`, `помножити`,
; `поділити`, їхні Sanskrit peers і symbolic notation встановлюються runtime
; напряму на ті самі callable values. Жодна людська поверхня не є мостом.
(define модуль abs)
(define найменше min)
(define найбільше max)
(define остача mod)
(define частка quotient)
(define корінь sqrt)
(define цілий-корінь isqrt)
(define найменше-у-списку min-list)
(define найбільше-у-списку max-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Comparisons (status: stable)
;; Порівняння
;; ═══════════════════════════════════════════════════════════════

; ADR-007/008 / 1014–1016: `менше?`, `більше?`, `рівне?`, їхні
; Sanskrit peers і symbolic notation є прямими runtime bindings.
(define не-більше? <=)
(define не-менше? >=)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Predicates (status: stable)
;; Предикати
;; ═══════════════════════════════════════════════════════════════

(define хибне? not)
(define однакові? equal?)
(define символ? symbol?)
(define текст? string?)
(define текст-передує? string<?)
(define числовий-буфер? numeric-buffer?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Lists (status: stable)
;; Списки
;; ═══════════════════════════════════════════════════════════════

(define список list)
(define довжина length)
(define приєднати append)
(define зворот reverse)
(define елемент-списку-за-індексом nth)
(define значення-у-списку? member?)
(define знайти-за-ключем assoc)
(define пара pair)
(define друге second)
(define третє third)
(define четверте fourth)
(define п'яте fifth)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Higher-order functions (status: stable)
;; Функції вищого порядку
;; ═══════════════════════════════════════════════════════════════

(define відобразити map)
(define відсіяти filter)
(define згорнути reduce)

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
(define текст-у-кодову-точку string->codepoint)
(define кодова-точка-у-текст codepoint->string)
(define число-у-текст number->string)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — I/O (status: stable)
;; Ввід/вивід
;; ═══════════════════════════════════════════════════════════════

(define друкувати print)
(define показати princ)
(define прочитати read)
(define прочитати-усе read-all)
(define значення-у-текст write-to-string)
(define обчислити eval)
(define середовище env)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Vectors (status: stable)
;; Вектори
;; ═══════════════════════════════════════════════════════════════

(define вектор vector)
(define створити-вектор make-vector)
(define довжина-вектора vector-length)
(define елемент-вектора vector-ref)

; vector-set! є мутацією — тому знак ! зберігається і в українській назві.
(define встановити-елемент-вектора! vector-set!)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Time (status: stable)
;; Час
;; ═══════════════════════════════════════════════════════════════

(define монотонний-нс mono-ns)
(define поточний-юнікс-час unix-time-now)

;; ═══════════════════════════════════════════════════════════════
;; Batch 1 — Other (status: stable)
;; Інше
;; ═══════════════════════════════════════════════════════════════

(define без-змін identity)
(define та and)
(define або or)
(define нехай let)
(define нехай* let*)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent map (status: stable)
;; Сталі асоціативні карти
;; User-facing API only; AVL internals (node-*, rotate-*, balance-*) excluded.
;; ═══════════════════════════════════════════════════════════════

(define порожня-карта map-empty)
(define отримати-з-карти map-get)
(define вставити-в-карту map-insert)
(define ключ-у-карті? map-contains?)
(define карта-у-список map->list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Persistent vector (status: stable)
;; Сталі вектори
;; User-facing API only; RRB-tree internals (vnode-*, vrotate-*, vbalance-*) excluded.
;; ═══════════════════════════════════════════════════════════════

(define порожній-вектор vec-empty)
(define додати-до-вектора vec-conj)
(define розмір-вектора vec-count)
(define елемент-вектора-за-індексом vec-nth)
(define вектор-у-список vec->list)
(define вектор-із-списку vec-from-list)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Time library (status: stable)
;; Бібліотека часу
;; ═══════════════════════════════════════════════════════════════

(define поточний-всч utc-now)
(define всч-із-юнікс utc-from-unix)
(define юнікс-спостереження-у-всч unix-time-observation->utc)
(define мілісекунди-із-наносекунд milliseconds-from-nanoseconds)
(define монотонний-мс mono-ms)
(define назва-часового-поясу timezone-name)
(define визначити-часовий-пояс timezone-detect)
(define зміщення-часового-поясу-в-секундах timezone-offset-seconds)
(define дедлайн-досягнуто? deadline-reached?)
(define дедлайн-досягнуто-на-момент? deadline-reached-at?)
(define минуло-нс elapsed-ns)
(define дедлайн-від deadline-from)
(define дедлайн-через-нс deadline-after-ns)
(define запитати-інтернет-час internet-time-sync)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Knowledge/Reasoning (status: stable)
;; База знань та логічний висновок
;; User-facing API only; indexing internals excluded.
;; ═══════════════════════════════════════════════════════════════

(define факт? is-fact?)
(define описати describe)
(define зібрати-факти-про collect-facts-about)
(define атом-у-списку? contains-atom?)
(define пряме-виведення forward-in)
(define логічний-висновок reason-in)
; Публічний предикат читається як питання; стара дієслівна назва лишається
; compatibility alias, щоб наявні українські програми не ламалися.
(define конфлікт? check-conflict)
(define перевірити-конфлікт check-conflict)
(define модуль-відомий? module-known?)
(define поточні-клаузи-модуля module-clauses-now)

; Reasoning engine
(define довести-мету prove-goal)
(define довести-мети prove-goals)
(define пояснити-доведення explain-proof)
(define джерело-доведення source-of)
(define походження provenance)
(define міркування reason)
(define пояснити-міркування reason-explain)

; Unification
(define уніфікувати unify)
(define логічна-змінна logic-var)
(define змінна? var?)
(define підставити apply-subst)
(define розіменувати walk)
; Occurs-check є питанням t/(), тому preferred-назва має ?. Стара назва
; збережена як compatibility alias.
(define змінна-зустрічається? occurs-check)
(define перевірити-зустрічання occurs-check)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Epistemic (status: stable)
;; Епістемічні структури
;; ═══════════════════════════════════════════════════════════════

(define твердження? claim?)
(define зміст-твердження claim-statement)
(define стан-розгляду-твердження claim-review)
(define доказ? evidence?)
(define метод-доказу evidence-method)
(define результат-доказу evidence-outcome)
(define спостереження? observation?)
(define зміст-спостереження observation-statement)
(define намір? intent?)
(define мета-наміру intent-goal)
(define підтримувальний-доказ supporting-evidence)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — Missing UK fill (status: stable)
;; ═══════════════════════════════════════════════════════════════

(define генерувати-символ gensym)

;; ═══════════════════════════════════════════════════════════════
;; Сумісність назв після смислового аудиту 2026-09-08
;; Preferred-назви вище є основними для нових програм; старі назви
;; лишаються alias-ами тієї самої семантичної тотожності.
;; ═══════════════════════════════════════════════════════════════

(define текст-менше? string<?)
(define за-номером nth)
(define перший-знак string-first)
(define решта-знаків string-rest)
(define встановити-вектор! vector-set!)
(define монотонний-час mono-ns)
(define юнікс-із-спостереження unix-time-observation->utc)
(define часовий-пояс-назва timezone-name)
(define часовий-пояс-виявити timezone-detect)
(define часовий-пояс-зміщення timezone-offset-seconds)
(define дедлайн-досягнуто-о? deadline-reached-at?)
(define дедлайн-з deadline-from)
(define інтернет-час-синхронізація internet-time-sync)
(define карта-порожня map-empty)
(define карта-отримати map-get)
(define карта-вставити map-insert)
(define вектор-порожній vec-empty)
(define вектор-додати vec-conj)
(define вектор-розмір vec-count)
(define вектор-за-номером vec-nth)
(define вперед-висновок forward-in)
(define модуль-умови-зараз module-clauses-now)
(define обґрунтувати-доведення explain-proof)
(define міркування-пояснити reason-explain)
(define відшукати walk)
(define твердження-текст claim-statement)
(define твердження-відгук claim-review)
(define доказ-метод evidence-method)
(define доказ-результат evidence-outcome)
(define спостереження-текст observation-statement)
(define намір-мета intent-goal)
(define підтримуючий-доказ supporting-evidence)

(define містить? member?)
(define текст-починається? string-prefix?)
(define містить-текст? string-contains?)
(define код-у-текст codepoint->string)
(define текст-у-код string->codepoint)
(define у-текст write-to-string)
(define юнікс-час-зараз unix-time-now)
(define дедлайн-після-нс deadline-after-ns)
(define карта-містить? map-contains?)
(define містить-атом? contains-atom?)

;; ═══════════════════════════════════════════════════════════════
;; Batch 2 — SA missing fill (Sanskrit surface for previously missing)
;; These are Sanskrit aliases loaded from uk.lisp context for reference.
;; The actual SA bindings are in sa.lisp; these UK lines ensure UK
;; coverage for gensym and env which were previously missing.
;; ═══════════════════════════════════════════════════════════════