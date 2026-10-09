# D10 — приймання пропозицій від заблокованої міграції

**Статус:** workflow / coordination, НЕ семантична authority. Завдання [#4463](https://github.com/juv4uk/sens/issues/4463). Актуальна влада: `language-contract.lisp`, ратифіковані D1–D9 і [Archipelago v1](ARCHIPELAGO-V1.uk.md). D10: research, **не ратифікований**.

## Коли запускати

У `.lisp → .sens` трипрохідний мігратор [#4450](https://github.com/juv4uk/sens/issues/4450) може знайти невідому функцію. Спочатку **BLOCK з точною причиною**: не створювати `.sens`, не вигадувати бінарний код і не підміняти значення D1–D9. Запис у цьому реєстрі ніколи не знімає BLOCK автоматично.

Далі з'ясувати, чи бракує справді універсального закону межі між Core та островом. Якщо це host I/O, механізм компілятора, ABI, register, backend, предметний алгоритм чи лише alias — функція лишається відповідному острову. Поява в історичному Lisp сама по собі не дає підстав додавати D10.

## Одне місце для заявок

`knowledge/d10-proposal-ledger.tsv` — **append-only** реєстр нерозглянутих заявок. Його рядок — *кандидат на розгляд*, не resident, не coordinate, не виконувана функція.

| Поле | Обов'язковий зміст |
|---|---|
| `proposal_id` | Унікальний `D10P-0001`, жодних повторних ID |
| `surface_uk`, `surface_ukr` | Українські читабельні написання; не англійська поверхня |
| `semantic_name`, `semantic_law` | Назва й конкретний закон поведінки; не alias і не opcode |
| `width` | Лише `D10` (пропозиція, без призначення 10-бітної координати) |
| `donor_provenance` | `owner/repo@COMMIT:path:line` для **реального** донора |
| `dedup_check` | `D1-D9@COMMIT=NO-MATCH;D10@COMMIT=NO-MATCH`; заявник перевіряє обидві частини проти поточного стану |
| `ownership_test` | `UNIVERSAL-BORDER: ...` з доказовим поясненням незалежності від субстрату |
| `blocked_source` | `owner/repo@COMMIT:path:line` реального BLOCK або `NO-MIGRATION-BLOCK` для словникового дослідження без зафіксованої зупинки міграції. Ніколи не вигадувати блокер. |
| `status`, `ratified` | Завжди `pending-review` та `0` у цьому реєстрі |

Журнал перевіряє лише схему, мітки стану, відсутність пустих полів і дублікатів **усередині журналу**. Сам по собі він НЕ підтверджує якість дедуплікації або закон; ці докази перевіряє рецензент.

## Обов'язковий зв'язок ledger ↔ вибраний D10

**Чинне машинне правило CI:** `scripts/check_d10_proposal_growth_gate.py` перевіряє `base → head` для кожного PR, що додає `knowledge/d10-v1-semantic-inventory.json`. Кожне **нове selected semantic_name** мусить мати існуючий або доданий в цьому PR **валідний** рядок `knowledge/d10-proposal-ledger.tsv`. Інакше CI повертає BLOCK. Старі selected rows та раніше записані ledger entries не можна редагувати/видаляти; нові строки додаються наприкінці. Додатково запускається `scripts/check_d10_selection_transition_history.py` для immutable 625-бази та git-blob SHA переходів. `pending-review` не означає `ratified` чи executable SENS.

**Борг архіву:** головна гілка вже містить п'ять дійсно selected research meanings `625→627→630` без рядків proposal ledger. Їхня історія є в `knowledge/d10-selection-transition-history.json`, а список чесно незаповнених пропозицій — у `knowledge/d10-ledger-backfill-audit-v1.json`. Backfill робиться окремим audit-PR *лише після* повного provenance/dedup, без фальшивих source SHA або уявного міграційного BLOCK. Нове правило не переписує цей історичний стан і не додає координат.

**Конституція tooling:** [D10-GUARD-GROWTH-DOCTRINE.uk.md](D10-GUARD-GROWTH-DOCTRINE.uk.md) — fail-closed перевірка зобов'язана мати доказовий append/extend маршрут замість вічної заборони на ріст.

## Як перевірити відсутність дубля

1. Закріпити SHA актуального `sens/main`, перевірити `lib/domains/d1.lisp` … `d9.lisp`: **значення**, закон, українські поверхні та alias. Відмітка `D1-D9@SHA=NO-MATCH` допустима лише після перевірки всіх дев'яти.
2. Перевірити обрані D10-кандидати з `knowledge/d10-*.json` (включно з consolidated inventory і provenance), `knowledge/d10-*` та документацію архіпелагу. Шукати не лише `semantic_name`, а й синоніми і **тотожну поведінку**. Поточний snapshot knowledge/d10-v1-semantic-inventory.json на main (blob 73dd518469f972c55411e004b70b054ba8b3ec86, 2026-10-09): **625/1024** вибраних research-кандидатів, **256** law-forced coordinates, **369** вибраних без координати, **399** ще не вибраних, **0** ратифікованих residents. Лічильник snapshot не є постійною константою.
3. Якщо перелік вибраних D10 неповний, інвентар суперечливий, або семантична тотожність неясна — **не писати NO-MATCH**, лишити джерело BLOCK і завести дослідницький review у #4463.
4. Лише за обох перевірених відсутностей, точного donor SHA, українських поверхонь та незалежного border law додати рядок зі статусом `pending-review`. Рішення й координату визначає **власник**, не агент.

Перевірка синтаксису журналу:

```sh
python3 scripts/check-d10-proposal-ledger.py
python3 scripts/check-d10-proposal-ledger.py --self-test
```

## Реальний перший BLOCK (не вигаданий кандидат)

[SENS #4458](https://github.com/juv4uk/sens/issues/4458) фіксує 75 блокувань історичного `print` у прогоні [37810152645](https://github.com/juv4uk/sens/actions/runs/37810152645). Це **доказ проблеми міграції, але ще не доказ універсального D10-закону**: можливо, це host I/O, допоміжний benchmark або nonprogram. Поки агент #4458 не встановив точне джерело/рядок, ефект і ownership, `print` **не отримує** рядок `pending-review`. Файл `.sens` лишається BLOCK. Це перший реальний triage case, а не синтетичний resident.

## D10 research queue: спершу мінімізувати корені, не наповнювати слоти

Координаційні джерела: [#4012 — глобальний D10 inventory](https://github.com/juv4uk/sens/issues/4012) і [#4182 — donor sweep усіх 87 репозиторіїв](https://github.com/juv4uk/sens/issues/4182); #4463 — лише fail-closed intake для реального міграційного BLOCK.

**625 назв/кандидатів ≠ 625 незалежних законів.** Поки немає доказу поведінкової незалежності, не створювати нові рядки в d10-proposal-ledger.tsv лише через нову назву, пакет або донор-репозиторій. Ідеї нижче — *черга дослідження*, не заявка, не resident і не координати D10.

Для кожної родини зберігати окремий evidence record з полями:
root_claim → observable_law → minimal_positive_witness → falsifiers → D1-D9 exact-behavior duplicate attack → D10 intra-family derivation attack → mechanism-only attack → minimal_irreducible_roots → coordinate=null.
Потрібні точні SHA/path/line кожного донора. Зіставляти реалізації за спостережуваним законом, а не за написанням. Якщо один корінь породжує інші через комбінацію вже доступних операторів, похідні не додають resident автоматично.

| Родина для дослідження | Мінімальний доказ, який потрібен перед пропозицією |
|---|---|
| Typed function-definition / introspection: PUTD, GETD, COPYD, REMD, FUNBOUNDP | Відокремити observable function-cell/namespace law від DEFINE + LAMBDA + LOOKUP; покрити redefine, відсутню функцію, копіювання, видалення та розрізнення функції й значення. |
| Reference-cell state: REF-CELL, DEREF, RESET-REF!, SWAP-REF!, predicate | Знайти мінімальний закон аліасованого стану й переходів. Не перетворювати п'ять surface-назв на п'ять коренів без негативних тестів на похідність. |
| Type-specifier algebra: TYPEP, TYPE-OF, SUBTYPEP, COERCE | Довести, що таке тип-специфікатор як мовне значення та які операції не виражаються іншими ратифікованими формами; тип host/Rust сам по собі не є доказом. |
| Persistent vector: VECTOR-EMPTY, VECTOR-NTH, VECTOR-CONJ | Перевірити порядок, індексацію, межі та незмінність попередньої версії після додавання; атакувати дублювання через списки/пари. FROM-LIST/TO-LIST — projection-кандидати, не автоматичні resident. |
| Control roots: CALL/CC, RETURN-FROM | Незалежні свідчення capture/resume/return та лексичної адресації цілі. Rust stack unwinding або runtime callback — механізм, не семантичний доказ; порівнювати з уже наявними control laws. |
| Map algebra vs mutable hash-table state | Спершу розділити персистентний mapping і мутабельну таблицю за спостережуваними законами оновлення, ідентичності та aliasing; однакова форма key/value не означає тотожної семантики. |
| Knowledge / proof graph | Відділити мовну семантику claim/evidence/observation та proof transition від validation, provenance storage, лічильників і tool bookkeeping; звести набір імен до мінімальних коренів. |

**Утримувати за механізмом, доки не з'явиться мовний закон:** port I/O (host/substrate boundary), READTABLE (parser hook без програмно спостережуваної конфігурації), UNDO (UI/history без формальної моделі стану), SEARCH (поки не атаковано дублювання послідовнісними операціями). Ці слова можуть бути корисними донорами evidence, але не дають автоматичного права на Core D10.

Блокер machine-block 1110 — це вже ratified D4 LIST без активованого Core4 callable path, а contextual Text7 — binding/representation seam. Жоден із них сам собою **не є D10-пропозицією**. Його ремонт — виправити runtime ownership і довести execution, не дублювати семантику в D10.

Метрика дослідницького прогресу: **кількість незалежних законів із пройденими позитивними та фальсифікаційними тестами**, не число відібраних назв. У цьому PR жодна з наведених родин не додається до ledger; усі координати лишаються null, ратифікація — 0.

## Межа відповідальності

- **Цей PR (#4463):** реєстр, протокол, локальна перевірка структури, cold-start підказка агентам.
- **Мігратор/кодек (#4450/#4451):** пізніше додають типізоване посилання `proposal_id` до BLOCK-звіту, лише якщо перевірений запис існує. Інакше BLOCK без ID. Не можна генерувати `pending-review` автоматично для кожного невідомого слова.
- **D10 owner:** review, dedup, ухвала. Навіть схвалений кандидат не є ратифікованим до явного рішення власника.

Ні цей документ, ні цей журнал не змінюють фізичний T5 `.sens`, структуру D2, семантику D1–D9 або релізні pins.
