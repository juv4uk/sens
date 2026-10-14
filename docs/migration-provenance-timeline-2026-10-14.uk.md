# Часова карта міграції SENS: походження законів, а не нова семантика

**Дата огляду:** 14.10.2026 (Europe/Kyiv). **Статус:** довідкова передача рою, **НЕ нормативний закон** і НЕ новий gate.  
**Обсяг:** `juv4uk/sens`; координування [#5029](https://github.com/juv4uk/sens/issues/5029), [#5141](https://github.com/juv4uk/sens/issues/5141), [#5609](https://github.com/juv4uk/sens/issues/5609), [#5767](https://github.com/juv4uk/sens/issues/5767).

> **Єдина чинна влада:** [CURRENT.md](../CURRENT.md) → [language-contract.lisp](../language-contract.lisp) і ратифіковані доменні джерела; семантичний verdict тільки SENS. Дати й коміти нижче пояснюють, **коли** закон з'явився, але не замінюють його. Довідковий документ ніколи не породжує відповідностей або права виконання.

## 0. Рання драбина D1–D6: чинні закони після історичних перебудов

**Дати D1/D2 наведено за власницьким рішенням у задачах;** це не вигаданий точний час першого Git-коміту. Для D3–D6 нижче перевірено саме `commit.created_at`. Дати ратифікації не слід плутати з попередніми експериментальними картами або пізнішими технічними cutover.

| Дата рішення / коміту | Первинний доказ | Чинна межа для міграції |
|---|---|---|
| **01.10.2026, рішення власника** | [#1699](https://github.com/juv4uk/sens/issues/1699) | **D1** лише точний біт `0=NO, 1=YES`. `D3:000 ()` — інша семантична сутність, не третя істинність D1 і не D1:0. Попередня 15-рівнева модель нечинна. |
| **01.10.2026, рішення власника** | [#1702](https://github.com/juv4uk/sens/issues/1702) | **D2** точні 2-бітові структури: `00` separator, `01` close, `10` open, `11` dot. Старі CONTROL2 escape-машини — provenance, не нормативна синтаксична семантика. |
| **04.10, 16:04:59 UTC (19:04:59 Київ)** | [#3202](https://github.com/juv4uk/sens/issues/3202), [804a938e](https://github.com/juv4uk/sens/commit/804a938e2c5acdb3a805b2e8d13a8e6cdd1c4cc2) | **D3** повний 8/8 L1–L5: `000 ()`, `001 QUOTE`, `010 ATOM`, `011 CDR`, `100 CAR`, `101 EQ`, `110 COND`, `111 CONS`. Попередня перестановка `011 COND` тощо — борг історичної реалізації, не альтернатива. |
| **04.10, 17:42:16 UTC (20:42:16 Київ)** | [#3272](https://github.com/juv4uk/sens/issues/3272), [9f899a78](https://github.com/juv4uk/sens/commit/9f899a78f74567634588d30a73ea05168027f86a) | **D4** компактний 16/16 bootstrap; `0010 LAMBDA`, `0011 DEFINE`, `0100 NOT`, `0101 NULL`, `1111 APPEND`. Відрізняти NOT (D1 predicate) від NULL (`D3:000` structural empty); старі проміжні D4-карти нечинні. |
| **04.10, 19:10:02 UTC (22:10:02 Київ)** | [#3305](https://github.com/juv4uk/sens/issues/3305), [#3330](https://github.com/juv4uk/sens/issues/3330), [05f9ad27](https://github.com/juv4uk/sens/commit/05f9ad27ee06b1c30f2bbbe90cde26294a06b8c4) | **D5 v2** 32/32, без дублювання нижніх доменів. Старий OD-005/pre-v2 та відхилені placement-плани не стають новими D5; D4:1111 — єдиний APPEND. Ratified resident ≠ реалізований виклик. |
| **04.10, 23:49:13 UTC (05.10, 02:49:13 Київ)** | [#3393](https://github.com/juv4uk/sens/issues/3393), [8b792c04](https://github.com/juv4uk/sens/commit/8b792c044d8fc14e3c8ffee0893e8f972cc1dd2c) | **D6** owner-ratified 64/64 із S3/S4 gauge і generator proofs. Ранні D6-донори/попередня геометрія — provenance; із зайнятості 64/64 не виникає право виконання кожної форми. |

**Важлива проміжна зміна, яку НЕ можна пропустити:** після ратифікації D3/D4/D5 04.10 рішення власника [#3327](https://github.com/juv4uk/sens/issues/3327) **тимчасово відкликало** всі семантичні ратифікації вище D2. Зокрема, 05f9ad27 (19:10 UTC) засвідчує першу D5 v2 ратифікацію, **але не безперервну владу** цього статусу. [#3330](https://github.com/juv4uk/sens/issues/3330) окремо затвердило карту D5 v2 умовно, після відновлення D3→D4. Лише [e02e3cf6](https://github.com/juv4uk/sens/commit/e02e3cf657dde36dd90771cbf4f385c8e396325e) від **04.10, 21:37:04 UTC (05.10, 00:37:04 Київ)** повторно закріпив **D1–D5 як чинний ланцюг** у Contract 11.4, скасувавши дію reset #3327 для D3–D5. D6 залишався дослідним до наступного власницького cut. Старий `D5`-snapshot між reset і відновленням не є нормативним лише через той самий бітовий код. Це і є причина перевіряти **послідовність комітів**, а не один збіг рядків.

**Наслідок:** при читанні історичного `.lisp` завжди спочатку визначити період і застосовану тоді карту; не подавати старі D3/D4/D5 імена чи Function8 байти як уже ратифіковані сучасні координати. Навіть після встановлення тотожності окремо довести чинний закон і конкретний допущений виконавчий механізм.

## 1. Хронологія на основі Git commit, а не назви сучасного файлу

Дата коміту наведена **UTC**; дата праворуч — місцева **Europe/Kyiv (UTC+03:00, жовтень 2026)**. Окремо зберігати дату рішення власника в issue і час появи коду в Git: це різні події.

| Дата/час коміту UTC | Дата/час у Києві | Що справді змінилось і що не випливає з цього |
|---|---|---|
| **06.10, 18:55:19** · [cf7011418](https://github.com/juv4uk/sens/commit/cf7011418d1daf583ce7cdfe78f16af74ef66e2c) | 06.10, 21:55:19 | Власницька ратифікація **D8 256/256** за [#3960](https://github.com/juv4uk/sens/issues/3960); Contract 11.7, `contracts/d8-ratification.lisp`, `knowledge/d8-ratified.json`. Старий плоский SID8/Sens8 **ніколи не був сучасним D8**. D8-резидент ≠ executable mechanism. |
| **06.10, 22:00:46** · [04058d2d](https://github.com/juv4uk/sens/commit/04058d2d0b69489a145539aff52fa3517ca4d82c) | **07.10, 01:00:46** | Власницька ратифікація **D9 512/512** за [#4008](https://github.com/juv4uk/sens/issues/4008); Contract 11.8. Із них 128 selector coordinates theorem-forced, 384 S4 gauge owner-ratified. Не трактувати історичні карти як D9 і не виводити callability з occupancy. |
| **11.10, 10:08:34–10:09:07** · [39f2e42b](https://github.com/juv4uk/sens/commit/39f2e42bf84917be23d3e861ff21f8636eaf47de), [dcb9bea1](https://github.com/juv4uk/sens/commit/dcb9bea1be35a45eed55beb68cb), [6682aff7](https://github.com/juv4uk/sens/commit/6682aff73647f45f3822dfb0c0eac1c2001e1ddf) | 11.10, 13:08–13:09 | **D24/D48/D96/D192/...** стали повноправними numeric domain peers, не просто сховищами бітів. `contracts/numeric-domains-ratification.lisp`; числа/NEG/RATIO лише за чинними явно допущеними законами. D1–D10 не стають арифметичними операндами від однакового payload. |
| **11.10, 22:56:07** · [03e365f7](https://github.com/juv4uk/sens/commit/03e365f7b06db208f752271cee944d15c326c770) | **12.10, 01:56:07** | Рішення власника щодо **цілого D10-каталогу 1024/1024**; у текстах датоване **12.10** за місцевим днем. `knowledge/d10-owner-whole-domain-ratification-20261012.json`. Це **не** автоматичний допуск до виконання і **не** дозвіл ordinary T5 profile D1–D9 виконувати D10. |
| **13.10, 02:25:55** · [6c70c616](https://github.com/juv4uk/sens/commit/6c70c61625e1c35ea9906e52f18c667ebab48944) | 13.10, 05:25:55 | У `lib/domains/d7.lisp` впроваджено **D7 keyboard v2, 128/128**; збережено `research/domain-archive/20261013/d7-v1-before-keyboard.lisp`. Ратифікаційне джерело — `contracts/d7-ratification.lisp` / `knowledge/d7-keyboard-v2-ratified.json`. Історична таблиця **D7 v1 126/128** збережена для provenance; **за v1 нічого не встигли мігрувати** (уточнення власника 14.10). Чинний маршрут нової міграції відразу використовує **v2 128/128** без історичного конвертера. |
| **13.10, 13:01:48** · [0b4fceac](https://github.com/juv4uk/sens/commit/0b4fceac9074ab683571bebf0fc8f577cfd51b30) | 13.10, 16:01:48 | **D11:** власницький **тестовий словник** 43 зайняті / 2048 ємності, `knowledge/d11-testing-vocabulary-ratified.json`. Це **не** ратифікація 2048 executable функцій, не автоматичний D11 T5 transport і не розширення ordinary D1–D9/D10 Zig APIs. |
| **14.10** · [#5767](https://github.com/juv4uk/sens/issues/5767), [#5770](https://github.com/juv4uk/sens/issues/5770) | 14.10 | Технічні механізми Zig T5/F3C, ABI, corpus parity, D10 coordinate profile **перевіряють носій**, а не ратифікують семантику. Фактичні результати й exact SHA перевіряти за зазначеними у задачах CI receipts; не переносити старі benchmark claims на новий код автоматично. |

**Не робити з календаря новий opcode:** історична дата — частина provenance конкретного джерела, але сама дата або 8 бітів не створюють `D8`. Окремо зберігати `commit SHA` первинної форми і `commit SHA` чинної ратифікації.

## 2. Незмінні правила перевірки під час міграції

1. **Семантична особа:** `exact bits + exact domain + admitted/proved or owner-ratified law`. Бінарне слово не перетворювати у десятковий посередник. Однакові payload у різних доменах — різні об'єкти. D2 структура, D1 предикат, D7 текст не підміняють функції; `D7 '0'..'9'` — текстові символи, не арифметика.
2. **Резидентність ≠ виклик:** D8/D9/D10 whole occupancy не доводить механізму. Якщо код ратифікований, але виклик не admitted, негативний witness має зафіксувати саме це; не створювати паралельної реалізації семантичної істини у Python/Rust/Zig.
3. **Профіль T5:** `t5.encode/decode/validatePhysical` у чинному Zig — звичайний D1–D9; `*Coordinates` — **окремо** D1–D10 як механічні координати, не дозвіл виконання. D11 тестовий словник і D24+ не можна автоматично вписувати в ці профілі. П'ять тритів/байт — фізична механіка; `2` є межею/доповненням, не третьою цифрою SENS.
4. **D7 тільки чинний v2:** власник підтвердив, що за історичним v1 **немає жодної мігрованої програми чи набору даних**. Тому ні конверсія v1→v2, ні v1 version-manifest, ні old-payload gate, ні карантин не є передумовою міграції. Нові `.sens` створювати **одразу за owner-ratified D7 keyboard v2 128/128** із точною шириною та проєкцією. Історію v1 залишити як архів, не змішувати phonology v1 із keyboard v2; якщо колись з'явиться реальний документований старий артефакт, розглядати його окремо, без глобального HOLD.
5. **Чистий Zig:** жодної таблиці SID8→D8, old/new lookup, historical source-era dispatcher, функціонального закону, створеного з байтів. Історичне зіставлення, якщо доказане, залишається у зовнішніх SENS migration tools із explicit source provenance; Zig передає фізичні exact-width дані. Класичний Rust reference implementation — helper, не другий семантичний закон.
6. **Цілісність:** `encode(decode(bytes)) == bytes` доводить канонічність, не тотожність оригіналу. Наприклад, `D9:100000000` → T5 `51 02`, а `51` саме по собі валідне `D5:10000`. Втрата байта, що залишає канонічний носій, виявляється **тільки** за зовнішньо закріпленими `expected byte length + SHA-256`; не вимагати неможливого «будь-яке усічення фізично reject».
7. **Тріада однойменних файлів:** `name.lisp` (чинна `ук` поверхня) → ратифіковані точні слова → `name.sens` (канонічний T5) → `name` (генерований 0/1-view). Кодування не вигадує semantic-map. Публікувати три SHA; відтворювати паритет у Zig↔Rust окремо від native SENS semantic self-verdict.
8. **Аксіоми й походження:** відрізняти `MATHEMATICAL_AXIOM`, `WORLD_DEFINITION_AXIOM`, `MODEL_LAW`, `OBSERVATION`, `DERIVED_FACT`, `UNKNOWN` відповідно до чинного SENS контракту там, де ці класи вже визначені; не оголошувати спостереження новою аксіомою лише тому, що test зелений. Докази залишаються у Git, а ця карта не додає жодної аксіоми.

## 3. Маршрут для агента, який бере наступний файл

**Перед зміною** записати у [#5029](https://github.com/juv4uk/sens/issues/5029) вузький `CLAIM`: реальний виконавець, exact paths, blob/base SHA, чинна authority, негативний/позитивний witness. Прочитати `git log --follow -- <file>`, `git show <sha>:<file>`, `git blame` і пов'язані issue/ратифікації; знайти **перший** commit зміни семантичного закону, не вважати rename або міграцію транспорту ратифікацією. Не торкатися чужого write-set.

**Для кожної форми** документувати: `original path@blob + commit date + historical schema`; `target exact domain/width/bits + owner authority`; `per-form admitted mechanism`; `original/target behavior or output SHA`. Якщо незалежно доведено лише частину функцій, переносити **цю частину**, не ставити глобальний стоп усьому файлу чи рою. За невідомим mapping — local `можливість-розв'язати-цікаву-задачу` з першою відмінністю, SHA, гіпотезою і відтворенням.

**Після зміни** підтвердити точну бітність і провідні нулі, D2, roundtrip byte-exact, один позитивний та однобітовий негативний **SENS** self-verdict для виконуваних форм; для транспортних інструментів — Zig↔Rust parity на **тому самому pinned корпусі** та окремі benchmarks без невиміряних speedup. RED мусить друкувати test_id/layer/fixture SHA/expected/actual/first difference/repro; відсутність фактичного прогону = `UNVERIFIED`, а не PASS. Лише центральний `.github/workflows/ci.yml` автоматичний; нових дубльованих auto-workflows не створювати.

**Передача рою:** [#5141](https://github.com/juv4uk/sens/issues/5141) — джерело/AST і доказані перетворення; [#5609](https://github.com/juv4uk/sens/issues/5609) — міграція функцій; [#5029](https://github.com/juv4uk/sens/issues/5029) — один writer/CLAIM/HANDOFF; [#5767](https://github.com/juv4uk/sens/issues/5767) — Zig T5 фізичне; [#5770](https://github.com/juv4uk/sens/issues/5770) — незалежний byte/parity корпус; [#5771](https://github.com/juv4uk/sens/issues/5771) — парні виміри; [#5041](https://github.com/juv4uk/sens/issues/5041) — контрольована інтеграція. Цей файл не привласнює їхні шляхи, не встановлює адміністративного HOLD, не запускає workflow і не уповноважує автоматичний merge.

## 4. Критерій успішної підготовки

Для обраного незалежного файлу: історичний source SHA + дата і ратифікаційне джерело встановлені; невизначені ідентичності позначені без домислів; відома межа виконуваності; заявлено неперетинний write-set; відтворюваний witness наявний або чесно `UNVERIFIED`. Суміжні агенти можуть безперервно рухати інші незалежні файли. **Ніякого нового нормативного бар'єра чи альтернативного оракула ця карта не створює.**


## 5. Зріз M2 від 14.10: коли Zig став симетричним входом, а C — незалежним свідком

**Статус:** довідкова Git-хронологія, НЕ ратифікація, НЕ новий semantic gate чи глобальний HOLD. Час — **Git committer UTC** за конкретним SHA; CI-verdict завжди окремо на точному SHA.

| Час UTC 14.10 | Шлях і коміт | Що змінилося | Що **не** доведено |
|---|---|---|---|
| **13:58:16** | [5196b991](https://github.com/juv4uk/sens/commit/5196b9914a6678262a782003b88d1211a95b0fee), `research/zig-codecs/transport_abi.zig` | Додано симетричний фізичний Zig ABI v2 **T5 → caller-owned BE3**: exact width/bits і fail-closed ємність. | Немає D2 reader, semantic evaluator чи семантичного реєстру Zig. |
| **14:11:11** | [015729fc](https://github.com/juv4uk/sens/commit/015729fc5eecafcb80290e5a27f5195867b16e48), `research/zig-codecs/host-c/d3_subset.c` | Додано незалежний **обмежений C-виконавець** із фізичним Zig ABI ingress для вибраного D1–D3 піднабору. | Сам файл не доводить Rust-free dependency closure або спільного semantic PASS двох хостів. |
| **14:22:00** | [1bf97ee5](https://github.com/juv4uk/sens/commit/1bf97ee50d69a6e42ed7e756964e0dda8396ea60), `crates/sens/src/binary_execution.rs` | Відкрито чинний `PhysicalT5Program::from_exact_words`: **SENS** після Zig-фізики читає D2, перевіряє executable heads, відповідає за чинний закон. | Не переносить семантику з SENS до Zig. |
| **14:24:29** | [221eb979](https://github.com/juv4uk/sens/commit/221eb9796ec03731968183e763b918189924ecee), `crates/sens-cli/src/bin/sens-trit.rs` | Zig BE3 ingress при ввімкненому Zig transport для eval/eval-core4/eval-f3, далі SENS reader. | Не доводить C-host і всіх CLI режимів. |
| **14:30:46** | [0bb725b9](https://github.com/juv4uk/sens/commit/0bb725b9f1dce6301e9b2e4884d8d70494b07da4), той самий CLI-файл | Вилучено залишковий Rust T5 physical decode у Zig F3C feature path; збережено SENS `from_exact_words` і перевірку одного кореня. | Source cutover не тотожний незалежному native self-verdict. |

**Механічна пастка конкурентного main:** [63b9e2ca](https://github.com/juv4uk/sens/commit/63b9e2ca8b2f03289cd4b8737b0cd20bafc38dc4) о 14:18:54 UTC імпортував `numeric_domains.zig` у `domain_ladder.zig` **до** появи файла в дереві; [23616d1b](https://github.com/juv4uk/sens/commit/23616d1bba6451484a71e436bb27b34be454c45d) о 14:26:53 додав його. Проміжний RED — Zig FileNotFound і його downstream evidence-кроки, **не** регресія семантики D24/D8. Перед зміною імпорту перевіряти існування модуля на **тому самому Git tree**, не створюючи нового загального блокера.

### Незалежні lane, яким потрібна ця послідовність

- **H0 #5777/#5775:** один Zig механічний ABI, exact word/BE3, version, ownership, error codes, bounds, CRC, SHA; **фізична** квитанція, не callability.
- **H1 #5787:** C-host/C-evaluator без Rust у **реальному dependency closure** для вузького допущеного D1–D3 піднабору; C не ратифікує нових законів.
- **H2 #5788:** однакові SHA-pinned позитивні та однобітні негативні входи на двох незалежних executors, окремі вердикти **A byte parity / B semantic parity**, output/error SHA, first mismatch і команда відтворення. Немає H2 PASS із самого T5 roundtrip.
- **Міграція файлів #5141/#5609:** `old path@SHA + історична дата → ратифіковане джерело → exact domain/width/bits → admitted mechanism → native SENS self-verdict`. Один CLAIM на неперетинний write-set; не затримувати інші незалежні файли.

**Незмінні часові межі:** під D7 v1 **нічого не було мігровано**, отже немає глобальної конверсії; чинна D7 keyboard v2 128/128 використовується відразу. D8 уперше owner-ratified 06.10, історичні 8-бітові коди не були його попередньою версією. D10 1024/1024 — residency, не автоматичний T5/callable admission; D11 — testing-only. Довідковий документ не стає другим semantic authority: лише власник, чинний SENS Contract 11.9 та ратифіковані аксіоми.

## 6. TCP: Git-хронологія трьох незалежних міграцій одного модуля

**Це карта походження, не ратифікація й не автоматичне правило переписування.** За власницьким [#1699](https://github.com/juv4uk/sens/issues/1699) і чинним `language-contract.lisp` (11.9), `D1:0=NO`, `D1:1=YES`, а `D3:000` є структурним `()`. Історичний спосіб обчислити YES не підміняє прямого one-bit D1.

Нижче — фактичний `git log -- lib/tcp.lisp` (Git committer UTC):

| Час UTC / commit | Зафіксована зміна | Обов'язкове розділення для міграції |
|---|---|---|
| **13.10, 09:02:59** · [ecd8e4cb](https://github.com/juv4uk/sens/commit/ecd8e4cbdd9818cc3fb8b4ae337abc15c3991a49) | Умова `(0100 (101 (100 decoded) (001 decoded)))` — старий D4 NOT/EQ — замінена `(010 (001 ()))`: D3 ATOM над QUOTE структурного порожнього. | Проміжний шлях до D1:YES; **не** дозвіл застосовувати D4 NOT до D3:000. |
| **13.10, 11:25:03** · [5910d7d6](https://github.com/juv4uk/sens/commit/5910d7d6795dcf8499ab155690ee9a746a4b5b19) | Збережено двопольовий `D3:110 COND` і повторне використання `utf8-*` / `tcp-*-raw`. | TCP/UTF-8 policy — у SENS; host — механізм, не новий закон. |
| **13.10, 21:04:45** · [6c3cc743](https://github.com/juv4uk/sens/commit/6c3cc743e9ad755c0144da5707d9d63841cd0e54) | У двох *одно-зв'язувальних* місцях `D6:001000 LET` змінено на явне застосування `D4:0010 LAMBDA`; додано `tests/fixtures/semantic/tcp-exact-selftest.bits` і SENS-виконання фізичного T5-свідка. | Арність, scope та механізм зв'язування **окремі** від D1. Не робити масової заміни кожного LET за одним прикладом. |
| **14.10, 15:16:21** · [42337cd3](https://github.com/juv4uk/sens/commit/42337cd36535855baf79bf96665e8ecce3ac193e) | `(010 (001 ()))` у єдиному fallback замінено **прямим `#d1:1`**; тести зіставляють direct/derived D1, `#d1:0`, COND і D4 NOT-невідповідність. | Чинний one-bit predicate; не numeric `1` і не D7-гліф `'1'`. Похідна форма лишається тільки як explicit provenance у тестах. |
| **14.10, 15:21:07** · [50fb8fc9](https://github.com/juv4uk/sens/commit/50fb8fc94c730481042e9019872dac5dda089af7) | `scripts/test-tcp-d1-bitness.py` оновлено, щоб вимагати безпосередній D1 fallback. | Python-страж джерела — це механічна перевірка, **не** другий SENS semantic oracle. |

**Незалежність доказів.** У `tests/test_tcp_d1_fallback.py` зафіксовано вихідний Git blob `8860b61e171fcefa56147d93153071a14dd4c55e` і послідовне відновлення `old → derived → direct`; це доказ історичної конкретної правки, не SHA фізичного T5. `crates/sens/tests/tcp_d1_fallback.rs` запускає чинні SENS форми з обома результатами D1/COND, а тест фізичного `tcp-exact-selftest.bits` перевіряє виконання через SENS. Автоматичний CI на [точному SHA 42337cd3, run 38588276472](https://github.com/juv4uk/sens/actions/runs/38588276472) має статус **SUCCESS**; [SHA 50fb8fc9, run 38588553432](https://github.com/juv4uk/sens/actions/runs/38588553432) — **SUCCESS**. Це **не** вердикти про всі наступні SHA.

**Передача #5029 / #5141 / #5609:** кожен агент визначає власний історичний `path@blob`, ratification SHA, точні width/bits, окремо *семантичний закон*, *синтаксичний вираз* і *виконавчий механізм*. Не замінювати всі `ATOM(QUOTE ())` на `#d1:1` без власного позитивного/однобітового негативного SENS-свідка: у чужому контексті можливі ефекти, змінені binder/scope та інша роль результату. `HOST_NEUTRAL_IMPACT` — C/Rust/Zig передають лише exact фізичні слова; тільки SENS визначає значення і callability. Дозволено рухати інші незалежні файли без глобального HOLD.
