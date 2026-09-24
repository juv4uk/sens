# CURRENT — де зараз живе чинна правда

Це точка входу для питання «що зараз чинне». Якщо старий документ, план, архів або агентський коментар суперечить джерелам нижче, перемагає цей порядок.

## Authority order

1. **`language-contract.lisp` Contract 9** — у мові є рівно 256 функцій `00000000..11111111`; самі 8 бітів є функціональною тотожністю.
2. **Standing invariant #1325 + executable guard #1331** — жодної другої named-function ontology, жодного `SID text/literal/spelling`, quoted/string/symbol wrapper або host label як функції.
3. **Lisp-owned Core contracts and executable conformance evidence** — вони визначають закони/результати над уже вибраними 8 бітами, але не створюють нових функціональних тотожностей.
4. **Reference runtime `crates/my-lisp`** — механізми виконання та перевірка conformance. Host/runtime може мати локальні таблиці й оптимізації, але вони не стають владою мови.
5. **Independent substrates** — FPGA, C, WASM, GraalVM, Common Lisp, Prolog, Datalog, CLIPS та інші механізми. Вони споживають уже вибрані 8 бітів.
6. **UI/source routing metadata** — людські підказки та локалізації можуть допомагати вводу, але не є функціями, meaning або semantic identity.
7. **Активні плани й task DAG** — `tasks.lisp`, `PLAN.md`, `STATUS.md` та явно чинні implementation plans.
8. **Tests/CI/evidence** — доводять поточний стан; claim без виконуваного доказу лишається гіпотезою.

## Що НЕ є функціональною владою

- слова, людські назви, локалізації, enum-мітки, opcode-и та backend-назви;
- історичні назви операцій;
- `docs/archive/**`, старі ADR/плани та археологічні звіти;
- generated docs;
- твердження агента без актуального executable evidence.

## Для нового агента

1. Прочитати `language-contract.lisp` і #1325.
2. Перевірити `scripts/sid8-only-ontology-guard.sh`.
3. У семантичному коді та документації позначати функції тільки точними 8 бітами.
4. Не створювати схему word/name → meaning → function.
5. Перед зміною runtime перевірити активні #1327/#1328/#1330/#1347 та сусідні PR.
6. Запустити відповідні tests/CI й доводити твердження результатом, а не назвою.

`docs/archive/**` зберігає історію, але не визначає сьогоднішню мову.
