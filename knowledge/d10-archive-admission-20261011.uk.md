# Партія наповнення D10: 647 → 651 (11.10.2026)

**Статус: SELECTED-RESEARCH / UNRATIFIED; D10 координати не призначено.** Замість нових дослідів відібрано 4 раніше готові source-grade архівні результати. Рішення власника «наповнюйте D10» дозволяє відібрати кандидати до дослідницького інвентарю, але не автоматичну ратифікацію чи runtime-opcode.

| Закон | Канонічне джерело в репозиторії | Збережений незалежний доказ |
|---|---|---|
| `EXACT-BARYCENTRIC-INTERPOLATE` | `knowledge/d10-exact-barycentric-interpolation-research-v1.json` | Python Fraction + незалежний Chez Scheme |
| `FINITE-SIMPLE-TEMPORAL-CLOSURE` | `knowledge/d10-finite-temporal-constraint-closure-v1.json` | Floyd–Warshall + Bellman–Ford + Z3 (збережений звіт) |
| `EXACT-BOOLEAN-PRIME-IMPLICANTS` | `knowledge/d10-quine-prime-implicants-20261009.json` | покомпонентне злиття Quine + незалежний перебір 3^n кубів |
| `BINARY-CONSTRAINT-SUPPORT-PROJECTION` | `knowledge/d10-symbolic-ai-arc-support-20261009.json` | Python 32768 випадків + SWI-Prolog 768 випадків (збережений звіт) |

## Облік переходу

- Основа: Git blob `7e13e929338baeef9b16c2139d24b78e23ea1e03`, 647/1024; 256 законом визначених координат, 391 без координати, залишок 377.
- Append: `d10.math.exact-barycentric-interpolate.20261011`, `d10.ai.finite-simple-temporal-closure.20261011`, `d10.logic.exact-boolean-prime-implicants.20261011`, `d10.ai.binary-constraint-support-projection.20261011`.
- Після відбору: 651/1024; 256 законом визначених координат, 395 відібраних без координат, залишок 373.
- Архівні 625 рядків збережено побайтно, попередні 12 переходів не переписано.
- Додано чотири `pending-review` у `knowledge/d10-proposal-ledger.tsv`, з SHA до цього переходу; жодних нових координат чи ратифікацій.
- Архівні JSON-досьє зберігають власний **історичний** статус NOT-SELECTED на момент написання. Це не заборона пізнішого source-linked append.

## Обмеження доказу

Підтверджені первинні джерела: [DLMF §3.3](https://dlmf.nist.gov/3.3), [Dechter–Meiri–Pearl 1991](https://doi.org/10.1016/0004-3702(91)90006-6), [Quine 1952](https://doi.org/10.2307/2262498), [Mackworth 1977](https://doi.org/10.1016/0004-3702(77)90007-8). Збережені в репозиторії перевірки містять незалежні реалізації, але **у цьому переході CI/реальні SBCL/Z3/SWI/Chez повторно ще не запущено**. Не видавати історичні PASS за поточний HEAD.

Поведеневий дедуп: прямого тотожного контракту серед відібраних D10 і ратифікованих D1–D9 не виявлено під час ревізії досьє/реєстру; кожний має окремий клас відношення, вхідні типи, вихідні свідки й негативні приклади. Семантична похідність (Core vs library) залишається **PENDING** та не означає ратифікації. Якщо незалежний регресійний тест знайде фактичний дублікат, цей перехід має бути відхилений, а не мовчки допущений.

Незмінні: канонічний D1–D9, D2 структурна влада, фізичний кодек `.sens`, всі Rust runtime semantics. Тільки дослідний append + леджер + стан + документаційна проєкція.
