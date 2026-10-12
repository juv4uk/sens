# Nano-SENS: наступний вимірюваний крок bootstrap
Дата: 2026-10-11  
Статус: **RESEARCH / NO NEW SEMANTICS / NOT A SIZE-MINIMUM CLAIM**

## Оновлення 2026-10-12 — перше відтворюване число

Live lineage flow пройшов у [CML run 38187859376](https://github.com/juv4uk/cml/actions/runs/38187859376), на CML commit `ec4ba010cebd9fdc37b39224142dcac3ee907cfe`, з pinned SENS source `d0787a40fcea36501747732aa61b6de19fe29c70`. Два незалежні clean-run jobs і job порівняння — **PASS**; кожен прогнав 189/189 тестів.

Перше підтверджене число Nano-SENS — **34,623,904 байти** для явно визначеного компонента `seed-v0-c0-runner.bin` (CML Rust lib-test bootstrap runner). Для цього самого ELF виміряно 6,042,632 байти завантажуваних сегментів і 4,147,007 байтів виконуваних code sections. Це розмір runner-компонента, **не** повний розмір seed і не мінімальність.

C1 і C2 кожен мають **92,248 байтів**, а їхні executable SHA-256 тотожні: `27b8fbf096cddbb77be2b4bf57cc58bf8b4fac4accc42adbcfbc10d6cd95f375`. Обидва покоління побудовані заново: C0 створив C1, C1 створив C2, без читання заздалегідь зібраних C1/C2. Два звіти розміру побайтно однакові: SHA-256 `dccd8748fcb47eb79ba10f22901534feeb30a7931f8310fedb95c0cf339f6aca`; чинний критерій лишається найсильнішим `byte-identical-artifact`.

Raw артефакти збережені на 30 днів: [clean run 1](https://github.com/juv4uk/cml/actions/runs/38187859376/artifacts/11720512293), [clean run 2](https://github.com/juv4uk/cml/actions/runs/38187859376/artifacts/11720585831), [підсумковий доказ двох запусків](https://github.com/juv4uk/cml/actions/runs/38187859376/artifacts/11719663973). Їхній найраніший строк завершення — **2026-11-11 00:25:56 UTC**.

Новий runtime census у кожному запуску знайшов 562 успішно відкриті repository-path файли; обидва набори збіглися за SHA `53320597b6b55667498bbc8f7c2b0bee7a6ea05b723c9385e339f5cff8ec87ad`. З-поміж спостережених шляхів 444 vendor-файли мали 4,940,765 байтів за виміром на кінець trace: сім вибраних пакетів — 296 файлів / 4,419,723 tracked bytes; ще 148 файлів manifest/checksum metadata з інших 74 vendor roots — 521,042 bytes. Це динамічне спостереження, а не доказ мінімальної замикальної множини.

Відомий операційний підсумок нижньої межі — **36,033,737 байтів**: runner 34,623,904 + pinned SENS build-input subset 1,397,243 + CML runtime contract 1,129 + WSM nucleus source 11,461. Повний seed-total залишається **BLOCKED**: ще треба замкнути module/cfg та compile-time include граф, перевірити clean offline replay і зовнішній Cargo cache/toolchain/shared libraries, а також визначити мінімальні Git refs/objects. Поточний звіт і новий lineage JSON збережено в `main`: `evidence/nano-sens-seed-v0-2026-10-12.json` та `evidence/compiler-selfhost-lineage-2026-10-12-nano-sens.json`.


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

Віддалений CML workflow для свіжого lineage тепер підтверджено: [run 38187859376](https://github.com/juv4uk/cml/actions/runs/38187859376) успішно зберіг бінарні артефакти, size report, lineage report і runtime census для двох чистих запусків. Додатково новий звіт `evidence/compiler-selfhost-lineage-2026-10-12-nano-sens.json` зафіксовано у `main`, а `.github/workflows/compiler-selfhost-lineage-contract.yml` розширено, щоб перевіряти його через SENS-side validator і повторно звіряти SHA pinned source. Остаточний результат саме цього validator workflow має бути зелений на останньому commit перед позначенням gate завершеним.

Попереднє твердження, що вимірювання seed-компонента заблоковане відсутністю артефактів, **застаріло** й замінене свіжим виміром від 2026-10-12. Бінарний файл було справді отримано з workflow artifact, а не відновлено з JSON. Повна closure/minimality і далі **BLOCKED**: 34,623,904 байти — лише CML runner-компонент; 36,033,737 байтів — лише явно перелічений операційний підсумок нижньої межі.

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

Для цього шляху вже є **один канонічний генератор усіх трьох файлів** — `scripts/publish_verified_uk_triplets.py`. Він приймає лише явні шляхи до джерел з ратифікованої української підмножини, записує у зовнішнє дзеркало `.lisp`, фізичний `.sens` і файл без розширення та публікує SHA-звіт. Публікація транзакційна: колізія або помилка перевірки відкочує створені файли; вихідне джерело не переписується.

Приклад повного шляху від конвертера до SENS-компілятора:

```sh
python3 scripts/publish_verified_uk_triplets.py \
  --mirror /tmp/sens-triplet-mirror \
  --report /tmp/sens-triplet-report.json \
  --write examples/migrated/smoke-quote.lisp

cargo xtask compiler-compile \
  --triplet /tmp/sens-triplet-mirror/examples/migrated/smoke-quote.sens \
  --out /tmp/smoke-quote-compiler-artifact.bin
```

Генератор трійки залишається обмеженим конвертером проєкцій, **не semantic-oracle admission**: його звіт прямо залишає `original_executables_oracle_certified = 0`. `scripts/verify_uk_t5_triplet.py` доводить лише обмежений roundtrip українського джерела, типованих слів і T5/view у підтриманому D1/D2/D3/D4 корпусі. `scripts/stage-two-projections.py` — окремий двухфайловий етап; для нового повного потоку вище він не потрібен.

Новий явний вхід компілятора:

```sh
cargo xtask compiler-compile --triplet /path/to/program.sens --out /path/to/new-artifact.bin
```

Шлях `program.sens` має мати двох однойменних сусідів: `program.lisp` та файл без розширення `program`. Режим `--triplet` читає саме фізичний T5, отримує слова через чинний SENS-рідер, перевіряє байтову тотожність розгорнутого view з канонічними словами та одним кінцевим LF, а також повторного T5-кодування. Потім він незалежно парсить/опускає джерело та бітовий view і вимагає однакового exact-domain результату. Далі викликається той самий компіляторний корпус у `lib/compiler-nucleus.lisp`.

Артефакт зберігає SHA-256 канонічного SW1-кодування exact-domain програми, як вимагає поле `program_wire_sha256`; фізичний `.sens` має власну окрему байт-до-байта перевірку T5. Symlink/non-regular inputs і наявний output відхиляються. `--input` та `--triplet` взаємовиключні; формат не визначається автоматично за вмістом.

CI тепер має end-to-end інтеграційні тести, які запускають саме `publish_verified_uk_triplets.py`, а потім передають створену трійку через публічний `cargo xtask compiler-compile --triplet`. Вони перевіряють позитивний шлях, змінений view, відсутній LF, змінене джерело й неоднозначний вибір вхідного режиму. Ці тести додані, але їхній реальний Hosted CI результат треба підтвердити; локальний `cargo` у поточному середовищі відсутній.

Це executable front-end до наявного SENS-written компілятора, але ще не машинний backend і не повний C1 → C2 self-host proof.

## Acceptance gates

- [x] З чистого checkout і без читання заздалегідь зібраного C1/C2 повторно запустити чинний self-host lineage flow: обидва clean-run jobs та comparison пройшли в [run 38187859376](https://github.com/juv4uk/cml/actions/runs/38187859376).
- [x] Для виміряного компонента визначити точний seed-артефакт і межу фізичних байтів: `seed-v0-c0-runner.bin`, 34,623,904 байти. Це ще не повна closure.
- [x] Два незалежні clean runs мають однакові pinned-входи, byte-identical size report і однаковий 562-файловий observed path set; traces збережено з retention 30 днів.
- [ ] Дочекатися зеленого SENS-side validator workflow для свіжого збереженого lineage report і перевірки source digests; CML workflow вже зафіксував `byte-identical-artifact`, але це окремий gate.
- [ ] Замкнути повний source/build/runtime closure, включно з module/cfg, compile-time includes, offline replay і мінімальним Git/toolchain dependency boundary.
- [ ] Окремо звіряти спостережуваний результат і точні байти для тих випадків золотого GAS/NASM корпусу, де контракт вимагає byte identity.
- [ ] Кожне зменшення seed проходить той самий функціональний корпус, негативні fail-closed випадки та lineage перевірки.
- [ ] Публікувати мінімальний розмір тільки після доведеної повноти closure і вимірювання; не використовувати «десятки байтів» як незасвідчену ціль або заявлений результат.

## Семантичні межі

- Чинна влада — Contract 11.8 / owner-ratified D1–D9; D10 лишається research/unratified і не є залежністю Nano-SENS.
- Історичні Lisp-кандидати можуть бути донорськими тестами/джерелами, але не додають значень до ядра без окремого закону, позитивного свідка, falsifier та перевірки дублювання.
- Мова визначає значення; CML, компілятор bootstrap, linker, GAS/NASM і цільова машина забезпечують механізми та свідків, а не другу таблицю семантики.
- Невідомий домен, невідповідний provenance, unsupported lowering або нерівний observable мають залишатися категоризованими FAIL/BLOCKED, а не виправлятися fallback.

## Власник наступної дії

Продовжити в межах наявних #3835 / #3822 / #3760: спершу зробити seed-метрику відтворюваною, потім оптимізувати фізичний результат, зберігаючи чинний доказ C1/C2. Нову гілку й окремий домен для Nano-SENS не створювати.
