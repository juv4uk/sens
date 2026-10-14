# Хронологія семантики SENS: доказовий хендофф міграції · 14.10.2026

> **Ненормативний індекс історичних доказів, НЕ нова аксіома і НЕ нова семантична влада.** Цей документ пояснює *коли* змінено контракт. За суперечності чинні [CURRENT.md](../../CURRENT.md), [AGENTS.md](../../AGENTS.md), [language-contract.lisp](../../language-contract.lisp), owner-ratified машинні таблиці та нативні SENS-свідки мають пріоритет. Історичні коміти — докази часу змін, а не поточні таблиці відповідності.

Пов'язані завдання: [#5029](https://github.com/juv4uk/sens/issues/5029) (координація), [#5041](https://github.com/juv4uk/sens/issues/5041) (інтеграція), [#5141](https://github.com/juv4uk/sens/issues/5141) (міграційні інструменти), [#5609](https://github.com/juv4uk/sens/issues/5609) (корпус), [#5767](https://github.com/juv4uk/sens/issues/5767) (Zig T5), [#5770](https://github.com/juv4uk/sens/issues/5770) (незалежний parity). Граничний базовий `main` для цього індексу: `7f06750f2ae8041a256655ea88eb6fccbc31faae` (14.10.2026); після кожного наступного push потрібна свіжа перевірка.

## Хронологія чинних переходів (Git commit date — UTC)

