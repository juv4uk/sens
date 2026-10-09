# D10 — живий Lisp evaluator для WSM-OS-LISP (research v1)

**Статус:** RESEARCH / UNRATIFIED. Немає жодної ратифікації чи нового двійкового коду.
**Підстава:** #4013, #4162, #4463.
**Підтверджена програмна реалізація:** `lib/meta-eval.lisp` та `lib/persistent-map.lisp` за точним SHA Git blob.

## Навіщо

Наша ціль — **жива Lisp-машина**, а не абстрактне заповнення домену. Після історичного огляду Interlisp-D, CADR, Genera, Scheme-79 і PSL відновлюємо в D10 *вже наявну у власних бібліотеках* семантику: стани evaluator, лексичні кадри та замикання, залежності функцій і персистентні структури.

**Межа доказу:** історичні машини тут є архітектурними паралелями, **не джерелом коду цих 31 кандидатів**. Зіставлення із історичними manual/spec конкретних операцій залишено для наступного аудиту. Джерелом рядків є точні локальні файли. Автоматична перевірка доводить наявність визначень та унікальність назв, але не доводить поведінкову еквівалентність, performance чи апаратну реалізацію.

## Результат

- Було: **558/1024**.
- Додано: **31 окремих дослідницьких кандидатів**.
- Стало: **589/1024**; залишилося **435**.
- Координати: **256** законних selector children (без змін); **333** відібраних без координат.
- Ратифіковано D10: **0**.

### OUTCOME-LAW (3)\n\n- `MY-RESULT-OK` ← `lib/meta-eval.lisp:49` — Construct an explicit successful metaevaluator result cell carrying its value\n- `MY-RESULT-FAIL` ← `lib/meta-eval.lisp:45` — Construct an explicit failure result cell carrying an error, distinct from a successful empty value\n- `MY-RESULT-FAIL?` ← `lib/meta-eval.lisp:49` — Recognize a tagged failure outcome without mistaking a successful empty result for an error

### LEXICAL-FRAME-LAW (5)\n\n- `MY-FRAME-BOUND?` ← `lib/meta-eval.lisp:233` — Test whether an identifier is locally bound within the supplied frame alist\n- `MY-FRAME-LOOKUP` ← `lib/meta-eval.lisp:194` — Retrieve the value of a named binding in the supplied frame alist\n- `MY-ENV-DEFINE` ← `lib/meta-eval.lisp:248` — Extend an ordinary lexical environment or update its finite shared definition frame\n- `ENV-BOUND?` ← `lib/meta-eval.lisp:281` — Check whether a name is bound through the evaluator's canonical and lexical environment rules\n- `MY-REFRESH-SHARED-FRAME` ← `lib/meta-eval.lisp:233` — Refresh the shared top-level definition frame of a captured environment from the caller while preserving lexical bindings

### CLOSURE-LAW (4)\n\n- `MY-CLOSURE?` ← `lib/meta-eval.lisp:561` — Recognize the evaluator's ordinary lexical closure representation\n- `MY-RECURSIVE-CLOSURE?` ← `lib/meta-eval.lisp:339` — Recognize a finite self-recursive closure with reconstructed self-binding at application\n- `MY-GROUP-CLOSURE?` ← `lib/meta-eval.lisp:352` — Recognize a finite mutually recursive group closure with shared group definitions\n- `MY-MAKE-CLOSURE` ← `lib/meta-eval.lisp:561` — Build a lexical closure if its parameter list is valid or return a structured error

### APPLICATION-LAW (4)\n\n- `MY-ARITY-OK?` ← `lib/meta-eval.lisp:782` — Validate exact or minimum argument cardinality against fixed/rest lambda parameter structure\n- `MY-ARITY-DETAIL` ← `lib/meta-eval.lisp:473` — Produce a structured expected-vs-received arity observation including rest-parameter mode\n- `MY-LAMBDA-LIST-ERROR` ← `lib/meta-eval.lisp:534` — Classify malformed lambda parameters, duplicate names, non-symbols and forbidden canonical bindings\n- `MY-APPLY-RESULT` ← `lib/meta-eval.lisp:784` — Apply primitive, lexical, self-recursive or mutually recursive callable with explicit success/error result

