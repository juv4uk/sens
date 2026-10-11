# Nano-SENS: наступний вимірюваний крок bootstrap
Дата: 2026-10-11  
Статус: **RESEARCH / NO NEW SEMANTICS / NOT A SIZE-MINIMUM CLAIM**

## Мета

Вивести вже наявний compiler self-hosting доказ у напрямі Nano-SENS: виміряти найменший **довірений початковий seed**, потрібний для відтворюваного запуску SENS-компілятора, не плутаючи його з розміром згенерованого компілятора.

Цей документ доповнює наявний граф #3756 → #3835 → #3822/#3760. Він не створює нової семантичної таблиці, домену або гілки.

## Зафіксована базова точка

У репозиторії вже наявний звіт `evidence/compiler-selfhost-lineage-2026-10-07.json` зі схемою `compiler-selfhost-lineage-report/1` і статусом `pass`.

За цим звітом:

- pinned SENS source SHA: `69d4bb7f8390e431b479eb17ea68dcefb80d04f9`;
- compiler nucleus SHA-256: `ce12207e51256d6b99d0c0dd4aeb3afc9444bec9b710a165a73fed8e12181091`;
- language-contract SHA-256: `177d532d24c1f0738a934152f65c7f01f90b5593c8dbfe519e31148c0aa80c40`;
- structural-law projection SHA-256: `3ce5bb4e042bfec446199a9c77787d0a022109e9a6d6442a4f93b50f68e34e9a`;
- target/profile: `x86_64-linux-gnu`, `SW1+compiler-evidence-canonical/1`;
- toolchain evidence: GCC `13.3.0`;
- C1 і C2 позначені executable; їхні executable SHA-256 рівні: `04f42b9015784a42f6f0fe415fb4b441d4bdbe71c7182ca7fc3240a322ff0ce3`;
- обидва згенеровані C-файли мають однаковий SHA-256: `c142995c434d600cf0751c563309d05883498507bcc32a3546cef495532d892e`;
- звіт декларує, що C0 не читав попередньо створені C1/C2 і що C0 побудував C1, а C1 побудував C2;
- reported C1 executable file size: **92,248 bytes**;
- обраний критерій еквівалентності: `byte-identical-artifact`.

Перевірка валідатора вже існує: `scripts/validate-compiler-selfhost-lineage.py`; контракт лінії доказів: `contracts/compiler-selfhost-lineage-v1.lisp`.

### Що це доводить — і чого ні

Це зафіксована доказова точка компіляторного покоління C1/C2, а не доказ мінімальності seed. **92,248 байтів — це заявлений розмір C1 executable у звіті; його не можна називати розміром довіреного C0/seed.** Звіт також не доводить автоматично паритет з усім золотим корпусом GAS/NASM.

## Наступний зріз: Nano-SENS size report

Перед оптимізацією потрібно отримати повторюваний вимір із чистого середовища та розділити щонайменше такі величини:

1. **Trusted seed bytes** — точні байти програми/виконуваного файла, без яких bootstrap не стартує; об'єкт виміру має бути явно названий і pinned.
2. **C1 executable bytes** — окремий результат компіляції ядра; не підставляти цей розмір замість seed.
3. **On-disk bytes / loadable bytes / code-section bytes** — різні метрики, якщо інструменти їх надають; не віднімати символи, debug-дані або секції мовчки.
4. **External bootstrap dependencies** — toolchain, linker, shared libraries, shell/process orchestration та інші залежності зазначити окремо, не приписуючи їх SENS-коду.
5. **Reproducibility** — SHA-256 кожного артефакту, повна версія toolchain, target/ABI, прапорці збірки й точний спосіб отримання байтового розміру.

Машиночитний звіт варто версіонувати як `nano-sens-size-report/1` і зберігати поруч із lineage evidence. Це **нова форма спостереження про розмір**, а не нове джерело семантичної влади.

## Вимірювальний інструмент додано

У `main` додано `scripts/measure-nano-sens-size.py`. Він:
- рахує точні file bytes та SHA-256 окремо для явно названого seed і C1 executable;
- приймає лише `compiler-selfhost-lineage-report/1` зі статусом `pass`, перевіряє pinned SENS revision, покоління C1/C2, fresh-bootstrap прапорці, C1 SHA та розмір проти lineage report;
- відмовляється створювати звіт, якщо provenance/розмір не збігаються;
- позначає секції ELF/PE, loadable segments, залежності toolchain, мінімальність і повний GAS/NASM паритет як невиміряні, доки для них немає окремих спостережень.

Локально перевірено `python3 scripts/measure-nano-sens-size.py --self-test`: **PASS**, п’ять позитивних тверджень і три негативні контролі (неправильний розмір, читання попереднього C1, нерівні фізичні байти C1/C2). Опційний `--c2-executable` перевіряє фактичний файл C2, а не лише хеш у звіті. Також пройшов `python3 -m py_compile`. Це перевірки самого вимірювального інструмента, не новий запуск компілятора.

Існуючий workflow `.github/workflows/compiler-selfhost-lineage-contract.yml` тепер має запускати цю перевірку для змін інструмента та контракту лінії доказів. Статус віддаленого Actions-run ще не підтверджений.

Вимір seed поки **BLOCKED** на визначенні й отриманні точного файлу C0/seed і C1 executable відповідного pinned lineage. Старий звіт має C1 hash/розмір, але немає доступного workflow artifact у збережених артефактах зазначеного run; не підміняти бінарний файл даними з JSON і не називати виміряним seed рядок у source.

## Виконуваний вхід до SENS-компілятора

Додано команду оболонки `cargo xtask compiler-compile`, яка з'єднує вже наявні codec і SENS-written compile body:

