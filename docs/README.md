# Документація SENS

Це коротка карта **актуальної** документації. Датовані матеріали в `docs/research/` і `docs/archive/` зберігають історію дослідження, але не переважають чинний контракт.

## Почати звідси

1. [`../README.md`](../README.md) — огляд проєкту.
2. [`../language-contract.lisp`](../language-contract.lisp) — машинна конституція, Contract 11.9 (D10 whole-domain ratified; D24+ numeric ratified; D10 T5 gated).
3. [`domain-paradigm.uk.md`](domain-paradigm.uk.md) — домени, закони й генеративний ріст.
4. [`language-core.md`](language-core.md) — технічна exact-domain модель.
5. [`semantic-authority-map.md`](semantic-authority-map.md) — що має семантичну владу.
6. [`project-reality-2026-10-12.uk.md`](project-reality-2026-10-12.uk.md) — актуальний зведений стан D10, Nano-SENS, бенчмарк-лабораторії та фізичних кодеків.

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
- `../knowledge/d10-v18-semantic-inventory.json` — повний 1024/1024 каталог D10; окремий акт цілісної ратифікації: `../knowledge/d10-owner-whole-domain-ratification-20261012.json`.

D10 ratification — нормативне рішення над повним каталогом, але не свідчення, що кожний закон independently verified або що D10 допущений до T5/physical runtime.

Колонки: `ук → укр → san → en → LISP → sym`.

D7 має 126 semantic rows; `0100001` і `0101010` owner-reserved. D8 owner-ratified 256/256 під #3960. D9 owner-ratified 512/512 під #4008 і має canonical human table `../lib/domains/d9.lisp`; нормативна machine-readable карта — `../knowledge/d9-ratified.json`.

## Human surfaces

- [`uk-surface-naming.md`](uk-surface-naming.md) — коротке `ук`, повне `укр`, selector-`п/р`, `?`, `!`.
- [`ukrainian-api.md`](ukrainian-api.md) — сучасний український surface-довідник без дублювання таблиць.
- [`program-surface-translator.md`](program-surface-translator.md) — механічний переклад source spellings через exact-domain projections.
- [`domain-surfaces-d7.md`](domain-surfaces-d7.md) — специфіка D7 sound/text surfaces.
- [`domain-surfaces-d8.md`](domain-surfaces-d8.md) — специфіка D8 human surfaces.
- [`domain-surfaces-d9.md`](domain-surfaces-d9.md) — D9 512/512 human projection і межа W9 runtime.

## Бенчмарк-лабораторія та поточні докази

- [`project-reality-2026-10-12.uk.md`](project-reality-2026-10-12.uk.md) — робоча картина і правила інтерпретації результатів.
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
