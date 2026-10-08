# D10 — самохостинг Lisp-машини та логічні докази: семантичні кандидати

**Статус:** RESEARCH / UNRATIFIED. **Контракт:** #4013, #4162, #4463.

## Призначення

У перспективі `wsm-os-lisp` повинен стати живою Lisp-машиною, а не лише завантажувачем одного виразу. Тому наступне наповнення D10 відновлює значення, **які вже визначені в наших реальних Lisp-бібліотеках**: лексична розв'язка імен, параметри/решта, явні наслідки обчислення, взаєморекурсивні замикання, доведення та спостереження за доказами.

Джерело: `lib/meta-eval.lisp` та `lib/reason.lisp` (точні pinned Git blob SHA і source-line у JSON). Це НЕ декларація, що Interlisp/CADR/Genera реалізовували ці конкретні функції під такими самими назвами; історична відповідність потребує окремого дослідження.

## Облік

| Поле | Значення |
|---|---:|
| Було | 602 |
| Відібрано | +23 |
| Стало | 625/1024 |
| Залишилося | 399 |
| Теоремно розміщені селектори | 256 (не змінювалися) |
| Без координат | 369 |
| Ратифікація D10 | 0 |

## Нові значення

### STRUCTURED-ERROR

- **MY-ERROR** — Construct a finite Lisp data record with distinct error kind and detail fields  (`lib/meta-eval.lisp:27`)

### LEXICAL-LOOKUP

- **ENV-LOOKUP** — Resolve an identifier with canonical identity precedence, shared top-level frame visibility and lexical shadowing  (`lib/meta-eval.lisp:265`)
- **MY-UNRESOLVED-NAME?** — Recognize an unresolved symbol reference while excluding valid canonical names, primitive identities and quoted symbol values  (`lib/meta-eval.lisp:307`)

### SOURCE-FORM

- **MY-LAMBDA-FORM?** — Recognize a lambda-headed source form while excluding nonlist operators and invalid head shapes  (`lib/meta-eval.lisp:359`)
- **MY-LAMBDA-DEF-FORM?** — Recognize a top-level named definition whose initializer is a lambda form, for finite recursion grouping  (`lib/meta-eval.lisp:368`)

### COMPARISON-LAW

- **MY-COMPARE-CHAIN** — Test an ordered series of evaluated values pairwise under one comparison identity, stopping at first false pair  (`lib/meta-eval.lisp:405`)

### PARAMETER-LAW

- **MY-FIXED-PARAM-COUNT** — Count required parameters in a proper or dotted lambda parameter list, excluding the rest binding  (`lib/meta-eval.lisp:441`)
- **MY-REST-PARAM?** — Detect a dotted tail or symbol-only rest parameter from the lambda parameter structure  (`lib/meta-eval.lisp:448`)
- **BIND-PARAMS** — Bind already admitted argument values into an environment, including a rest-parameter binding to the remaining list  (`lib/meta-eval.lisp:587`)

### RESULT-EVALUATION

- **MY-EVAL-LIST-RESULT** — Evaluate an argument list from left to right and return a tagged success list or the first failure without evaluating later arguments  (`lib/meta-eval.lisp:599`)
- **MY-EVAL-BODY-RESULT** — Evaluate body forms in order, returning only the final successful result or the first failed evaluation  (`lib/meta-eval.lisp:622`)

### LEXICAL-SHADOWING

- **MY-PARAMS-BIND-NAME?** — Check whether a formal parameter list binds a candidate name including dotted rest position  (`lib/meta-eval.lisp:1033`)
- **MY-FORM-REFERENCES-NAME?** — Detect a reference to an identifier in a Lisp source form while excluding quoted data and nested lambda shadows  (`lib/meta-eval.lisp:1055`)

### DEFINITION-GRAPH

- **MY-SELECT-DEFS-BY-NAMES** — Retain a source-ordered subset of lambda definitions named by a finite group of identifiers  (`lib/meta-eval.lisp:1180`)
- **MY-REMOVE-DEFS-BY-NAMES** — Return remaining lambda-definition forms after excluding all forms whose defined name belongs to a chosen component  (`lib/meta-eval.lisp:1190`)

### CLOSURE-GROUP

- **MY-GROUP-CLOSURE-FROM-DEF** — Construct a finite group-recursive closure from one definition, member group and captured lexical environment  (`lib/meta-eval.lisp:724`)
- **MY-BUILD-GROUP-ENV** — Reconstruct group member closure bindings around the captured environment at application time without relying on cyclic host references  (`lib/meta-eval.lisp:752`)

### LOGIC-SCOPING

- **RENAME-VARS** — Rename logic variables in a compound rule with the current proof depth to prevent accidental capture during rule application  (`lib/reason.lisp:226`)

### LOGIC-PROOF

- **PROVE-RULE** — Rename the selected rule, unify its head with a goal, recursively prove its body and attach provenance to every successful substitution  (`lib/reason.lisp:243`)
- **PROVE-GOAL-STATE** — Extend an existing proof-state substitution and proof list by attempting a goal through admitted indexed or linear rules  (`lib/reason.lisp:281`)
- **MAP-GOAL-RESULTS** — Combine every successful goal substitution with the accumulated proof-node sequence without dropping source order  (`lib/reason.lisp:295`)

### PROOF-OBSERVATION

- **COUNT-USAGE** — Count how many times each proof rule occurs in a nested provenance tree, returning a finite rule-count association list  (`lib/reason.lisp:385`)
- **MERGE-USAGE** — Merge two finite per-rule occurrence tables by adding counts of equal rule identifiers  (`lib/reason.lisp:378`)

## Що свідомо не додаємо

- `REASON-MAKE-INDEX` — Optimization/indexing mechanism: source rule scan must be semantically identical to indexed evaluation
- `REASON-INDEX-CANDIDATES` — Optimization/access path, no additional observable proof law
- `MY-APPLY` — Unwraps MY-APPLY-RESULT, not a new result semantics
- `MY-EVAL` — Unwraps MY-EVAL-RESULT, already selected
- `MY-COND-HAS-MIGRATION-CLAUSE?` — Legacy migration-mode adapter, not stable domain law
- `VTREE-GET` — Representation-specific index AVL helper; public VEC-NTH already lower-domain resident
- `MY-PRIMITIVE` — Internal wrapper constructor; requires equivalence review against existing primitive identity laws

## Інваріанти

1. Основна ідентичність мови досі **точний двійковий код + домен + доведений закон**; human names тут лише пояснення дослідницького реєстру.
2. D10 — **єдиний глобальний потік**, не 23 окремі “слоти” пакетів.
3. Усі нові `coordinate=null`, `ratified_resident=false`, власник вирішує їхній остаточний статус.
4. Неприпустимо міняти вже ратифіковані D1–D9 або підмішувати механізми індексу, LLVM, АВІ, драйвери й мікрокод у Core.
5. Перед ратифікацією потрібні виконувані parity-приклади: lexically shadowed name, dotted parameters, short-circuit error, recursive closure, capture-free rename, multi-proof provenance, proof usage totals.

## CI gate

```sh
python3 scripts/check-d10-selfhost-reason-harvest-v1.py
python3 scripts/check-d10-v1-semantic-inventory.py
python3 scripts/check-d10-fill-v1-seed.py
```

Перевірка реєстру доводить джерело та відсутність дублювання **за іменами**, а не доведення поведінкової еквівалентності семантик. Остання лишається відкритою до оракульних тестів та власникового review.
