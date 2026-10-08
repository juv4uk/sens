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
    ["cargo", "test", "-p", "sens", "--test", "specific_original_semantic_witness"]
  ]
}
```

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
