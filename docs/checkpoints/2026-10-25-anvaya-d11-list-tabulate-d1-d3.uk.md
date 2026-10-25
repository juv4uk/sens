# Anvaya (अन्वय): D11 LIST-TABULATE, збереження елементів D1/D3

Дата: 25.10.2026. Область: D1–D12+ через одну перевірену родину
D11 з чинними законами D3/D4/D5/D6. Мета агента — не кількість
комітів, а доведене співпадіння SENS-закону з нативним виконанням.

## Спадкоємність

Дякую Viveka за D10 MAP, Satya за D9 STRING-APPEND,
Ṛta за CLIPS та колегам, які розвивають D11.
Свіжий main на початку ходу:
`6ab47990fb6255d32039bdba6e8263f97b02950c`.

У попередньому завершеному CI `40159975168`, SHA
`3a89acef006be319b581dffec24807f78be38297`,
падає `producer_records_are_reconstructed_by_the_physical_f6_consumer`:
`root reconstruction rejected: 0`; це старий SHA.
Див. також `40159918382`: 1 з 2 тестів F6 падає,
2-й malformed-record контроль PASS.
Після цього власні колеги змінили символ `accepted`
у F6 consumer і відновили фізичні пакети FS, тож НЕ
стверджувати, що той самий дефект зберігся в актуальному
main без нового журналу. Нові CI мають чергу.

## Функція та її семантика

Функція D11 — кандидат SRFI-1 `табулювати-список`,
вже реалізована колегою в
`lib/d11-srfi1-list-tabulate.lisp`.

Закон: невід'ємна ціла кількість D24+ `n`,
першокласна SENS-функція `f` → власний правильний
D3-список `(f(0), ..., f(n-1))`. Нуль створює
`()` і не викликає callback. Для ненульової
кількості D1:ні й D3:() як **значення елементів**
не дорівнюють термінатору зовнішнього списку.
Невалідна кількість дає D3 Type до callback.
Внутрішня реалізація використовує D5 `додати`,
D3 `сполучити`, D6 `зворот` та D2/3 `за-умовою`;
ніяких нових D11 opcode або Rust семантики.

Важливе уточнення: у репозиторії вже був окремий
`tests/semantic/d11-srfi1-list-tabulate-values-law.lisp`,
який перевіряє значення D1:ні та D3:(). Це НЕ
нова непокрита функція. Цей хід зміцнює **інший**
позитив зі збереженням одночасної перевірки індексів
і додає незалежну перевірку-мутант, тож доказові
шляхи не можна видати за першу реалізацію.

## Реальні коміти з push у main

1. `1206a95d99a3a563a6a290a55ea456fe4eca1334`:
   `tests/semantic/d11-srfi1-list-tabulate-law.lisp` —
   розширено початкову спільну D1-позитивну форму.
   Перевіряє D24 індекси нуль, один, два, точний
   кінець після трьох елементів, порожній вхід
   з callback, який при виклику кинув би D3 Type,
   а також один D1:ні й один D3:() як елементи
   правильного одноелементного зовнішнього списку.
   Вся перевірка має єдиний D1 вердикт;
   перевірено баланс SENS-дужок.
2. `26f9aa4dbec8588961a85080a6e8eca613839752`:
   новий
   `tests/semantic/d11-srfi1-list-tabulate-empty-element-mutant.lisp`:
   хибна теза
   `(порожній? (табулювати-список число-один
   (функція (номер) (як-є ()))))`
   мусить повернути точний D1:ні. Це незалежно
   ловить помилку, що внутрішній елемент `()`
   завершує зовнішній список.
3. `72c11485d536fcdf748def4c640043647a145bb9`:
   додано `d11-list-tabulate-empty-element-mutant`
   з очікуванням D1:ні до наявного
   `scripts/prove-lisp-semantic-t5m.sh`, профіль
   `core4`. Еталонний шлях:
   direct SENS → Zig/T5M mint/open/verify →
   paired SENS → standalone фізичний SENS.
   Наявний `tests/semantic/d11-srfi1-list-tabulate-*.lisp`
   SHA256 glob уже охоплює новий мутант.
   Жодного додаткового workflow чи Python oracle.

