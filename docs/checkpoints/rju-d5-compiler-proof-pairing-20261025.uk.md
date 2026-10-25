# Ṛju · 25.10.2026 · Д5/D3 compiler REVERSE-ONTO: доказовий закон і мутант

## Аватар і спадкоємність
Ṛju означає прямий та точний шлях. Дякую Nyāya та Pramāṇa: закон компіляторного `компілятор-зворот-до` уже став SENS-кодом та був доданий до фізичного proof-runner. У цьому кроці семантичне тіло не змінюється; виправляється прихований борг перевірки володіння тестами.

## Підтверджений запуск попереднього кроку
За GitHub Actions `40145070483`, exact SHA `d379de70df1d875a2bd0aedd3ba83e91f60d32e3`:
- `compiler-reverse-onto-positive`: PASS, D1:1, нативний SENS.
- `compiler-reverse-onto-order-mutant`: PASS, D1:0, нативний SENS.
- `compiler-reverse-onto-d1-root-type`: PASS, точне `car expects a non-empty list` у direct/paired/standalone.
- `compiler-reverse-onto-improper-tail-type`: PASS, та сама очікувана CAR Type у direct/paired/standalone.

Водночас єдиний CI попереднього SHA — FAILURE, не успіх всього релізу.

## Знайдена першопричина охоронця
Охоронець `scripts/guard_native_semantic_ownership.py` перевіряє інваріант одного стебла:
`*-law.lisp` ↔ `*-mutant.lisp`. Для раніше створеного `compiler-reverse-onto-order-mutant.lisp` позитив `compiler-reverse-onto-order-law.lisp` був відсутній, хоча тотожний за сценарієм позитив уже існував під назвою `compiler-reverse-onto-proper-law.lisp`. CI дав:
`SENS_LAW_POSITIVE_MISSING source=tests/semantic/compiler-reverse-onto-order-mutant.lisp`.

Виправлення — тільки перенесення існуючого SENS-негативу без зміни тіла до `compiler-reverse-onto-proper-mutant.lisp` та оновлення джерельного маршруту в runner. Не створювати дубль позитиву й не послаблювати охоронець.

## Контракт
- D3: лише `()` є структурним кінцем, D1:ні у хвості => CAR Type.
- Позитив перевіряє `D1:так`, мутант — `D1:ні`, обидва використовують реальні DEFINE SENS без Rust/Python-оракула.
- Оригінальний `lib/compiler-nucleus.lisp` незмінний, координати Д1–Д12+ незмінні.
- Для зміненої назви runner генерує лише тимчасові фізичні артефакти через чинний mint/open/verify — ніяких сфальшованих бітів.

## Статус та наступні цілі
- Власність закону/мутанта: STATIC_STRUCTURE_FIXED; новий native CI ще має перевірити саме цей SHA.
- RELEASE: NO-GO.
- Д6 `довжина-до` на попередньому CI: direct `cdr expects a non-empty list` замість очікуваного `car expects a non-empty list`. Вихідний Core4 SENS визначає саме `(перше значення)` для неправильного атомного хвоста; потрібна перевірка runtime-resolution D6 та stale фізичного `lib/core4.sens`, а не заміна CAR на CDR у свідку.
- Також лишаються окремі проблеми D10 UnknownSymbol, D11 T5M-біндинги, D12 фізична драбина й непідтверджені кандидати каталогу.
- Наступний агент перевіряє exact CI цього коміту, потім ізолює D6 джерело/DEFINE/фізичний маршрут та складає точні позитив/мутант/Type відмови. Не оголошувати GO без власника.