### EVALUATION-LAW (3)\n\n- `MY-EVAL-RESULT` ← `lib/meta-eval.lisp:1260` — Evaluate a form using the metaevaluator's structured successful or failed observation semantics\n- `MY-EVAL-TOP-FORM` ← `lib/meta-eval.lisp:975` — Evaluate a top-level definition or expression, returning the threaded environment and value\n- `MY-EVAL-PROGRAM` ← `lib/meta-eval.lisp:1262` — Evaluate a sequence of top-level forms with shared-frame definitions and dependency-aware recursive groups

### DEFINITION-GRAPH-LAW (7)\n\n- `MY-DEF-DEPENDENCIES` ← `lib/meta-eval.lisp:1081` — Select names referenced freely by one definition from a finite candidate set\n- `MY-BUILD-DEPENDENCY-GRAPH` ← `lib/meta-eval.lisp:1120` — Build a graph mapping each top-level lambda definition name to dependencies in its definition block\n- `MY-GRAPH-REACHES?` ← `lib/meta-eval.lisp:1152` — Decide finite directed reachability across definition dependencies using a visited set\n- `MY-SCC-NAMES` ← `lib/meta-eval.lisp:1163` — Compute the group of names mutually reachable with a selected definition, retaining singletons\n- `MY-EVAL-LAMBDA-BLOCK` ← `lib/meta-eval.lisp:1245` — Evaluate one contiguous lambda-definition block by dependency graph and strongly connected components\n- `MY-INSTALL-GROUP-ENV` ← `lib/meta-eval.lisp:774` — Install all mutually recursive closures as finite bindings in a shared definition environment\n- `MY-LAMBDA-DEF-REFERENCES-NAME?` ← `lib/meta-eval.lisp:1083` — Recognize a free reference in a lambda definition while respecting nested parameter shadowing and quoted forms

### PERSISTENT-AVL-LAW (5)\n\n- `AVL-MAKE-BALANCED-NODE` ← `lib/persistent-map.lisp:82` — Construct a persistent AVL node with height derived from child heights\n- `AVL-BALANCE-FACTOR` ← `lib/persistent-map.lisp:86` — Calculate left subtree height minus right subtree height of a persistent AVL node\n- `AVL-ROTATE-LEFT` ← `lib/persistent-map.lisp:89` — Perform an AVL left rotation returning a new structurally shared tree\n- `AVL-ROTATE-RIGHT` ← `lib/persistent-map.lisp:96` — Perform an AVL right rotation returning a new structurally shared tree\n- `AVL-REBALANCE` ← `lib/persistent-map.lisp:109` — Restore AVL height-balance invariant using single or double rotations after a node update

## Явно НЕ добираємо

- `lib/meta-eval.lisp` `my-result-value`: PURE-PROJECTION: source function is exactly CDR on result pair
- `lib/meta-eval.lisp` `my-fourth`: PURE-ALIAS to existing fourth projection
- `lib/meta-eval.lisp` `my-cond-has-migration-clause?`: MIGRATION-SPECIFIC compatibility helper
- `lib/persistent-map.lisp` `node-left`: PURE-ALIAS to existing fourth
- `lib/persistent-map.lisp` `node-right`: PURE-ALIAS to existing fifth

- Переадресація `CAR/CDR` як нових слотів.
- Код machine ABI / UEFI / IRQ / allocator / PCI / FPGA microcode (це механізми таргета, не функції D10).
- Чужі історичні адреси, opcode й implementation identity.

## Контракти

1. Один глобальний потік D10, без окремих пакетних доменів.
2. Не дублювати точні значення D1–D9 чи вже відібрані D10.
3. `coordinate=null` для всіх нових кандидатів; усі `ratified_resident=false`.
4. Де поведінка ще вимагає порівняння, власник може відхилити конкретного кандидата незалежно від назви.
5. `wsm-os-lisp` володіє машинним виконанням; це дослідження не втручається у target ABI.
6. Пізніше додати runnable parity fixtures для closure/frame/arity/SCC і компіляції definitions.

## Перевірка

```sh
python3 scripts/check-d10-lisp-machine-evaluator-harvest-v1.py
python3 scripts/check-d10-v1-semantic-inventory.py
python3 scripts/check-d10-fill-v1-seed.py
```

Матеріали: `knowledge/d10-lisp-machine-evaluator-harvest-v1.json`.
