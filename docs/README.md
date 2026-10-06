# Документація SENS

Це коротка карта **актуальної** документації. Датовані матеріали в `docs/research/` і `docs/archive/` зберігають історію дослідження, але не переважають чинний контракт.

## Почати звідси

1. [`../README.md`](../README.md) — огляд проєкту.
2. [`../language-contract.lisp`](../language-contract.lisp) — машинна конституція, Contract 11.8.
3. [`domain-paradigm.uk.md`](domain-paradigm.uk.md) — домени, закони й генеративний ріст.
4. [`language-core.md`](language-core.md) — технічна exact-domain модель.
5. [`semantic-authority-map.md`](semantic-authority-map.md) — що має семантичну владу.

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

Колонки: `ук → укр → san → en → LISP → sym`.

D7 має 126 semantic rows; `0100001` і `0101010` owner-reserved. D8 owner-ratified 256/256 під #3960. D9 owner-ratified 512/512 під #4008; нормативна machine-readable карта — `../knowledge/d9-ratified.json`.

## Human surfaces

- [`uk-surface-naming.md`](uk-surface-naming.md) — коротке `ук`, повне `укр`, selector-`п/р`, `?`, `!`.
- [`ukrainian-api.md`](ukrainian-api.md) — сучасний український surface-довідник без дублювання таблиць.
- [`program-surface-translator.md`](program-surface-translator.md) — механічний переклад source spellings через exact-domain projections.
- [`domain-surfaces-d7.md`](domain-surfaces-d7.md) — специфіка D7 sound/text surfaces.
- [`domain-surfaces-d8.md`](domain-surfaces-d8.md) — специфіка D8 human surfaces.

## Реалізація та conformance

- `../crates/sens/` — Rust reference mechanism.
- `../tests/fixtures/conformance.lisp` — observable conformance.
- `../.github/workflows/domain-tables.yml` — guard канонічних domain tables.
- `../scripts/check-domain-tables.py` — перевірка повноти, координат, marker-grammar і surface-колізій.

## Історія та research

`docs/research/` і `docs/archive/` можуть містити старі координати, старі назви, D8-research твердження або flat Sens8/Sid8 модель. Це provenance, а не current authority.
