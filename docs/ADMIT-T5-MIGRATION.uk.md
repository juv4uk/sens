# Міграція з доказом: один оригінальний `.lisp` → фізичний `.sens`

Команда: `python3 scripts/admit-t5-migration.py --help`.

Цей інструмент — **допуск** реального файла, а не четвертий перекладач і не
обхід мови. Повторно використовує чинний `scripts/migrate-three-pass.py`,
`scripts/sens_t5_codec.py` і незалежний Rust `sens-trit open`.
Пакетна координація — окремий напрям #4449; цей інструмент приймає **один**
джерельний шлях із наперед визначеним доказом.

## Спершу збери незалежний Rust-рідер

```sh
cargo build -p sens-cli --bin sens-trit
```

## Приклад маніфесту для конкретного старого файла

```json
{
  "schema": "sens-t5-proof-admission/v1",
  "source": "path/to/old-program.lisp",
  "source_era": "historical-legacy",
  "source_git_blob_sha1": "<40 hex of tracked original git blob>",
  "source_sha256": "<64 hex of original source bytes>",
  "expected_physical_sha256": "<64 hex of independently verified packed T5>",
  "expected_typed_sha256": "<64 hex of independently verified typed D1-D9 words>",
  "oracle_commands": [
    ["python3", "tests/test_specific_original_history.py", "-q"],
    ["cargo", "test", "-p", "sens", "--test", "specific_original_current"]
  ],
  "oracle_witnesses": {
    "historical": {"path": "tests/test_specific_original_history.py", "git_blob_sha1": "<40hex>"},
    "current": {"path": "crates/sens/tests/specific_original_current.rs", "git_blob_sha1": "<40hex>"}
  },
  "historical_observation": {
    "command": ["python3", "tests/oracle_for_this_source.py", "{source}"],
    "stdout_sha256": "<64 hex of EXACT historical observable stdout>"
  }
}
```

**Відтепер для кожного справжнього оригіналу** (поза `tests/fixtures/`)
видавець вимагає `historical_observation`. Команда повинна реально
приймати `{source}` — перевірений Git-blob вихідного `.lisp`, а в
`stdout_sha256` записується SHA-256 точних байтів її стандартного виводу.
Скрипт запускає цю команду, перевіряє хеш і потім **самостійно виконує
`sens-trit eval`** на щойно згенерованому фізичному T5-файлі.
Будь-який ненульовий вихід, stderr, порожнє спостереження або найменша
різниця у байтах stdout → **BLOCK до запису**. Історичний та сучасний
оракули повинні бути незалежними, а їхні команди — предметом рев'ю.
Це обмежений доказ спостережуваної поведінки конкретного джерела,
а не доказ усіх 490 файлів, самоінтерпретації чи релізної готовності.

Файли з `tests/fixtures/` — **окрема демонстрація T5**, без підтвердження
поведінки історичної бібліотеки; у звіті для них зазначається
`observable_parity=NOT_VERIFIED_FIXTURE_CANARY`, `release_admitted=false`.
Присвоїти їм право історичної міграції через маніфест неможливо.

Доказ не можна замінювати на фальшивий `true` чи тест іншої програми.
Перевірений тест повинен засвідчувати саме цю програму, її оригінальну
спостережувану поведінку та правильність поточних D1–D9 доменів. Маніфест
підлягає рев'ю.

Спочатку **без запису**:

```sh
python3 scripts/admit-t5-migration.py \
  --root . \
  --manifest /tmp/old-program-proof.json \
  --mirror /tmp/sens-mirror \
  --reader target/debug/sens-trit \
  --report /tmp/old-program-admission.json
```

Якщо результат `VERIFIED_NOT_WRITTEN`, тільки тоді явно публікуй новий бінарний
файл:

```sh
python3 scripts/admit-t5-migration.py \
  --root . \
  --manifest /tmp/old-program-proof.json \
  --mirror /tmp/sens-mirror \
  --reader target/debug/sens-trit \
  --report /tmp/old-program-admission.json \
  --write
```

Після незалежної перевірки вміст нового `/tmp/sens-mirror/path/to/old-program.sens`
можна перенести як фізичний Git blob до однойменного шляху в репозиторії та
провести окрему перевірку PR. Скрипт не зливає самостійно, не рухає піни
компілятора, не стирає вихідний `.lisp` і не переписує існуючий `.sens`.

