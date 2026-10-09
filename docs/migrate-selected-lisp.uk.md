# Пофайлова міграція наявного Lisp у двійкову SENS

Це окремий адаптер над канонічними scripts/migrate-three-pass.py і scripts/sens_t5_codec.py. Він працює з ОДНИМ раніше наявним файлом, не пише поверх джерела, не створює неіснуючих семантичних законів і не підміняє Rust-оракул.

## Команди

Спочатку зібрати реальний D2 reader:

    cargo build -p sens-cli --bin sens-trit
    git hash-object lib/ВАШ-ФАЙЛ.lisp

Потім:

    python3 scripts/migrate-selected-lisp.py \
      --source lib/ВАШ-ФАЙЛ.lisp \
      --source-blob ВАШ_40_СИМВОЛЬНИЙ_GIT_SHA \
      --source-era legacy \
      --out-root /tmp/sens-admitted \
      --reader target/debug/sens-trit \
      --oracle /absolute/path/to/independent-verifier \
      --report /tmp/sens-one-file.json

Вихід: /tmp/sens-admitted/lib/ВАШ-ФАЙЛ.sens. Далі його слід додати у PR із доказами й CI; CLI не мерджить автоматично.

## Що гарантовано

- Вхідний Git blob SHA закріплений; один змінений байт — BLOCK.
- source-era=auto блокує неоднозначні W8/D8; legacy дозволяє міграцію тільки через історичну доказову таблицю та оракул; current з W8 блокується, поки API #4517 не інтегровано.
- Коди D1–D9 є 0/1 ідентичностями; D2 задає всю структуру. Трит 2 — фізичний розділювач між словами; п'ять тритів у байті, EOF за довжиною, жодного фальшивого 22-сентинела. Порожній список = D3:000.
- Невідомі текстові імена, змінні без доказу, host I/O, непройдені типи чисел і об'єкти, що не відповідають точній бітовій граматиці, блокуються.
- Python робить точний T5 roundtrip. Справжній Rust sens-trit відкриває фізичний файл і перевіряє D2-граматику. Це ще НЕ є перевіркою семантики.
- Для публікації потрібен окремий незалежний oracle executable: аргументи — шляхи до старого .lisp і тимчасового фізичного .sens. JSON stdout містить schema=sens-historical-current-oracle/v1, status=PASS, source_blob_sha, physical_sha256, typed_word_sha256, historical_observable, current_observable та evidence. Спостереження мають бути однакові.
- CLI звіряє SHA й порівняння оракулів, але не може довести, що сторонній verifier дійсно запустив старий рантайм. Reviewer мусить верифікувати його незалежність; тестовий oracle stub лише перевіряє протокол, не є семантичним доказом. Окремий Cargo-тест у workflow виконує справжній чинний D4-оракул.
- Вхідне .lisp не змінюється. Існуючий .sens ніколи не перезаписується. Атомарне створення з no-clobber, --dry-run лише валідує. JSON-звіт містить BLOCKED, VERIFIED_DRY_RUN або WRITTEN.
- Архіви бенчмарків, схеми, ISA-каталоги й quoted/data witness не вважаються виконуваним оригінальним кодом. Новий канарковий приклад не скорочує число 491.

## Реальний прогрес

Файл можна рахувати за оригінальний перенесений лише після того, як існуючий до міграції executable .lisp із когорти 491 отримав same-stem фізичний .sens, незалежний історичний/current oracle пройшов, і PR злитий у main. Аудитуйте Git-дерево головної гілки, а не кількість dry-run кандидатів.

## Інспекція справжнього старого файла без семантичного оракула

Для діагностики старого Lisp можна запустити тільки перевірки фізичного T5 та D2:

    cargo build -p sens-cli --bin sens-trit
    python3 scripts/migrate-selected-lisp.py \
      --source benchmarks/closures.lisp \
      --source-blob HEAD --source-era legacy \
      --inspect --out-root /tmp/sens-audit-no-write \
      --reader target/debug/sens-trit \
      --report /tmp/sens-audit.json

Параметр --source-blob HEAD прив'язує вхід до ТОЧНОГО Git blob перевіреного коміту; незакомічена зміна блокується. Також можна передати 40-символьний blob SHA явно. Інспекція повертає BLOCKED (код 2 і точна причина) або SYNTAX_ONLY_UNVERIFIED (код 0). ОБИДВА стани означають нуль нових .sens і не є доказом збереження семантики.

Режим --inspect взаємовиключний із --dry-run. Для фактичного запису обов'язковий незалежний історичний/current verifier. GitHub workflow інспектує три РЕАЛЬНІ вихідні файли benchmarks/closures.lisp, benchmarks/parser.lisp, lib/machine/block.lisp і публікує артефакт sens-original-lisp-triage, не створюючи фізичного файла. Це дослідження заблокованих джерел, а не успішна міграція.