```text
canonical sens-syntax-wire/1 (SW1) bytes
  -> wire_decode_program + exact byte roundtrip
  -> lowered_program_to_exact_data (representation conversion only)
  -> lib/compiler-nucleus.lisp:
       compiler-compile-program-artifact
  -> compiler-compilation-artifact/1 or compiler-compilation-error/1
  -> canonical compiler-evidence bytes
```

Приклад:

```sh
cargo xtask compiler-compile --input /path/to/program.sw1 --out /path/to/new-artifact.bin
```

- `--input` має містити саме canonical SW1 bytes; це внутрішній compiler-program-data transport, **не** фізичний T5 `.sens` або opt-in F3 `.senc`. Формати не визначаються sniffing і не підміняють один одного.
- `--out` — новий файл; наявний шлях не перезаписується.
- Команда використовує Git HEAD як provenance revision. SENS обирає запити/ролі та складає весь program artifact; wrapper виконує лише codec roundtrip, representation conversion, provenance та канонічний evidence encode/decode.
- Семантична відмова зберігається як канонічний `compiler-compilation-error/1` артефакт і повертає ненульовий exit code. Невалідний/неканонічний SW1 не запускає compiler.
- Додано локальні unit-тести в `crates/xtask/src/compiler_compile.rs` для повторюваного артефакту, roundtrip verification, неправильного wire та D8 fail-closed. Workflow `.github/workflows/compiler-role-cutover.yml` містить команду `cargo test -p xtask compiler_compile::tests -- --nocapture`; віддалений результат цього запуску потрібно підтвердити окремо.

### Під’єднання наявної трифайлової проєкції

Для вже підготовленої трійки тепер передбачено окремий явний режим:

```sh
cargo xtask compiler-compile --triplet /path/to/program.sens --out /path/to/new-artifact.bin
```

Шлях `/path/to/program.sens` має мати двох однойменних сусідів: `program.lisp` та файл без розширення `program`. Контракт наявних інструментів:
- `scripts/stage-two-projections.py` готує тільки український `.lisp` і читабельний exact-width файл `program`; сам він фізичний `.sens` не створює.
- `scripts/sens_view.py parse /path/to/program` використовує існуючий T5 codec, щоб отримати `program.sens`. Це не перейменування тексту.
- `scripts/verify_uk_t5_triplet.py` — read-only перевірка трійки у своєму обмеженому D1/D2/D3/D4 корпусі; його статус не є доказом runtime-семантики або release admission.

Режим `--triplet` читає саме фізичний T5, отримує слова через чинний SENS-рідер, перевіряє байтову тотожність розгорнутого view і повторного T5-кодування, після чого незалежно парсить/опускає джерело та бітовий view і вимагає однакового exact-domain результату. Далі викликається той самий компіляторний корпус у `lib/compiler-nucleus.lisp`. Артефакт зберігає SHA-256 канонічного SW1-кодування exact-domain програми, як вимагає поле `program_wire_sha256`; фізичний `.sens` проходить окрему байт-до-байта перевірку T5, але його SHA не підставляється в поле SW1 provenance. Symlink/non-regular inputs і наявний output відхиляються.

`--input` і `--triplet` взаємовиключні та не визначають формат за вмістом: перший залишається SW1 bootstrap-входом, другий — фізичною T5 трійкою. Це з’єднує готові кодеки з компілятором, але не означає, що увесь `lib/compiler-nucleus.lisp` вже пройшов міграцію в обмежений корпус трифайлового конвертера.

Це executable front-end до наявного SENS-written компілятора, але ще не машинний backend та не повний C1 → C2 self-host proof.

## Acceptance gates

- [ ] З чистого checkout і без читання заздалегідь зібраного C1/C2 повторно запустити чинний self-host lineage flow.
- [ ] До вимірювання визначити seed-артефакт і точну межу того, що рахується його фізичними байтами.
- [ ] Два незалежні чисті запуски дають однакові pinned-входи та відтворювані виміри; рівність SHA вимагати для однакових детермінованих артефактів, а відмінності середовища записувати, не нормалізувати мовчки.
- [ ] Перевірити lineage report наявним валідатором; не послаблювати критерій `byte-identical-artifact` після його успіху.
- [ ] Окремо звіряти спостережуваний результат і точні байти для тих випадків золотого GAS/NASM корпусу, де контракт вимагає byte identity.
- [ ] Кожне зменшення seed проходить той самий функціональний корпус, негативні fail-closed випадки та lineage перевірки.
- [ ] Публікувати мінімальний розмір тільки після вимірювання; не використовувати «десятки байтів» як незасвідчену ціль або заявлений результат.

## Семантичні межі

- Чинна влада — Contract 11.8 / owner-ratified D1–D9; D10 лишається research/unratified і не є залежністю Nano-SENS.
- Історичні Lisp-кандидати можуть бути донорськими тестами/джерелами, але не додають значень до ядра без окремого закону, позитивного свідка, falsifier та перевірки дублювання.
- Мова визначає значення; CML, компілятор bootstrap, linker, GAS/NASM і цільова машина забезпечують механізми та свідків, а не другу таблицю семантики.
- Невідомий домен, невідповідний provenance, unsupported lowering або нерівний observable мають залишатися категоризованими FAIL/BLOCKED, а не виправлятися fallback.

## Власник наступної дії

Продовжити в межах наявних #3835 / #3822 / #3760: спершу зробити seed-метрику відтворюваною, потім оптимізувати фізичний результат, зберігаючи чинний доказ C1/C2. Нову гілку й окремий домен для Nano-SENS не створювати.
