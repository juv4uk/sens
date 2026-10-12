# SENS: підготовка міграції — T5 для звичайних програм, Frame3 Carrier (F3C) для дуже малих

**Рішення власника 11.10.2026 новіше за попереднє правило про один універсальний кодек.**
Утримуємо два фізичні кодеки: чинний T5 з явним розширенням .sens і
авторський **Frame3 Carrier (F3C)** з явним розширенням .senc та міткою 0xF3.
Історичні CLI-команди лишають назву `f3`, тому **encode-f3/open-f3/decode-f3/eval-f3 означають F3C**, а не Envelope E1/E2/E3.
Чинні .sens не переписувати і не перейменовувати; звичайні команди залишилися на T5.

Нормативна матриця режимів: [режими проєкту](project-modes-2026-10-12.uk.md).

**Frame3-Micro (F3M, .f3m)** — не третій default production-кодек, але це
справжнє фізичне кодування SENS для dense bounded rank-space. Сімейство
вибирається явно як F3M, а конкретний профіль визначає **точна довжина**:
1 байт = F3M-1, 2 = F3M-2, 3 = F3M-3, 4 = F3M-4. Один committed байт `0x3E`
відновлює `CAR(CONS(1,NIL))` і проходить той самий SENS evaluator з
паритетом до T5. Внутрішнього selector/version/integrity metadata немає.
Назви E1/E2/E3 зарезервовано за колишніми S3/v1-v3 Envelope.
Див. [номенклатуру](codec-naming-2026-10-12.uk.md).

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
4. **M3 — ЯВНИЙ TINY F3 CORE/CLI: GREEN на перевіреному SHA.**
   Незалежний [Rust↔Python parity #38169848649](https://github.com/juv4uk/sens/actions/runs/38169848649)
   розділяє фізичний transport і D3 code admission, 0 failures.
   [Реальний CLI #38170264184](https://github.com/juv4uk/sens/actions/runs/38170264184)
   виконує open/decode/eval parity для всіх 9 допустимих F3,
   не змінюючи T5 default. Міжрепозиторна апаратна parity — окремо.
5. **M4 — вибіркове розгортання (НЕ РОЗПОЧАТО):**
   тільки після M3 переводити короткі програми в .senc;
   T5 лишається загальним форматом, вихідні .sens зберігаємо
   для rollback і відтворення. CML/GPU/FPGA/GraalVM — окрема
   перевірка, не автоматичне припущення.

## Правило вибору

Джерело: [Rust proof](../crates/sens/examples/two_codec_small_programs.rs)
та [контракт](codec-two-routes-t5-f3-2026-10-11.uk.md).

Це правило нижче стосується **production-вибору T5/F3C**. F3M є окремим
explicit bounded proof/research route: F3M-1 має 256/256 unique ranks,
F3M-2 — 65 536/65 536 exhaustive roundtrip, F3M-3 — 16 777 216 rank slots,
real-evaluator witnesses, DP-minimum `16 3C 63` для першого 6/6-capability
коду та exhaustive final-64K winner `FF FB 37`; F3M-4 — наступні
4 294 967 296 rank slots з algebraic capacity proof, 65 536 stratified
roundtrip samples і executable `DE AD BE EF`. Воно не змінює default:
`.sens` → T5, `.senc` → F3C, `.f3m` → F3M family + length profile.

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

## Як користуватися готовим явним F3-маршрутом

~~~sh
cargo build --locked --release -p sens-cli --bin sens-trit
target/release/sens-trit encode-f3 /tmp/short.sens  # create-new short.senc
target/release/sens-trit open-f3 /tmp/short.senc
target/release/sens-trit decode-f3 /tmp/short.senc
target/release/sens-trit eval-f3 /tmp/short.senc

# Шлях стандартного .sens не змінювався
target/release/sens-trit open tests/fixtures/migration-quote-cohort-main/quote-legacy.sens
~~~

Це працює тільки для файлів, створених за перевіреним правилом tiny F3:
фізичний F3 коротший, T5-основа не більше 16 байтів, D3 code admission і
одна канонічна форма. Не вмикати жодного autodetect за байтами.
[Повний інструмент випробування 9 файлів](../.github/workflows/two-codec-explicit-cli.yml).

**SENS CLI encoder+decoder завершено:** [CI #38170817413](https://github.com/juv4uk/sens/actions/runs/38170817413), SHA 2ac5cbe001dcc949561aeb6bca231e52befd75a7, SUCCESS. Мала QUOTE-програма 4B T5 → 3B F3, оригінал побайтово не змінено, повторний запис і перевищення межі відхилено, дев’ять вибраних F3 дали exact open/decode/eval parity. [Raw artifact](https://github.com/juv4uk/sens/actions/runs/38170817413/artifacts/11714003230).

## M3: цілісність перенесених F3 і фактичний CML blocker

Оригінальна tiny F3 має щільний фізичний rank, але **не містить CRC/MAC**.
Для файла з неперевіреного носія декодування й виконання дозволяти тільки
після порівняння із **довіреним** SHA-256 конкретних фізичних байтів.
Нові явні команди (не впливають на звичайний .sens/T5):

~~~sh
target/release/sens-trit verify-f3-sha256 /tmp/short.senc EXPECTED_TRUSTED_64_LOWERCASE_HEX
target/release/sens-trit eval-f3-sha256 /tmp/short.senc EXPECTED_TRUSTED_64_LOWERCASE_HEX
~~~

EXPECTED_TRUSTED_64_LOWERCASE_HEX потрібно брати з перевіреного manifest
або підписаного джерела. Хеш від недовіреного сусіднього файла не є доказом
автентичності. CLI читає фізичний файл один раз, звіряє хеш **до** декодера
F3 і до SENS evaluator, на невідповідність відмовляє без fallback.

[SHA і transport CI #38172737465](https://github.com/juv4uk/sens/actions/runs/38172737465)
на кодовому SHA db3c4ed9e57eb1ab80fc285533ae93b1c6d068cc — **SUCCESS**:
усі 9 малих F3 кандидатів із 23 фізичних джерел пройшли порівняння
зі звичайними T5 після перевірки staged SHA-256; negative на модифікований
F3 і помилковий SHA спрацювали. [Raw artifacts](https://github.com/juv4uk/sens/actions/runs/38172737465/artifacts/11714671813).

**CML зараз BLOCKED, а не мігрований:**
- [Candidate export failure](https://github.com/juv4uk/cml/actions/runs/38172268895):
  SENS xtask compiler-export відмовляє на nucleus-d3-001, q2:1/1 not callable;
- [Candidate CML compilation](https://github.com/juv4uk/cml/actions/runs/38172451274):
  142 compile errors на старі sens::sid/Sid8 після прив'язки нового SENS;
- [Дослідний інтеграційний тест](https://github.com/juv4uk/cml/blob/master/tests/tiny_f3_to_cml_lowering_test.rs)
  вже існує в поточній default-гілці CML master, але **IR parity поки не доведено**.

Поки CML не пройде compiler-export і заміну історичних кодових залежностей
на SENS-верифіковані DomainCall, production external/sens gitlink лишається
незмінним. У жодному разі не повертати старі SID8 як владу мови для
тимчасового обходу компіляції.

## Власники й статуси суміжних компонентів

[Машиночитаний інвентар споживачів](migration-two-codec-consumers-2026-10-11.tsv)
фіксує сім компонентів: Rust, CLI, триаду, CML, GraalVM, CUDA/Futhark
і FPGA. Для інших репозиторіїв шлях читача наразі TO_INVENTORY,
статус BLOCKED_UPSTREAM_CODEC_API; **це не виконана міграція**.

## Попередній доказ і незняті блокери

[Верифікований proof #38168014737](https://github.com/juv4uk/sens/actions/runs/38168014737):
**23/23** фізичних файлів побайтово відновлені, 9 F3,
14 T5, **443 → 434 байти**. Це 2,03% лише на малому корпусі
з повторюваними fixtures.

**Оновлення:** колишні 1062/1703 розбіжностей були наслідком змішування
структурного фізичного transport-паритету та виконавчого D3 допуску;
ці рівні тепер перевіряються окремо, без відключення негативних тестів.
Явний production CLI tiny F3 реалізовано, 9/9 порівнянь open/decode/eval GREEN.

**Що лишається поза цією завершеною SENS CLI ланкою:**
- Підтвердити глобальні required checks і всі незалежні зміни на актуальному final SHA;
- Перевірити CML, GPU/Futhark, FPGA та GraalVM на їхньому обладнанні;
- На F3 немає CRC/MAC; для публікації потрібні довірені hashes/підписи
  маніфесту, бо зміна на інший допустимий короткий F3 може лишитися непоміченою;
- Історичні red #5406/#5408 не маскувати або вимикати.

Координація: Rust #5439, міграція #5440, CLI #5445,
CI #5442, один merge-writer #5041. **Нові гілки заборонені.**