Вміст файлів повторно перевірений GitHub fetch на SHA
`72c11485d536fcdf748def4c640043647a145bb9`.
CI цього commit: `40161244647` — queued на момент аудиту.
Не називати закон PASS до фактичного завершення SENS.

## Архітектурний статус D1–D12+

- D1 — точна істина/хиба; D2 — керування;
  D3 — `()`, cons, car, cdr, atom, eq, cond;
  D4 — lambda, list, macro та похідні;
  D5 — арифметичні дії над явними D24+;
  D6 — reverse і похідні обходи;
  D7 — клавіатурні текстові клітинки;
  D8/D9 — лише наявні явно допущені функції;
  D10 — 1024/1024 ратифіковані *ідентичності*,
  це не 1024 доведені викличні функції;
  D11 — каталог кандидатів, кожен потребує
  власного SENS-механізму;
  D12+ — числа, а не неявні літерали у коді.
- Розрізняти `source-defined`,
  `physical-reminted`, `native-proven`
  та `owner-release-approved` без підміни.
- Граф залежностей конкретного кроку:
  D1 verdict / D2 керування → D3 спискова структура →
  D4 першокласна функція → D5 D24 індекс →
  D6 зворот → D11 табуляція → Zig/T5M носій.
- Відокремлювати SENS Type від D1:ні:
  неправильний D3 хвіст — помилка, не хибна гіпотеза.

## Наступному Swarm-агенту: P0–P1

P0. На одному стабільному candidate SHA перевірити
повний комплект D11 LIST-TABULATE:
`d11-list-tabulate-law`,
`d11-list-tabulate-values-law`,
`d11-list-tabulate-mutant`,
`d11-list-tabulate-empty-element-mutant`
та `d11-list-tabulate-d1-count`,
`d11-list-tabulate-negative-count`,
`d11-list-tabulate-fraction-count`.
Виконати direct, paired, standalone на реальних
SENS і Zig/T5M, зберегти джерело й фізичні SHA.
Позитив: D1 так; мутанти: D1 ні; погані
кількості: точний Type. Не змінювати expected
для прикрашання CI.

P0. F6: перевірити після коміту
`938a7b2593c69935b3b4558fcd0274a97c07bee1`
та remint FS `907504ec0fea9cce1a819671d74db1b02f9051bf`.
Якщо `root reconstruction rejected: 0` зберігається,
простежити точний D3/D7 статус `accepted`, адреси,
оболонки та результат `фс-відновити-корінь` у SENS,
не обходити відхилення Rust-контролем.

P0. Д10 MAP після Viveka: усі 12 законів мають
один позитивний D1, один мутант D1:ні і чинний
Zig/T5M маршрут; перевірити результат, а не тільки
присутність `run_case`. Д11 LIST= й D9
STRING-APPEND теж потребують нових фізичних квитанцій.

P0. Порівняти `lib/core4.lisp` та точний фізичний
`lib/core4.sens` на одному SHA, штатним канонічним
remint; зберегти фізичні hash receipts.
Не робити ручний копіпаст бітових форм.

P1. D11 LIST-TABULATE: після нативного PASS
перевірити, чи потрібне фізичне джерело
`lib/d11-srfi1-list-tabulate.sens` як окремий
канонічно змінтований артефакт, чи достатньо
здійсненого bundled T5M proof. Далі брати
наступний непокритий D11 кандидат лише з
історичним джерелом та без дублювання D1–D10.

`SENS_SOURCE=tests/semantic/d11-srfi1-list-tabulate-law.lisp`
`NATIVE_SENS_POSITIVE=NOT_VERIFIED`
`NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
`PHYSICAL_SHA_PAIR=NOT_VERIFIED_ON_CURRENT_MAIN`
`RELEASE=NO-GO`

---
Deutsch: Die D11-LIST-TABULATE-Beweise prüfen D1:nein und D3:()
als gültige Listenelemente. Die nativen Ergebnisse fehlen noch.

English: D11 LIST-TABULATE now has a strengthened shared positive
and an independent empty-element mutant. Real SENS/Zig/T5M
execution on the current SHA remains unverified.
