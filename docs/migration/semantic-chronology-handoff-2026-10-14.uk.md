# Хронологія семантики SENS — доказовий handoff для міграційного рою

**Дата зрізу:** 14.10.2026. **Базовий `main` при початку огляду:** `f7ccc1c9bb80c489a6dc9f414e4f6c0421016b45`.
**Статус:** ненормативна робоча пам'ятка. Не є новою ратифікацією, схемою перетворення, gate, freeze, ані дозволом виконувати нерозміщені функції.
**Диспетчер:** [#5029](https://github.com/juv4uk/sens/issues/5029); окремий Zig T5 — [#5767](https://github.com/juv4uk/sens/issues/5767), незалежний паритет — [#5770](https://github.com/juv4uk/sens/issues/5770), вимірювання — [#5771](https://github.com/juv4uk/sens/issues/5771).

## Спочатку джерело закону, потім історія

1. Чинний машинний [`language-contract.lisp`](../../language-contract.lisp) — **Contract 11.9**. [`CURRENT.md`](../../CURRENT.md) веде до [таблиць D1–D10](../../lib/domains/) і ратифікацій; [`docs/semantic-authority-map.uk.md`](../semantic-authority-map.uk.md) пояснює пріоритети.
2. Закон ідентичності: **точне двійкове слово + точний домен + допущений/доведений закон**. Рівний машинний payload не означає рівних резидентів. `D1:1` ≠ `D2:01`; `D3:000` `()` ≠ D1 false і ≠ історичний нульовий восьмибітовий слот.
3. **Ратифікація резидента, доказ закону, виконавчий допуск, фізична підтримка носія та людське написання — різні факти.** Наявність D10-координати в T5 не робить її виконуваною. Семантично вирішує SENS; Zig, Rust, Python та апаратні механізми лише виконують і перевіряють носій.
4. Історична [`docs/language-core-axioms.md`](../language-core-axioms.md) прямо позначена **draft / not yet ratified** (09.08.2026); [`my-lisp-constitution.lisp`](../../my-lisp-constitution.lisp) — згенерована **draft-проєкція**. Не підміняти ними новішу ратифіковану доменну онтологію, хоч вони корисні для походження гіпотез.
5. Використовувати найновіші власницькі уточнення в [`AGENTS.md`](../../AGENTS.md), але жодному технічному виконавцю не привласнювати право приймати нові важливі семантичні чи архітектурні рішення. **CLAIM** у #5029 — факт конкретного виконавця та файлового write-set, не вигаданий «запущений агент».

## Датовані зміни — факти з `git log` і ратифікацій

| UTC / чинна дія | Commit / документ-першоджерело | Що насправді змінилося | Правило для перенесення |
|---|---|---|---|
| 24.09.2026 21:34 | [`fa42bdb69739`](https://github.com/juv4uk/sens/commit/fa42bdb69739) | Тодішній контракт декларував **один історичний восьмибітовий SID-простір** | Коректний опис *тієї епохи*, а не попередня карта чинного D8 |
| 29.09.2026 20:46 | [`07643eeb91cc`](https://github.com/juv4uk/sens/commit/07643eeb91cc) | Contract 10: загальний закон PredicateBit | Старі тести належить зіставляти із поточним D1, а не лише з host Bool |
| 03.10.2026 17:16 | [`320a389d0054`](https://github.com/juv4uk/sens/commit/320a389d0054) | Перехід контрактної семантичної влади до **exact domains** | Вісім фізичних бітів більше не є самостійним semantic ID |
| 04.10.2026 16:04 | [`804a938e2c5a`](https://github.com/juv4uk/sens/commit/804a938e2c5a) | D3 ратифіковано за L1–L5: `000 ()`, `001 QUOTE`, `010 ATOM`, `011 CDR`, `100 CAR`, `101 EQ`, `110 COND`, `111 CONS` | Прежній порядок D3-функцій не переносити без явного фактичного bridge |
| 04.10.2026 17:42 | [`9f899a78f745`](https://github.com/juv4uk/sens/commit/9f899a78f745) | D4 bootstrap — 16/16; точні D4-функції та селектори | Звіряти D4 за канонічними таблицями, не за історичними назвами |
| 04.10.2026 19:10 | [`05f9ad27ee06`](https://github.com/juv4uk/sens/commit/05f9ad27ee06) | D5 повторно ратифіковано, 32/32, після перегляду | Донорна Lisp-назва сама не ратифікує координату |
| 05.10.2026 05:05 | [`49597e89a952`](https://github.com/juv4uk/sens/commit/49597e89a952) | D1–D6 фундамент, Contract 11.5, D6 64/64 | Не зрівнювати domain occupancy із доведеною виконуваністю |
| 06.10.2026 18:37 / 18:55 | [#3960](https://github.com/juv4uk/sens/issues/3960), [`cf7011418d1d`](https://github.com/juv4uk/sens/commit/cf7011418d1d) | **Перший чинний D8 256/256.** Власницьке рішення о 18:37:02, commit о 18:55:19 | До цієї миті **не було** сучасного D8; не вводити історичний SID8↔D8 test чи alias |
| 06.10.2026 21:44 / 22:00 | [#4008](https://github.com/juv4uk/sens/issues/4008), [`04058d2d0b69`](https://github.com/juv4uk/sens/commit/04058d2d0b69) | D9 512/512, Contract 11.8 | Issue описує власницьке рішення як «07.10» — **час у Git UTC 06.10 22:00:46**, різницю дат зберігати, не «виправляти» заднім числом |
| 09.10.2026 18:30 / 19:33 | [`e405be6f4b91`](https://github.com/juv4uk/sens/commit/e405be6f4b91), [`10ca5065b307`](https://github.com/juv4uk/sens/commit/10ca5065b307) | Нативний T5 decode / streaming-encode механізм у Rust | Оптимізація носія **не** змінює мовну координату чи семантичний закон |
| 11.10.2026 10:09 | [`6682aff73647`](https://github.com/juv4uk/sens/commit/6682aff73647), [numeric ratification](../../contracts/numeric-domains-ratification.lisp) | Числова драбина **D24/D48/D96/D192/...** ратифікована окремо | Не виводити арифметичність D1–D10 із цифр або host integer |
| 11.10.2026 22:56 / 23:33 | [`03e365f7b06d`](https://github.com/juv4uk/sens/commit/03e365f7b06d), [`080a11f3a9e8`](https://github.com/juv4uk/sens/commit/080a11f3a9e8) | Акт D10 **атомарно всього домену 1024/1024**, дата рішення в [JSON](../../knowledge/d10-owner-whole-domain-ratification-20261012.json) — **12.10**; Contract 11.9 | Відокремити час запису commit від дати власницького акта. Немає автоматичного доказу F1–F4 чи фізичного runtime-admission |
| 12.10.2026 12:40 | [`416622b1ae1b`](https://github.com/juv4uk/sens/commit/416622b1ae1b) | **D1–D10 не математичні операнди**; лише явна D24+ математика | Старе обчислення на голому `0`/`1` не можна «полагодити» мовчазним decimal bridge |
| 13.10.2026 02:20 / 02:25 | [`2028695f4c79`](https://github.com/juv4uk/sens/commit/2028695f4c79), [`6c70c61625e1`](https://github.com/juv4uk/sens/commit/6c70c61625e1) | Чинний D7 **v2 keyboard 128/128**, попередня v1 126/128 — лише походження | Символи `0`–`9` у D7 є **текстом**, а не D24+ чи функціями |
| 13.10.2026 17:59 | [`ce84f04d7a5f`](https://github.com/juv4uk/sens/commit/ce84f04d7a5f) | Додатково уточнено machine-binary default та decimal лише як людську проєкцію D24+ | Берегти провідні нулі/тип, не робити binary→decimal→binary семантичну трансляцію |
| 14.10.2026 02:44 / 03:57 / 10:36 | [`5baa90b62be6`](https://github.com/juv4uk/sens/commit/5baa90b62be6), [`ace3a41a0560`](https://github.com/juv4uk/sens/commit/ace3a41a0560), [`6f08e09f4cb0`](https://github.com/juv4uk/sens/commit/6f08e09f4cb0) | Незалежний Zig T5, D10 coordinate-only профіль і безалокаторний фізичний валідатор | **D1–D9** звичайний T5; **D1–D10** окремий координатний; Zig 0.16.0 не встановлює D10 callability |

**D11 — окрема ситуація:** [`knowledge/d11-testing-vocabulary-ratified.json`](../../knowledge/d11-testing-vocabulary-ratified.json) має 11-бітовий **тестовий словник** (43 зайняті з 2048), *не callable Core*. За поточним [#5767](https://github.com/juv4uk/sens/issues/5767) власник тимчасово не допускає самовільне використання D11 у T5/міграції, поки окрема робота з функціями не завершена. Не плутати із D10 або із числовими D24+.

## Практична матриця підготовки, без захоплення чужих CLAIM

| Незалежний напрям | Джерело істини і наступна доказова робота | Ознака завершення окремого зрізу |
|---|---|---|
| Розбір історичних `.lisp` когорт (#5609, #5141) | За датою введення форми визначити *той* історичний контракт; відобразити лише на незалежно доведену теперішню `(domain,width,bits,law)`; зберегти QUOTE/D2/COND/D1, не переписувати старі SID8 прямо в D8 | Для кожної заміни: source path/blob SHA, функція, старий контекст, новий чинний закон, SENS позитивний і негативний self-verdict |
| Reader/AST/EVAL (#5605/#2817/#5606) | Звіряти чинні domain-контракти та незалежні механізми; висновок із Rust-реалізації не вважати новою мовною аксіомою | Адресний native SENS witness на змінену семантичну форму, негативний bit/type фальсифікатор |
| D7/D24+ та арифметика | Дату D7 v2 і закони D24+ зіставити зі старим джерелом, не підставляти bare digits як операнди | Відсутнє неявне перетворення D7-тексту/функціонального коду в число; реальний SENS математичний self-verdict |
| Zig T5 / Rust / corpus (#5767/#5770) | Відрізнити механічний `encode(decode)` від **незалежного** Zig↔Rust декодованих координат та byte parity на *одному git-tracked snapshot*. SHA-256 — доказ походження; FNV-64 лише некриптографічний digest | Один pinned `HEAD`, corpus manifest SHA-256, ті самі файли і кожне слово `(width,payload)`, негативні fixtures, точна команда/CI |
| Бенчмарки (#5771) | Парні входи, однакове залізо/компілятори, raw samples, p50/p95, алокації/peak RSS — кожне **вимірювати**, не здогадуватись | Наявний raw artifact із environment, SHA і умовами відтворення; окремо від native semantic verdict |
| D11 | Лише документувати окремий тестовий словник і рішення власника; не розширювати T5 або callability | HANDOFF після *фактичного* власницького рішення та доказів спеціальної D11 lane |

**Це пропозиція порядку перевірок, не призначення людей чи зміна політики.** Перед дотиком до файла перечитати актуальні CLAIM у #5029, звірити свіжий `main`, а перетин передавати через HANDOFF/ACK. Незайнятий файл не зупиняє решту рою; технічно недоведений крок лишається вузькою «можливістю-розв'язати-цікаву-задачу» з причиною та SHA. Важливі рішення залишаються за власником SENS.

## Рецепт для наступного агента: перевірити *коли* закон увійшов

```sh
git fetch origin main
git rev-parse origin/main
git log -n 30 --date=iso-strict --format='%H %cI %s' -- language-contract.lisp
git log --follow --date=iso-strict --format='%H %cI %s' -- lib/domains/d7.lisp
git log --date=iso-strict --format='%H %cI %s' -- crates/sens/src/ternary_transport.rs
git show --format=fuller --stat cf7011418d1daf583ce7cdfe78f16af74ef66e2c
git show cf7011418d1daf583ce7cdfe78f16af74ef66e2c:knowledge/d8-ratified.json
git show 04058d2d0b69489a145539aff52fa3517ca4d82c:knowledge/d9-ratified.json
git show 03e365f7b06db208f752271cee944d15c326c770:knowledge/d10-owner-whole-domain-ratification-20261012.json
git diff 320a389d0054^ 320a389d0054 -- language-contract.lisp
git ls-files -z -- '*.sens'   # передати NUL-список споживачу, не split('\n')
```

Для конкретної функції потрібні **обидва** свідки: `git show <pre-change-SHA>:<path>` (що означало джерело тоді) та `git show <current-SHA>:<path>` (чинна машинна таблиця/закон). Відсутній чи неретифікований міст означає **не вгадувати**, а зафіксувати вузьку проблему та продовжити незалежні файли.

### Мінімальний паспорт готової міграції конкретного stem

```text
stem/path:
base main SHA + original file blob SHA:
historical source-era commit/date + applicable historical contract:
present ratified (domain, exact width, binary bits, law) source:
mechanism/callability proof (separate from ratification):
D1/D2/QUOTE and D7/D24 boundaries checked:
positive native SENS witness:
one-bit or one-domain negative native SENS witness:
.lisp/.sens/extensionless physical SHA256 (as applicable):
Zig 0.16 D1-D10 transport + Rust same-corpus receipt:
first differing byte/word + exact reproduction command, when mismatch:
actual CI URL + exact commit SHA:
CLAIM/HANDOFF source in #5029:
verdict: PROVED / SOURCE_READY / UNVERIFIED / narrow TECHNICAL_ISSUE
```

**Найважливіше:** старий зелений тест може підтверджувати *правильність старого контракту*, а не нової семантики. Тільки датований доказ переходу + чинна ратифікація + адресний native SENS witness дають підставу переносити значення. Цей документ — маршрут до доказів, а не сам доказ для всіх файлів.
