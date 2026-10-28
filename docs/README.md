# Документація SENS

Це навігація до **чинних джерел**, а не дубль контракту. Нормативна семантика належить ратифікованим законам і доменам; реалізаційні новини не змінюють її. Матеріали з датою, зокрема звіт від 12.10.2026, — зріз на вказаний день, **не** статус сьогоднішнього CI. Датовані матеріали в `docs/research/` та `docs/archive/` лишаються історією.

## Почати звідси

1. [`../CURRENT.md`](../CURRENT.md) — чинна влада й зафіксований стан реалізації; джерело для розв'язання суперечностей.
2. [`../README.md`](../README.md) — короткий огляд, запуск і відмінність `.lisp` / `.sens` / видимого бітового перегляду.
3. [`../contracts/language-contract-12.lisp`](../contracts/language-contract-12.lisp) — новий канонічний Contract 12.0; [`../language-contract.lisp`](../language-contract.lisp) лишається сумісною точкою входу.
4. [`domain-paradigm.uk.md`](domain-paradigm.uk.md), [`language-core.md`](language-core.md), [`semantic-authority-map.md`](semantic-authority-map.md) — домени, фізичні носії, межі семантичної влади.
5. [`SENS-LISP-TO-T5-MIGRATION-2026-10-08.uk.md`](SENS-LISP-TO-T5-MIGRATION-2026-10-08.uk.md) — датована історія міграції; назва зберігає тогочасний T5, поточний фізичний шлях описано як T5M.
6. [`project-reality-2026-10-12.uk.md`](project-reality-2026-10-12.uk.md) — **архівний за датою** звіт про D10, Nano-SENS та фізичні кодеки, не поточна обіцянка готовності.

## Поточна математична межа та реалізація

- `*.lisp`: повні людські викличні голови `укр` із ратифікованих таблиць та українська клавіатурна поверхня. Цифрові викличні голови, числові літерали, сирі бітові виклики й активні SID8/Sens8-голови заборонені; числові значення будуються з українських спискових даних та арифметики.
- Математична драбина починається з D12: **D12/D24/D48/D96/D192/…**. Окремі source projection і сумісні reader-и можуть мати інший мінімум ширини; це не змінює першого числового домену.
- `crates/sens/src/source_projection.rs`: точне зниження десяткових цілих залежить від вибраного профілю мінімальної ширини; wrapper сумісності може лишатися D24-first, тоді як спеціальний профіль явно вибирає D12. Це не повна реалізація довільних дробових source-літералів.
- `*.sens`: справжні T5M-байти; `name` без розширення поруч із `name.lisp` / `name.sens` — лише похідний видимий бітовий перегляд, що не створює іншої семантики.
- Відображення SID8/Sens8 на ратифіковану драбину перевіряється через **історичну роль**, не рівність 8 бітів з D8. Усі заперечення мають бути локальними з командою відтворення.
- [Центральний CI](../.github/workflows/ci.yml): GitHub-hosted Ubuntu 24.04; поточні push-запуски **не скасовуються** новими (`cancel-in-progress: false`); `queue: max` залишає до 100 очікуваних runs на групу, після чого GitHub може відхиляти нові. Це не означає, що тести пройшли.

## Канонічні human tables

Повні human-readable проєкції живуть **по одному домену на файл**:

- `../lib/domains/d1.lisp`
- `../lib/domains/d2.lisp`
- `../lib/domains/d3.lisp`
- `../lib/domains/d4.lisp`
- `../lib/domains/d5.lisp`
- `../lib/domains/d6.lisp`
- `../lib/domains/d7.lisp`
- `../lib/domains/d8.lisp`
- `../lib/domains/d9.lisp`
- `../lib/domains/d10.lisp`
- `../lib/domains/d11.lisp` — лише 43 тестові ратифіковані ідентичності; 512 selector-кандидатів — дослідження, не callable Core.
- `../knowledge/d10-v18-semantic-inventory.json` — повний 1024/1024 каталог D10; окремий акт цілісної ратифікації: `../knowledge/d10-owner-whole-domain-ratification-20261012.json`.

D10 ratification — нормативне рішення над повним каталогом, але не свідчення, що кожний закон independently verified або що D10 допущений до фізичного T5M runtime.

