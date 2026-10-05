# Core bootstrap split (#3629)

Цей benchmark відповідає на одну вузьку проблему: старий startup_bench починав
кожен mode з Session::default(), а Session::default() вже завантажує macro
library. Через це назви macro/core не дозволяли відрізнити перший macro
bootstrap від повторного.

## Modes

Старі provenance-compatible modes не перейменовуються:

- session — Session::default();
- bytes — default Session + прочитати Core FASL bytes;
- decode — default Session + FASL decode;
- parse — default Session + textual Core parse;
- macro — default Session + ще один load_macro_library;
- core — default Session + load_core_library.

Нові diagnostic controls:

- root — чистий Environment::root();
- root-macro — root + перший load_macro_library;
- root-core — root + повний load_core_library.

## Rule

Це незалежні process modes. Їхні різниці є діагностичними порівняннями, а не
математично точним nested phase subtraction.

Primary metric — Cachegrind I refs. Wall time допоміжний. Decision rows мають
щонайменше 3 повтори.

Цей slice не відкриває crate-private profile selection або stable-peer binding
у public API. Якщо наступна фаза потребує такої межі, спочатку треба знайти
механічний measurement design, а не розширювати semantic API заради benchmark.
