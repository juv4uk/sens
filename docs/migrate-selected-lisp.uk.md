# Пофайлова міграція наявного Lisp у двійкову SENS

Це обмежений сумісний T5-адаптер над канонічними `scripts/migrate-three-pass.py` і `scripts/sens_t5_t5m_codec.py`. Він працює з ОДНИМ раніше наявним файлом, не пише поверх джерела, не створює неіснуючих семантичних законів і не підміняє SENS-виконання Python-оракулом. Для чинного фізичного носія T5M використовується `scripts/migrate-one-to-sens.py` (і його Zig-підтвердження); наявність фізичного носія не є релізним admission.

## Команди

Спочатку зібрати реальний D2 reader:

    cargo build -p sens-cli --bin sens-trit
    git hash-object lib/ВАШ-ФАЙЛ.lisp

Потім — **тільки історичний dry-run, без фізичного запису**:

    python3 scripts/migrate-selected-lisp.py \
      --source lib/ВАШ-ФАЙЛ.lisp \
      --source-blob ВАШ_40_СИМВОЛЬНИЙ_GIT_SHA \
      --source-era auto \
      --out-root /tmp/sens-inspection \
      --reader target/debug/sens-trit \
      --oracle /absolute/path/to/independent-verifier \
      --dry-run \
      --report /tmp/sens-one-file.json

Це створює лише звіт `VERIFIED_DRY_RUN`, **не** `.sens`. Для чинного запису існує `scripts/migrate-one-to-sens.py`: він створює Zig/T5M `.sens` і однойменний двійковий перегляд після точнодоменного перетворення. Окремі SENS-свідки виконання та згода власника залишаються умовами релізу.

## Що гарантовано

- Вхідний Git blob SHA закріплений; один змінений байт — BLOCK.
- `--source-era auto` є єдиним допустимим режимом. Значення `legacy` і `current` залишено лише для явної діагностики помилкового старого виклику: обидва дають `BLOCKED / RETIRED_SOURCE_ERA`, без фізичних виходів. Невизначений W8/D8 завжди блокується; історична таблиця є provenance, а не виконавчим дозволом.
- Коди D1–D9 є 0/1 ідентичностями; D2 задає всю структуру. Трит 2 — фізичний розділювач між словами; п'ять тритів у байті, EOF за довжиною, жодного фальшивого 22-сентинела. Порожній список = D3:000.
- Невідомі текстові імена, змінні без доказу, host I/O, непройдені типи чисел і об'єкти, що не відповідають точній бітовій граматиці, блокуються.
- Python робить точний T5 roundtrip. Справжній Rust sens-trit відкриває фізичний файл і перевіряє D2-граматику. Це ще НЕ є перевіркою семантики.
- Для публікації потрібен окремий незалежний oracle executable: аргументи — шляхи до старого .lisp і тимчасового фізичного .sens. JSON stdout містить schema=sens-historical-current-oracle/v1, status=PASS, source_blob_sha, physical_sha256, typed_word_sha256, historical_observable, current_observable та evidence. Спостереження мають бути однакові.
- CLI звіряє SHA й порівняння оракулів, але не може довести, що сторонній verifier дійсно запустив старий рантайм. Reviewer мусить верифікувати його незалежність; тестовий oracle stub лише перевіряє протокол, не є семантичним доказом. Окремий Cargo-тест у workflow виконує справжній чинний D4-оракул.
- Вхідне `.lisp` не змінюється. Цей історичний адаптер **не має права створювати** `.sens`: доступні лише `--inspect` та `--dry-run`; звіт містить `BLOCKED`, `SYNTAX_ONLY_UNVERIFIED` або `VERIFIED_DRY_RUN`. Спроба старого запису дає `LEGACY_T5_PUBLICATION_DISABLED`. Жоден його PASS не є семантичним допуском.
- Архіви бенчмарків, схеми, ISA-каталоги й quoted/data witness не вважаються виконуваним оригінальним кодом. Новий канарковий приклад не скорочує число 491.


**Межа результату:** `SYNTAX_ONLY_UNVERIFIED` і навіть
`VERIFIED_DRY_RUN` сумісного T5-адаптера не засвідчують
пофайлову українську `.lisp ↔ .sens` тотожність для всього корпусу.
Зелений roundtrip потребує незалежного реального SENS-оракула,
відтворення вихідної проєкції та релізного леджера на одному SHA.

## Реальний прогрес

Файл можна рахувати за оригінальний перенесений лише після того, як існуючий до міграції executable .lisp із когорти 491 отримав same-stem фізичний .sens, незалежний історичний/current oracle пройшов, і PR злитий у main. Аудитуйте Git-дерево головної гілки, а не кількість dry-run кандидатів.

## Інспекція справжнього старого файла без семантичного оракула

Для діагностики старого Lisp можна запустити тільки перевірки фізичного T5 та D2:

    cargo build -p sens-cli --bin sens-trit
    python3 scripts/migrate-selected-lisp.py \
      --source benchmarks/closures.lisp \
      --source-blob HEAD --source-era auto \
      --inspect --out-root /tmp/sens-audit-no-write \
      --reader target/debug/sens-trit \
      --report /tmp/sens-audit.json

Параметр --source-blob HEAD прив'язує вхід до ТОЧНОГО Git blob перевіреного коміту; незакомічена зміна блокується. Також можна передати 40-символьний blob SHA явно. Інспекція повертає BLOCKED (код 2 і точна причина) або SYNTAX_ONLY_UNVERIFIED (код 0). ОБИДВА стани означають нуль нових .sens і не є доказом збереження семантики.

Режим `--inspect` взаємовиключний із `--dry-run`. Для чинної фізичної публікації потрібен окремий Zig/T5M-маршрут та незалежні докази SENS-виконання; старий адаптер не публікує файлів навіть із позитивним історичним оракулом. GitHub workflow інспектує три РЕАЛЬНІ вихідні файли benchmarks/closures.lisp, benchmarks/parser.lisp, lib/machine/block.lisp і публікує артефакт sens-original-lisp-triage, не створюючи фізичного файла. Це дослідження заблокованих джерел, а не успішна міграція.