## Чому BLOCK — правильний результат

- Невідомий historical SID8, непідтверджена функція, локальне перевизначення
  чи неоднозначне 8-бітне D8/SID8 → **BLOCK**.
- `source_era` наразі лише `historical-legacy`; сучасний D8 вимагає іншого
  окремого доказу. Немає автоматичної догадки.
- Невідомі числа / носій D24+, Text7, D1-керування, ефекти хоста чи рекурсія
  не отримують значення за схожістю імен.
- Недійсний Git blob, непогоджені хеші, збій Rust D2 grammar, збій
  цільового оракула, симлінк або вже наявний `.sens` → **BLOCK**, код виходу 2.
- `--write` публікує 5-трит/байт T5 тільки після всіх перевірок через
  атомарне no-clobber hardlink. Файловий EOF — довжина байтів, не `22`.

Тести `tests/test_admit_t5_migration.py` виконують справжній шлях на
вже доведеній програмі `two-forms.lisp` / `two-forms.sens`, включаючи
реальні Python three-pass, Rust reader та Rust oracle. **Це перевірка роботи
інструмента, не міграція одного з початкових 491 заблокованих файлів.**
Для старого оригінального файла потрібен його власний перевірений маніфест
та незалежна спостережувана семантика.


## Як запускати скрипт у справжньому міграційному CI

До інтеграції інструмент існував у main, але workflow запускав лише його
unit-тести. Тепер `.github/workflows/admit-t5-migration.yml` **дійсно
викликає** `scripts/admit-t5-migration.py --write` для кожного рев'юваного
маніфесту `knowledge/migration-admissions/*.json`. Тригери: PR зі змінами
доказів чи мігратора, push у main і ручний `workflow_dispatch`.

GitHub-hosted job компілює справжній Rust `sens-trit`, запускає регресії,
для кожного маніфесту ізольовано мігрує джерело до нового фізичного
`.sens` у тимчасовому mirror, перевіряє T5, D2 та названі oracle-тести,
публікує звіт і байти як artifact `reviewed-t5-migration-admissions`.
`BLOCKED` або порожня черга зупиняють job: нема тихого SUCCESS.
**Ніяких автоматичних комітів з CI чи перезапису джерела.**

Щоб агент вніс **справжній оригінальний** файл, потрібно рев'юваним PR:
1. Додати маніфест `knowledge/migration-admissions/<описова-назва>.json`
   з exact git blob SHA, SHA256 джерела, SHA256 фізичного T5 та typed SHA.
2. Назвати окремий тест, який порівнює спостережувану поведінку історичного
   файла з поточною SENS на цьому конкретному джерелі. Саме присутність
   довільної команди у `oracle_commands` НЕ є семантичним доказом.
3. Дочекатися зеленого CI, перевірити artifact `.sens` і тільки потім
   оформити окремий PR на той самий шлях із `.sens` поруч з `.lisp`.

Початковий контрольний `two-forms-canary.json` — перевірка **роботи
автоматичної черги**, уже наявний тестовий приклад; він **не** зменшує число
оригінальних неперенесених файлів. Маніфести оригінальних програм без
семантичного доказу не додавати. Не дублювати наявні gate у нових скриптах.

## Перевірюваність коду оракулів

Маніфест вимагає рівно два окремі, простежувані Git blob свідки: Python-тест історичного джерела `tests/test_*.py` і Rust-тест поточного SENS `crates/sens/tests/*.rs`. `oracle_witnesses` зберігає для кожного точні `path` і `git_blob_sha1`, а `oracle_commands` запускає відповідні тести. Допуск відхиляє `echo`, `true`, `python -c`, одну-єдину команду, незв'язаний тест, змінений тест або зміну джерела в процесі перевірки. Файли тестів мають прямо називати відповідні `.lisp` та `.sens`.

Це не автоматична математична сертифікація: окреме рев'ю має підтвердити правильність тверджень у тестах. Для оригінальних виконуваних програм також **залишається обов'язковою** незалежна байтова перевірка `historical_observation` проти реального `sens-trit eval` та збереження `expected_current_eval_stdout` для чинного канонічного прикладу. Новий контракт доповнює ці умови, не замінює їх.
