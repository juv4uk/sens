# SENS: підготовка міграції — T5 для звичайних програм, F3 тільки для дуже малих

**Рішення власника 11.10.2026 новіше за попереднє правило про один універсальний кодек.**
Утримуємо два фізичні кодеки: чинний T5 з явним розширенням .sens і
авторську Рамку-3 (F3) з явним розширенням .senc та міткою 0xF3.
**Введення .senc у production loader НЕ відбулося**; чинні .sens
не переписувати, не перейменовувати та не декодувати за схожістю.
Дослідний профіль .f3m — не третій виробничий кодек.

## Етапи

1. **M0 — інвентаризація:** Git HEAD, усі tracked .sens,
   фізичні розміри й SHA-256, вибір кодека. Нічого не переписувати.
2. **M1 — offline rehearsal:** у **новому каталозі поза checkout**
   готувати .sens або .senc за доказаним вибором, зберігаючи шляхи.
   Без in-place rename, git add та виконання мігрованого файла у CLI.
3. **M2 — byte-exact аудит:** через *явне розширення* декодувати
   кожен staged файл назад у канонічний T5 та порівняти ПОБАЙТОВО
   з оригіналом. Перевірити source SHA, staged SHA, source HEAD,
   кількість файлів, відсутність зайвих payload, заборону symlink.
   Пошкодження, невідомий профіль або обрив → FAIL.
4. **M3 — explicit production codec API (BLOCKED):**
   [#5439](https://github.com/juv4uk/sens/issues/5439) має
   виправити Rust↔Python F3 parity, надати окремий явний decoder.
   [#5445](https://github.com/juv4uk/sens/issues/5445) інтегрує
   тільки opt-in F3 CLI маршрут з fail-closed guards.
   [#5442](https://github.com/juv4uk/sens/issues/5442) підтвердить
   production gate на точному HEAD.
5. **M4 — вибіркове розгортання (НЕ РОЗПОЧАТО):**
   тільки після M3 переводити короткі програми в .senc;
   T5 лишається загальним форматом, вихідні .sens зберігаємо
   для rollback і відтворення. CML/GPU/FPGA/GraalVM — окрема
   перевірка, не автоматичне припущення.

## Правило вибору

Джерело: [Rust proof](../crates/sens/examples/two_codec_small_programs.rs)
та [контракт](codec-two-routes-t5-f3-2026-10-11.uk.md).

- T5 завжди припустимий для поточної канонічної фізичної програми.
- F3 лише якщо вхідний T5 займає **до 16 повних байтів**,
  оригінальний F3 frame_encode допускає структуру,
  строгий decode_senc відновлює всі точні слова
  і повний 0xf3+body **менший** за T5.
- У випадку неуспішного **encode selection** лишаємо T5.
  **Під час decode .senc** помилка зупиняє операцію:
  жодного вгадування кодека і жодного автоматичного fallback.
- Зберігати точні D1–D9 widths та leading zeros, D2 00/01/10/11,
  цитовані дані QUOTE. Збалансований D2 не автоматично означає
  виконувану програму.

## Реальний інструмент підготовки в main

Запуск із кореня репозиторію:

~~~sh
cargo build --locked --release -p sens --example two_codec_small_programs

# Без змін tracked файлів:
python3 scripts/prepare-two-codec-migration.py > /tmp/two-codec-plan.json

# Явний окремий каталог, якого ЩЕ НЕ ІСНУЄ:
python3 scripts/prepare-two-codec-migration.py \
  --stage /tmp/sens-two-codec-rehearsal \
  > /tmp/two-codec-staged-report.json

# Повторна незалежна перевірка всіх двох форматів:
python3 scripts/prepare-two-codec-migration.py \
  --verify-stage /tmp/sens-two-codec-rehearsal \
  > /tmp/two-codec-verified-report.json
~~~

**Сценарій не робить cutover.** Stage має лежати за межами Git checkout
і створюється лише з режимом create-new. При повторному запуску
на тому самому шляху stage відхиляється (ніякого overwrite).
Саме окремий Rust example через --convert і --restore виконує
фізичний алгоритм; Python не дублює семантику чи кодування F3.

Manifest v1 зберігає source_git_sha, source_sha256, source_bytes,
codec, selected_bytes, staged_file, staged_sha256.
--verify-stage знову отримує вибір із Rust на актуальному HEAD,
звіряє вихідні hashes і всі фізичні файли, потім декодує
кожен staged файл назад до T5 у тимчасовому каталозі.
Кожен байт порівнюється з незміненим джерелом.

[CI workflow](../.github/workflows/two-codec-migration-rehearsal.yml)
додатково псує перший байт справжнього F3 файла, вимагає
НЕнульовий status і після відновлення повторює весь аудит.
Статус CI слід перевіряти для актуального SHA, не вгадувати.

## Попередній доказ і незняті блокери

[Верифікований proof #38168014737](https://github.com/juv4uk/sens/actions/runs/38168014737):
**23/23** фізичних файлів побайтово відновлені, 9 F3,
14 T5, **443 → 434 байти**. Це 2,03% лише на малому корпусі
з повторюваними fixtures.

Перед міграцією production:
- 1062/1703 старих Rust↔Python F3 parity-розбіжностей;
- немає explicit production F3 reader у sens-trit;
- необхідні всі required CI на одному актуальному SHA;
- зовнішні CPU/GPU/FPGA/GraalVM споживачі не перевірені;
- історичні red #5406/#5408 не маскувати або вимикати.

Координація: Rust #5439, міграція #5440, CLI #5445,
CI #5442, один merge-writer #5041. **Нові гілки заборонені.**
