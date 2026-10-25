# Viveka (विवेक) — D11 FREQUENCIES: відновити причинний нативний доказ

Дата: 25.10.2026. Принцип: тільки SENS є семантичним оракулом; script є маршрутом Zig/T5M, не мовним виконавцем.

## Діагностовані першопричини

Раніше Nyāya виправив `lib/d11-clojure-frequencies-unary.lisp` через виклик
`підтвердити-список-для-групування` із `lib/d11-clojure-group-by.lisp`.

Фізичний CI точного SHA `8481eaa2c99a378e281938c3f21c6c255898a6d3`
[run 40147829152](https://github.com/juv4uk/sens/actions/runs/40147829152)
виявив:
- `SENS_LAW_NOT_REGISTERED` для двох нових `tests/semantic/d11-frequencies-outer-*`.
- `SENS_LAW_MUTANT_MISSING` для `d11-frequencies-outer-preflight-d1-law.lisp`.
- `d11-frequencies-unary-positive` та `d11-frequencies-improper-groups-type`
  відхилені через `unknown Text7 binding` замість SENS-вердикту/Type.
- Додатково `T5M_COMMITTED_PAIR_DRIFT` і `T5M_COMMITTED_VIEW_DRIFT`
  для бібліотеки FREQUENCIES; фізичну пару НЕ можна вважати актуальною.
- Інші незалежні RED: D6 NTH/MAPLIST/MIN/MAX, D10 CLIPS, збіркові ворота.
  Цей коміт не підміняє їхні причини чи очікування.

Виявлена причина першого `unknown Text7 binding`: чинний proof-route
склеював тільки FREQUENCIES та law. Він не підключав GROUP-BY DEFINE,
попри використання SENS-валідатора з GROUP-BY.

## Виконана дельта

- В усіх чотирьох старих FREQUENCIES proof-пакетах GROUP-BY DEFINE
  тепер завантажуються ПЕРШИМИ, за ними FREQUENCIES DEFINE та SENS свідок.
- До існуючого `scripts/prove-lisp-semantic-t5m.sh` додані
  `d11-frequencies-outer-preflight-d1-positive` (D1:так),
  `d11-frequencies-outer-preflight-d1-mutant` (D1:ні),
  `d11-frequencies-outer-before-inner-type`
  (точно `car expects a non-empty list`).
- Створено справжній SENS мутант у
  `tests/semantic/d11-frequencies-outer-preflight-d1-mutant.lisp`.
- SHA256 input-receipts охоплюють обидва SENS бібліотечні джерела
  і всі свідки. Не створено нової CI процедури/runner, opcode або
  host-семантики. В інших SENS-функціях змін немає.

## Доказовий стан
- Статично перевірено коректну кількість маршрутів, наявність джерел,
  баланс SENS-форм нового мутанта.
- NATIVE_SENS_POSITIVE=NOT_VERIFIED_ON_NEW_SHA.
- NATIVE_SENS_MUTANT=NOT_VERIFIED_ON_NEW_SHA.
- NATIVE_SENS_CAR_TYPE=NOT_VERIFIED_ON_NEW_SHA.
- COMMITTED_T5M_PAIR=STALE_PENDING_NATIVE_MINT.
- RELEASE=l0.42.0:NO-GO (без рішення власника).

## Наступному Swarm
1. На одному SHA переглянути `SENS_LAW_*result` для всіх FREQUENCIES
   (старі й нові). Лише буквальний SENS Type правильного шару є доказом.
2. Перегенерувати `lib/d11-clojure-frequencies-unary.sens` та
   `lib/d11-clojure-frequencies-unary` лише фізичним SENS/Zig T5M mint;
   звірити точні байти та `standalone` SENS.
3. Подивитися чи проходять D10 CLIPS та D6 NTH/MAPLIST/MIN/MAX,
   не приховувати RED та не перезапускати без виправлення.
4. Далі D3–D5 → D6–D8 → D10 → D11 → числовий D12 у єдиному
   доменному контракті; D7 лише текст і не заміна доменного коду.
5. Реліз NO-GO до фізично доведеного кандидата й ратифікації власника.
