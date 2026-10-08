# Міграція `.lisp` → однойменний фізичний `.sens` (T5)

**Рішення власника 2026-10-08.** Старі міграційні файли **без розширення заборонено публікувати як код SENS**. Старий `name` без суфікса не є новим артефактом. Джерело лишається `name.lisp` як оригінал/провенанс; нова ціль **`name.sens` із байтовим T5**. Самі джерела не видаляємо.

## Канонічна фізика

Двійкові source слова: D1..D9 exact width, символи `0` і `1`. Лише файловий транспорт має логічний трит `2` МІЖ сусідніми словами; кожні 5 тритів — один фізичний байт в межах `0..242`. У файлі немає ASCII-рядка `1012...` та немає видимих пробілів. Немає `22` після останнього слова. Кінець — фізичний EOF; 0..4 трити `2` добивають останній байт. `sens-trit open` виводить слова із звичайними пробілами, які НЕ записані у файлі. D2 і D7 недоторкані.

**Приклади**:

```text
source: examples/demo.lisp
target: examples/demo.sens           (той самий базовий шлях, не examples/demo)
typed words: 10 | 001 | 00 | 000 | 01
T5 physical (hex): 63 89 06 A1   # 4 байти
open viewer: 10 001 00 000 01   # людська проєкція, не вміст файла
empty symbol: () → 000, T5 physical byte 00
```

## Шлях 1: три проходи історії

```sh
python3 scripts/migrate-three-pass.py . \
  --out /tmp/sens-t5-mirror \
  --foundation knowledge/d1-d7-foundation.json \
  --domain-surfaces crates/sens/src/domain_surface_registry_generated.rs \
  --semantic-generated crates/sens/src/semantic_registry_generated.rs \
  --semantic-registry crates/sens/src/semantic_registry.rs \
  --necessary-forms crates/sens/src/eval/necessary_forms_generated.rs \
  --historical-map contracts/core1-historical-sid-map.lisp \
  --text7 crates/sens/src/text7_projection_generated.rs \
  --report /tmp/sens-t5-migration-report.json \
  --dry-run
```

Після аналізу `--dry-run` прибрати опцію лише для окремого затвердженого підкорпусу. Усі залишкові текстові назви, невідомі функції/числа, UTF-8/ASCII-вставки та нескінченні/невалідні форми блокують **окремий файл**; скрипт не повинен створити `*.sens` із частково кодованою програмою.

## Шлях 2: manifest-first

```sh
python3 scripts/migrate-to-sens-codes.py /path/to/approved-corpus \
  --foundation knowledge/d1-d7-foundation.json \
  --sens-mirror /tmp/sens-t5-mirror \
  --report /tmp/sens-manifest-report.json
```

`--binary-mirror` залишений тільки як дослідне видиме `0/1` **стейджингове подання**. Його ніколи не можна трактувати як готовий фізичний `.sens`! Новий `--sens-mirror` пише тільки справжні байти. Будь-які старі `.sens` у джерелах не можна читати як UTF-8 `.lisp`.

## Безпека й CI

- `write-new-only`: будь-який існуючий `name.sens` — blocker. Запис нового файла через атомарне створення без перезапису. Багаторазовий запуск без очищення вихідного mirror не повинен непомітно переписати артефакти.
- Фізична тотожність: `T5_decode(T5_encode(words)) == exact typed words`, `T5_encode(T5_decode(bytes)) == bytes`; `typed_sha256` включає довжину КОЖНОГО слова, а `physical_sha256` — байти файла.
- Окремо перевіряти D2 parse та SENS oracle evaluation parity; Python T5 roundtrip — НЕ повна семантична ратифікація. Не видавати blocked output за готовий `.sens`.
- Масове переписування `master` через `git rm`, або пуш конвертованих файлів напряму без PR — ЗАБОРОНЕНО. Старий workflow замінено preview artifact без дозволу на write до репозиторію.
- Розподіляти реальні `.lisp` по взаємовиключних каталогах, один агент — один PR, а файл без доведеного відображення відкладати в blocker ledger.

**Задачі:** [головна #4449](https://github.com/juv4uk/sens/issues/4449); [фізичний T5 #4446](https://github.com/juv4uk/sens/pull/4446); [конвертер #4450](https://github.com/juv4uk/sens/issues/4450); [маніфест #4451](https://github.com/juv4uk/sens/issues/4451); [CI #4452](https://github.com/juv4uk/sens/issues/4452).

73.

## Короткий запуск чинного мігратора

Конвертер має вбудовані шляхи до поточної ратифікованої D1–D9 основи, generated surfaces, history map та Text7. Тому окремий підтверджений файл запускається **без переліку всіх реєстрів**:

```sh
python3 scripts/migrate-three-pass.py \
  tests/fixtures/migration-multiform-cohort/two-forms.lisp \
  --out /tmp/sens-one --source-era legacy
```

Результат: `/tmp/sens-one/two-forms.sens` — **фізичний T5**, а звіт — `/tmp/sens-one.report.json`. Оригінальний `.lisp` залишається незмінним, наявні `.sens` у mirror не перезаписуються.

Для **саме ще не переведених** вихідних файлів, без повторного підрахунку вже наявних T5-пар:

```sh
python3 scripts/migrate-three-pass.py . \
  --out /tmp/sens-unpaired-audit \
  --unpaired-only --dry-run --source-era legacy
```

`files_skipped_paired` показує кількість пропущених пар; `files_seen` і `files_blocked` належать до тих, які сканувалися. Жоден `.sens` у режимі `--dry-run` не створюється.

**Важлива неоднозначність восьми бітів:** `--source-era legacy` означає історичний SID8; `--source-era current` з ратифікованим D8 фундаментом залишає сучасний D8; `--source-era auto` блокує неоднозначний W8 head, не вгадує за формою бітів. Для змішаного корпусу спочатку класифікуйте походження файлів, тоді запускайте обмежені підкорпуси. Чинний D8 resident сам по собі **не доводить викликуваності**.

Механічний T5 roundtrip **не є** oracle-parity. Нерозпізнані binders, текст, числа та host-ефекти залишаються BLOCKED, без псевдоконвертації.