Колонки: `ук → укр → san → en → LISP → sym` (у виконуваному людському `.lisp` викличні голови беруться з **повної** `укр`, не компактної `ук`).

**Чинна D7 — keyboard/v2, 128/128** семибітових текстових координат (ратифікація власника 13.10.2026): [`knowledge/d7-keyboard-v2-ratified.json`](../knowledge/d7-keyboard-v2-ratified.json), [`lib/domains/d7.lisp`](../lib/domains/d7.lisp). Координати `0100001` і `0101010` були зарезервовані **тільки в історичній звуковій v1 (126/128)**. **За D7 v1 нічого не встигли мігрувати**, тому нові програми використовують чинну D7 v2 без будь-якої процедури v1→v2 або додаткового міграційного блокування. D7 — дані/текст, не числа й не callable Core. D8 owner-ratified 256/256 під #3960. D9 owner-ratified 512/512 під #4008; нормативна машинна карта — [`knowledge/d9-ratified.json`](../knowledge/d9-ratified.json), людська — [`lib/domains/d9.lisp`](../lib/domains/d9.lisp).

## Human surfaces

- [`uk-surface-naming.md`](uk-surface-naming.md) — коротке `ук`, повне `укр`, selector-`п/р`, `?`, `!`.
- [`ukrainian-api.md`](ukrainian-api.md) — сучасний український surface-довідник без дублювання таблиць.
- [`program-surface-translator.md`](program-surface-translator.md) — механічний переклад source spellings через exact-domain projections.
- [`d7-keyboard-v2.uk.md`](d7-keyboard-v2.uk.md) — **чинна** D7 v2: клавіатурні/text-проєкції, точна бітність і профіль декодування.
- [`domain-surfaces-d7.md`](domain-surfaces-d7.md) — **архівна D7 v1** (126/128), звукова карта та історична provenance; не кодувати нові дані за нею.
- [`domain-surfaces-d8.md`](domain-surfaces-d8.md) — специфіка D8 human surfaces.
- [`domain-surfaces-d9.md`](domain-surfaces-d9.md) — D9 512/512 human projection і межа W9 runtime.

## Бенчмарк-лабораторія та поточні докази

- [`project-reality-2026-10-12.uk.md`](project-reality-2026-10-12.uk.md) — **датований звіт на 12.10**, не поточний вердикт усього CI.
- [`../benchmarks/README.md`](../benchmarks/README.md) — **згенерований** індекс зареєстрованих стендів та окрема таблиця support-exemptions; не редагувати вручну.
- [`../evidence/benchmark-sweep-2026-10-12.json`](../evidence/benchmark-sweep-2026-10-12.json) — повний sweep 54/54 зі збереженими чотирма FAIL, без оголошення глобального green.
- [`../benchmarks/support-exemptions.json`](../benchmarks/support-exemptions.json) + [`../benchmarks/support-exemptions.schema.json`](../benchmarks/support-exemptions.schema.json) — явно перевірені support-каталоги, які не є benchmark stands; `scripts/benchmark_registry.py --coverage` показує решту backfill debt #4172, а `--strict` лишається фінальним воротом.
- [`research/nano-sens-seed-v0-20261012.uk.md`](research/nano-sens-seed-v0-20261012.uk.md) — виміряний Nano-SENS baseline з відкритим seed closure.
- [`../evidence/nano-sens-static-source-edges-2026-10-12.json`](../evidence/nano-sens-static-source-edges-2026-10-12.json) — receipt успішного статичного source-edge аудиту (окремо від повного seed-closure gate).
- [`benchmarks/2026-10-09-domain-occupancy-bitmask.uk.md`](benchmarks/2026-10-09-domain-occupancy-bitmask.uk.md) — історичний occupancy-механізм; його старі виміри не переіменовуються в D10 runtime-admission доказ.

## Реалізація та conformance

- `../crates/sens/` — Rust reference mechanism.
- `../tests/fixtures/conformance.lisp` — observable conformance.
- `../.github/workflows/domain-tables.yml` — guard канонічних domain tables.
- `../scripts/check-domain-tables.py` — перевірка повноти, координат, marker-grammar і surface-колізій.

## Історія та research

`docs/research/` і `docs/archive/` можуть містити старі координати, старі назви, D8-research твердження або flat Sens8/Sid8 модель. Це provenance, а не current authority.
