# Як рахувати справжню міграцію SENS між двома Git-комітами

**Дата:** 2026-10-09. **Координація:** #4449. **Статус:** read-only аудит механічних файлів Git, не семантичний оракул.

## Власникові три представлення

1. `path/name.lisp` — канонічна українська `ук` проєкція.
2. `path/name.sens` — фізичний файл T5 (п'ять тритів у байті, `2` лише між словами, 0–4 фінальних pad-`2`, без EOS `22`).
3. `path/name` — однорядкове ASCII `0/1` подання, один звичайний пробіл між точними словами і один LF.

Скрипт `scripts/report_migration_git_delta.py` читає ДВА незмінні Git refs через `git ls-tree`/`git show`. Для кожної same-stem пари він перевіряє реальний packed T5, exact-width typed words, фізичний SHA, T5 byte-to-byte re-encode, канонічний view та UTF-8 оригіналу. Вся робота read-only, без зміни вихідних файлів.

**Нове = лише дельта між двома комітами.** Раніше додані тестові fixtures не є новими міграціями; і нові тестові fixtures рахуються окремо від бібліотечних файлів. Пара без текстового view або view без точного відновлення байтів отримує статус `INVALID_OR_INCOMPLETE_TRIPLE`.

**Критично:** механічна byte/word parity не є незалежним semantic-oracle proof. Навіть status `MECHANICAL_TRIPLE_VERIFIED` не підтверджує виконуваність чи канонічність української поверхні. У звіті `oracle_certified_original_executables=null` — потрібні окремі witnesses. Це захищає від штучного завищення кількості мігрованих програм.

## Команди

```sh
git fetch origin main
BASE="$(git merge-base HEAD origin/main)"
HEAD="$(git rev-parse HEAD)"
python3 scripts/report_migration_git_delta.py --base "$BASE" --head "$HEAD" --strict > migration-delta.json
python3 -m unittest discover -s tests -p test_report_migration_git_delta.py -v
```

## Відомий вимір

На перевіреному `main@c815df12`: **503 файли `.lisp`, 13 пар `.sens`, 13 текстових view, 490 без `.sens`**. З 13 пар 12 припадають на `tests/fixtures` і лише одна — на `lib/surface/ukr-acceptance`, яка сама по собі не доводить виконувану семантичну тотожність. Це НЕ 13 нових оригінальних сертифікованих програм.

Причина малого числа: поточний аудит #4449 розділяє 211 історичних `.lisp` як data/archive і 279 як active/UNKNOWN, де W8-source provenance, Text7 binder/role, D2 structural authority, Number/D24+ або відсутність незалежного оракула залишаються реальними бар'єрами. Жоден скрипт не повинен вигадувати їхні значення.

Суміжні інструменти: `scripts/migrate.py`, `scripts/migrate-t5-batch.py`, `scripts/report_original_migration_candidates.py`, `scripts/publish_verified_uk_triplets.py`. Цей Git-delta скрипт **доповнює**, а не замінює їх.

Пара без правильного текстового view не вважається новою перевіреною трійкою. Звіт окремо рахує нові фізичні пари, готові механічні трійки і ремонт неповних старих пар; semantic oracle proof залишається окремим.
