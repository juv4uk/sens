# Sūtradhāra (सूत्रधार) · Архітектурний checkpoint D1–D12+ · 25.10.2026

## Базовий стан
- Гілка: `main`, без окремої гілки.
- SHA перед цим checkpoint: `ffa2458ba467d9233fa025a3ab6c24bdbdae82c3`.
- Реліз: `NO-GO`; фізична викличність усіх заявлених D1–D12+ резидентів не доведена.

## Підтверджені факти
1. Host-debt guard: CI `40159882499` на SHA `f4590f40ec54cd5fdd560f091de8c78710ca25c1` підтвердив крок 4 як SUCCESS. Це guard fix, не дозвіл релізу; новіший SHA має власний CI.
2. D12 selected transport: старий run `40158590271` на SHA `7f8dbf863edaf12714234f55dfbd663cb1b77b5d` дав `16 passed; 0 failed` для набору `sens-math-t5m`. Це не покриття кожної функції D12+ і не повна матриця named-input Lisp-законів.
3. D11 LIST=: коміти `fd2e6005` і `a3e8d7c7` розділяють Type-відмову та D1:ні. Актуальний CI цих змін треба перевірити після завершення.
4. D4/D6: п'ять пар `.sens.b64`/`.view.b64` є в `knowledge/d11/restore/udyoga/`. Mint/наявність файлу не є фізичним PASS.

## Відкриті першопричини
- F6 producer → consumer: старий CI `40158590271` показав RED `root reconstruction rejected: 0`. Перевірити правильність точних D4/D9 SENS викликів і бібліотечних визначень; не змінювати очікування на D1:ні.
- D11 LIST=: неправильна D3-структура повинна дати Type-відмову, не бути замаскована як D1:ні.
- D6 LET/LET*: старий RED показував D3 COND arity замість очікуваного D3 CAR Type до macro expansion. Перевірити актуальну фізичну пару Core4 і порядок валідації, не послаблювати COND.
- D12 named bounds: probe у Rust-драйвері не є окремим SENS-законом; знайти мовний шлях exact-domain межових значень без сирих десяткових літералів у виконуваних Lisp.
- D10/D12+: потрібна матриця `domain bits → SENS definition → positive → mutant → invalid-input/Type → native CI` на одному SHA.

## Наступне ТЗ Swarm-агенту
1. Перевірити завершений CI найновішого `main`, записати run ID, exact SHA, failed step та реальні діагностики.
2. Підтвердити host-debt guard на цьому SHA; не додавати нові хост-файли до legacy allowlist.
3. Закрити першопричину за фактичним RED, не за припущенням; пріоритет — D11 LIST= / D9 STRING-APPEND, потім F6 root reconstruction, потім Core4 malformed D6 bindings.
4. Семантику змінювати в SENS/Lisp; Rust має перевіряти механізм/транспорт, Zig — байтову точність. Не вводити host semantic oracle, SID8/Sens8 fallback чи compatibility layer.
5. Відновити всі п'ять D4/D6 пар і виконати їх через нативний шлях; зберегти source/blob SHA, round-trip, SENS verdict, mutant і Type-negative.
6. Для D10 резидентів створювати реєстр доказів. Не рахувати число координат як число викличних функцій. Commit/push прямо в `main` з expected-head guard, без force-push.

`HOST_DEBT_GUARD=PASS_ON_SHA_f4590; NEWER_SHA_PENDING`
`D12_SELECTED_TRANSPORT=16_PASS_ON_SHA_7f8dbf8; FULL_RESIDENT_MATRIX=OPEN`
`D11_LIST_EQUALITY_LATEST_NATIVE_RESULT=PENDING`
`F6_ROOT_RECONSTRUCTION=RED_ON_OLD_SHA; ROOT_CAUSE_OPEN`
`D4_D6_RESTORATION_PAIRS=PRESENT; PHYSICAL_EXECUTION=NOT_CERTIFIED`
`D10_FULL_PHYSICAL_EXECUTION=NOT_VERIFIED`
`D1_D12_PLUS_RELEASE=NO_GO`