| Коли / джерело | Який факт введено | Чого НЕ можна виводити |
|---|---|---|
| 05.10.2026 · [49597e89](https://github.com/juv4uk/sens/commit/49597e89a9529c12ab5738b420cde1059357ae85) | D1–D6 foundation, Contract 11.5 | Старі вісім бітів не стають доменною адресою |
| 05.10.2026 · [e345aa3f](https://github.com/juv4uk/sens/commit/e345aa3f0c3db8d915468f6d5eddd39dbaf4a708) | D7 Contract 11.6 | Історичне Text7/126 із 128 — не нинішня клавіатурна D7 v2 |
| **06.10.2026 18:37:02 UTC** · [owner issue #3960](https://github.com/juv4uk/sens/issues/3960); **18:55:19 UTC** · [cf7011418](https://github.com/juv4uk/sens/commit/cf7011418d1daf583ce7cdfe78f16af74ef66e2c) | Уперше ратифіковано **сучасний D8 v2, 256/256**; `knowledge/d8-ratified.json` | Жодна попередня SID8/Sens8/Function8-мапа не була «раннім D8»; рівність бітів не є semantic successor |
| 06.10.2026 22:00:46 UTC · [04058d2d](https://github.com/juv4uk/sens/commit/04058d2d0b69489a145539aff52fa3517ca4d82c) | Ратифіковано сучасний **D9, 512/512** | Residency не дорівнює runtime callability |
| 11.10.2026 · [6682aff7](https://github.com/juv4uk/sens/commit/6682aff73647f45f3822dfb0c0eac1c2001e1ddf), [d6184d80](https://github.com/juv4uk/sens/commit/d6184d80257912a4b10c75f56f3b0e6e01d5401a) | Доменна числова родина D24/D48/D96/... та NEG/RATIO у ній | D1–D10 не стають математичними операндами від схожих payload |
| **12.10.2026 за датою акта** · [03e365f7](https://github.com/juv4uk/sens/commit/03e365f7b06db208f752271cee944d15c326c770), Git timestamp **11.10 22:56 UTC**; [080a11f3](https://github.com/juv4uk/sens/commit/080a11f3a9e8254c233e58336f2898841432faa2) | Власник ратифікував каталог **D10 1024/1024**, Contract 11.9 | Не автоматизує механізм виконання, F1/F2/F3 law proof чи T5 opcode admission |
| 12.10.2026 · [416622b1](https://github.com/juv4uk/sens/commit/416622b1ae1b0866a523a31e7fff70cd49f9d604) | Явно відмежовано двійкові D1–D10 від арифметики D24+ | Немає неявного десяткового посередника для semantic identity |
| **13.10.2026** · [2028695f](https://github.com/juv4uk/sens/commit/2028695f4c79c04bb676214ec22c5e8ca53446aa) | Нова owner-ratified **D7 keyboard v2, 128/128** | Історичну D7 sound/Text7 v1 не використовувати як поточний keyboard oracle |
| 13.10.2026 · [b085cf87](https://github.com/juv4uk/sens/commit/b085cf87b4f3ab7b3286348f9a816b84bbea6d64) | Для QUOTE пріоритет — *чинна точна доменна координата*, D7 тільки для об'єкта без такої координати | Не дублювати CAR/QUOTE/NIL через D7, `MAP` із D6/D8 неоднозначний без контексту |
| **13.10.2026** · [0b4fceac](https://github.com/juv4uk/sens/commit/0b4fceac9074ab683571bebf0fc8f577cfd51b30) | **D11 testing vocabulary**: `knowledge/d11-testing-vocabulary-ratified.json`, 43/2048, *testing only* | Це не Core callability і не дозвіл автоматично розширити Zig T5 |
| 13.10.2026 · [ce84f04d](https://github.com/juv4uk/sens/commit/ce84f04d7a5f5b63761ed0668fbd579b0099aac1) | Контракт уточнив двійкові слова, D7-текст та зовнішнє D24+ проєктування | Десяткове представлення людиною не є внутрішнім семантичним перетворенням |
| 14.10.2026 · [954f40a0](https://github.com/juv4uk/sens/commit/954f40a08f2766fe825ff740080bc335c22f6671), [12b4da8d](https://github.com/juv4uk/sens/commit/12b4da8db9c5d9cc6e697165bc9ec8ea3cc0d46f) | Zig T5 exact-coordinate тести, 59 049 двобайтових фізичних кандидатів, негативи; real T5 harness | Механічний test/source commit ≠ доказ semantic SENS PASS або повної міжмовної матриці на живому корпусі |

За датою UTC D10-коміт має 11.10, а за київським часом та актом ратифікації — 12.10. Не «виправляти» історію коміту, зберегти обидва джерела часу.

## Де проходить семантична межа

**Окремо фіксувати чотири осі:** (1) owner-ratified residency `domain + exact width + bits`, (2) закон/доведений successor, (3) допущений механізм виконання, (4) фізичну підтримку обраного carrier/profile. Перші три осі визначає чинна SENS authority та нативні свідки, Zig/Rust/Python можуть перевіряти фізичний носій і адаптацію, але не ратифікувати значення.

- `D1:0` (NO) — не те саме, що `D3:000` (порожній список); `D1:1` — не `D2:01`. Структура D2 — не числова тотожність. `D7` — текст, його символи `0..9` не стають математикою D24+.
- **Контрприклад історичної колізії:** за [попереднім аудитом](domain-ladder-cutover-2026-10-12.uk.md) `10101000` історично означало `INVOKE`, а нинішня D8-координата цих самих восьми бітів означає `ROUND`. Без незалежно доведеного successor — тільки локальна *можливість розв'язати цікаву задачу*, не blind replace.
- Для QUOTE перевіряти exact current identity раніше за D7; двозначний `MAP` у D6/D8 потребує кваліфікації; невідоме quoted datum не отримує права виклику. [Закон цитат](../QUOTED-DATA-AND-STRING-ADMISSION-LAW-2026-10-13.uk.md).
- `docs/language-core-axioms.md` має власне маркування **DRAFT, NOT RATIFIED** і є історичним/концептуальним матеріалом. Знайдена там стара аксіома чи схема не замінює сучасні `language-contract.lisp`, ратифікаційні файли й тестований закон. Історію не переписувати заднім числом.

## Механічний профіль, який не можна підмінювати семантикою

- Zig 0.16: `research/zig-codecs/t5/t5.zig` — `encode/decode/validatePhysical` до **D9**; `encodeCoordinates/decodeCoordinates/validateCoordinatesPhysical` до **D10**, лише фізична координата. D11 поза обома Zig T5 профілями, навіть за існування ratified **testing** vocabulary.
- **Спостережений неузгоджений профіль міграційних інструментів:** `scripts/sens_t5_codec.py` фізично має `BITS=[01]{1,11}`, `parse_words`/raw decode до W11, але `encode_projection` суворіший (D1–D9, D10 runtime admission не дає). Це походить із D11 [commit 0b4fceac](https://github.com/juv4uk/sens/commit/0b4fceac9074ab683571bebf0fc8f577cfd51b30). **Не** подавати raw W11 Python-файл у Zig coordinate-only D10 як «ті самі допустимі входи». Для кожної конкретної конверсії заявити профіль та очікувану ширину; D11-only — окремий, непідмінений маршрут, без глобального HOLD.
- T5 здатен прийняти канонічний коротший носій після фізичного усічення довшого; тому втрата байтів, яка створила інший валідний T5, виявляється через *зовнішні очікувані length+SHA-256*, не самодостатнім decode. FNV-64 придатний для швидкої некриптографічної статистики, але не замінює SHA-256-рецепт корпусу.
- Наявні `research/zig-codecs/tools/parity_corpus.py`, `t5_corpus_snapshot.py` та [PR #5781](https://github.com/juv4uk/sens/pull/5781) слід **дедуплікувати**, не створюючи третю незалежну нормативну модель маніфесту. SHA і tracked-membership — механічна підготовка, не сам parity Zig↔Rust.

## Мінімальний маршрут однієї міграції для рою

1. **Чинний main + час виникнення зміни.** Зберегти `git rev-parse HEAD`, `git log --follow --format=fuller -- <path>`, `git show --format=fuller <change_sha> -- <path>`, за необхідності `git log -S'<old_fragment>' -- <path>`. Якщо файл вже змінювався паралельно — перечитати його blob SHA і зробити HANDOFF у [#5029](https://github.com/juv4uk/sens/issues/5029); не перезаписувати.
2. **Семантичний доказ на рівні кожної форми.** `source path@blob` → старий token/AST та закон у той історичний момент → сучасна ратифікована `(domain,width,bits)` з **чинних** `lib/domains/dN.lisp`, `knowledge/*ratified*`, `language-contract.lisp` → окремий статус механізму. Не встановлювати відповідник за збігом байта; невизначеність ізолювати до конкретної форми.
3. **Зберегти цитату, структуру, бітність.** D2-структура/QUOTE/COND/лексичне зв'язування/провідні нулі не повинні змінити закон; не вставляти числовий посередник. Не підмінювати D7 текстом функцію, що має current-domain identity.
4. **Три same-stem проєкції:** `name.lisp` (чинна `ук` поверхня) → `name.sens` (canonical T5) → `name` (згенерований exact 0/1 view); зафіксувати blob+SHA кожної, кодек/профіль, версію інструментів та повторне encode/decode byte-exact. F3C — окреме явне `.senc`, не автоматичне переписування оригінальної `.sens`.
5. **Два різних типи свідків:** Zig↔Rust bytes/typed words/негативи = **MECHANICAL TRANSPORT**; виконаний нативний бінарний SENS positive + one-bit negative із шляхом, SHA, командою та actual verdict = **SEMANTIC**. Не виводити друге з першого.
6. **Звіт READY → один інтегратор:** exact write-set, base/current SHA, source і target SHA, перша відмінна позиція при fail, команда відтворення, реальні CI URL і статуси. Нерозв'язана форма — вузька «можливість розв'язати цікаву задачу» з причиною/власником, а не заборона всього рою. Ніякого самовільного merge, force-push, обходу RED чи нового автоматичного workflow.

## Межа цього документа

Це тільки handoff із Git-походженням і повторюваними кроками. Він **не** ратифікує код, не змінює D11, D8, QUOTE або D24+, не створює окремого оракула і не свідчить про повну готовність міграції. Перед роботою читати [CURRENT.md](../../CURRENT.md), [чинні директиви](../../AGENTS.md), відповідні ратифікаційні артефакти й останні коментарі #5029.
