# Перехід фізичного транспорту SENS на Zig · 14.10.2026

## Актуалізація межі Rust T5 · 24.10.2026

Попередні абзаци про `--no-default-features` як робочий Rust physical backend
застаріли й не описують поточний CLI: команда без `zig-transport` відмовляє
фізичним командам (`RUST_ZIG_ONLY`), а `backend` повідомляє
`transport=unavailable`. Ознайомлюйся з кодом `sens-trit`, а не з історичним
прикладом нижче.

- `sens-cli` залежить від `sens` із `default-features = false`; те саме
  виставлено всім прямим production-залежностям SENS у workspace. Типова
  production-збірка не вмикає `sens/rust-t5-reference`.
- Фізичні Rust T5 API в `sens` тепер feature-gated. CLI не має runtime feature
  для ввімкнення Rust fallback; без `zig-transport` фізичні команди відмовляють.
  Dev-залежність підключає reference API тільки під час сумісних тестів.
- D7↔W7 українська проєкція SENS винесена в `d7_projection.rs`, отже
  семантичне зіставлення символу з точним доменним словом не залежить від
  Rust T5-пакувальника.
- `sens` зберігає `rust-t5-reference` у власних default features як перехідну
  сумісність для чинних інтеграційних тестів та споживачів. Тому наступний
  зріз ізоляції — перенести ці тести на Zig-свідків і лише тоді прибрати
  compatibility default ядра. Це свідомо не приховано як завершена міграція.

Перевірка цього зрізу: `cargo check --locked -p sens-cli --bin sens-trit`
успішний; граф звичайних залежностей не містить feature
`sens/rust-t5-reference`; D7/Zig boundary, bare-session CLI та reference T5
roundtrip integration tests також успішні.

## Нове рішення власника: Zig — єдиний турнікет, але НЕ реєстр кодів

> **«Zig — турнікет, не реєстр. Реєстр — контракт, ратифікований власником. SENS вирішує значення, Zig дає коди обом, Rust тримає байти. Той, хто дає, не вирішує; той, хто вирішує, — закон».**

Це **архітектурна ціль обов'язкового шляху виконання**, а не твердження, що нинішній `main` уже довів відсутність усіх обходів. Цей документ — технічний handoff; нормативну владу зберігають `CURRENT.md`, `language-contract.lisp`, `contracts/numeric-domains-ratification.lisp` та ратифіковані `lib/domains/dN.lisp`/knowledge-таблиці. **Генератор читає тільки ратифіковані джерела і породжує відповідні проєкції SENS/Zig/Rust** із exact domain, width, bits та SHA джерела; Zig не призначає жодної нової координати й не розв'язує конфліктів semantic registry.

```text
Нормативний контракт SENS + ратифіковані домени
             │ генерація/пін джерела, НЕ Zig-влада
             ▼
      проєкції для SENS / Zig / Rust

SENS: law + admitted words ──► Zig: exact width/physical encode ──► Rust: opaque bytes/storage
SENS: law + semantic verdict ◄── Zig: exact physical decode/validate ◄── Rust: opaque bytes/input
```

**Важлива межа:** у стрілках до/від Zig проходять *типізовані механічні слова або фізичні байти*, не Rust `ExprKind`/`Value`, host `bool` чи самопризначений opcode. На вході Zig перевіряє width/payload/buffer/profile/canonicality; SENS сам вирішує, чи це допустима функція, D2-структура, D1-істина, D7-текст, D24+-число або взагалі не виконуваний об'єкт. На виході Zig повертає механічний носій/помилку; Rust не може підмінити семантичне `D1:NO` host-статусом відмови транспорту. Будь-який `Rust-only` reference/backend — **лише явно обраний порівняльний режим**, не непомітний production fallback.

### Аудит реалізованого стану проти цілі, перевірка 14.10.2026

| Ділянка | Підтверджено в коді | Невиконаний перехід |
|---|---|---|
| `crates/sens-cli/Cargo.toml` + `build.rs` | `zig-transport` — default для CLI; пін Zig 0.16.0; відсутність компілятора не перемикає типову збірку мовчки на Rust | Це **не** автоматично Zig-default для всього `crates/sens`/WASM/FPGA |
| `research/zig-codecs/transport_abi.zig` | ABI **v2**, caller-owned `[width, MSB, LSB]` для `sens_zig_t5_encode_be3`, безалокаційний `sens_zig_t5_validate`, явні F3C pack/unpack | Поки **немає** відповідного `sens_zig_t5_decode_be3` для повернення exact-width слів Zig→SENS; no-bypass ingress усіх CLI не доведено |
| `crates/sens-cli/src/bin/sens-trit.rs` | Зовнішні `.sens` байти проходять Zig physical validate; encode BE3 доходить до Zig та порівнюється з поточним reference | CLI досі викликає `sens::decode_ternary_words`, `sens::decode_ternary_program`, `sens::open_ternary_program` після фізичного validation; ще не повне `Zig decode→canonical typed words→SENS reader` |
| `crates/sens-cli/src/main.rs`, `crates/sens/src/binary_execution.rs`, `crates/sens/src/ternary_transport.rs` | Існують прямі Rust decode/encode-функції T5 і внутрішній перехід до SENS reader | Прямі production ingress/egress маршрути потребують поступової інвентаризації/переведення, окремо від еталонних бенчмарків і тестових reference-path |

**Отже, сьогодні не заявляти:** `single-gateway-complete`, `Rust-bypass-eliminated`, `Zig-decoder-ABI-ready`, `native-semantic-PASS` або `all-targets-freestanding` без точного commit/run receipt. Сам факт default Zig CLI і успішний Zig↔Rust byte-parity не доводить повного турнікета.

### Порядок точкової реалізації без нового глобального блокера

1. **#5777 → #5779, M1 — симетричний декодер в Zig ABI.** Додати **окремо заявленим CLAIM** caller-owned Zig `T5 bytes→BE3 typed width/payload` із точними length/capacity/error, no host layout або Zig registry. Спочатку підтвердити canonical T5 механіку D1–D9; D10 лишається **окремим coordinate-only профілем**. Не міняти ABI-version без явної сумісності та доказу, не вписувати D11/D24+ у T5 автоматично.
2. **M2 — один CLI ingress/egress через турнікет.** Почати із `sens-trit`: Rust передає bytes у Zig, Zig повертає лише механічні слова, SENS-owned reader робить D2/semantic admission; у зворотному напрямі SENS exact-width → Zig BE3 encoder → Rust зберігає тільки байти. Залишити test-only reference як *явно* обрану незалежну перевірку. Будь-яка відмова Zig — fail-closed, не `try Rust`.
3. **M3 — інвентаризація інших entrypoints.** Окремими неперетинними CLAIM перевести `sens-cli/main.rs`, `sens/binary_execution.rs` і решту реальних runtime boundary calls; для Cargo package boundaries потрібна явна технічна схема без cyclic dependencies. `ternary_transport.rs` може лишитися порівняльним reference, але **не прихованим production bypass**. Не масово видаляти reference-код або робити компілятор Zig джерелом семантики.
4. **M4 — доменна генерація, окрема від gateway.** Контракт→машинні exact-bit проєкції із source SHA, контроль довжин і провідних нулів, без самостійного `Zig defines Dn`. D7 — одразу чинна keyboard v2 128/128 (історичний v1 **не має мігрованого корпусу**, не вводити conversion gate); D11 43/2048 — тестовий словник без callable; D24/D48/... — окремо ратифіковані числові домени, їхній майбутній фізичний конверт вимагає **окремого** явного закону.

### Доказ для кожної підланки

- **Позитив:** байт-у-байт Zig↔Rust *reference* roundtrip на **одному git-tracked SHA-корпусі**, збереження width і leading zeros (зокрема `D1:1` ≠ `D2:01`), і окремий позитивний нативний SENS self-verdict.
- **Негатив:** invalid length/byte/padding, недостатня місткість, перевищення профілю, переплутаний D8/D9 width, `D10` execution поза профілем, test-only D11 як callable, host `NO` замість Zig error або SENS `D1:NO`, спроба обійти Zig прямим Rust-decoder у *обраному production entrypoint*. Не додавати порівняння **історичний SID8→сучасний D8**.
- **Квитанція:** `test_id`, layer, exact file/commit/fixture SHA, expected/actual, перша відмінність, одна команда відтворення, actual central CI exact-SHA status; benchmark на однаковому корпусі та апаратурі. Жодного нового авто-workflow: чинний `.github/workflows/ci.yml` лишається єдиним; семантичний PASS виключно SENS.

**Координація:** [#5029](https://github.com/juv4uk/sens/issues/5029) для неперетинного CLAIM, [#5779](https://github.com/juv4uk/sens/issues/5779) для firewall, [#5777](https://github.com/juv4uk/sens/issues/5777) для ABI, [#5767](https://github.com/juv4uk/sens/issues/5767) для T5, [#5770](https://github.com/juv4uk/sens/issues/5770) для parity. Цей handoff **не** призначає Zig кодів, не запускає CI, не створює нової ратифікації і не уповноважує самовільне злиття.

## Явне рішення власника: «переходим на зіг» → «зроби дефолтним кодеком»

**Переходимо на Zig для фізичних кодеків та транспорту.** Мова SENS, її ратифіковані двійкові слова й D2/D3 закони, SENS evaluator, невідворотні нормативні рішення і 2046 координат **не перетворюються на Zig-семантику**. Zig володіє лише зовнішніми байтами, пакуванням, конвертом; зміна ідентичності через десятковий SID8/W8/Sens8 неприпустима.

### Вже реалізовані механізми (Zig за замовчуванням у sens-cli)

- `research/zig-codecs/t5/t5.zig` — незалежний exact-width T5; D1–D9, padding/width/canonicality.
- `research/zig-codecs/f3c/f3c.zig` — обмежений F3C, явний `.senc` з `0xf3`, без sniffing/fallback, тільки якщо весь файл коротший.
- `research/zig-codecs/transport.zig` — Zig фізичний файловий інструмент; `t5-check`, `t5-roundtrip`, `f3c-pack`, `f3c-check`, `f3c-unpack`; create-exclusive, вихідні дані зберігаються.
- `research/zig-codecs/transport_abi.zig` — Zig-owned синхронний C ABI v2: T5 validate/encode і F3C pack/unpack; **виклик не передає власності пам’яті через FFI**.
- `crates/sens-cli/build.rs` і `crates/sens-cli/src/bin/sens-trit.rs` — звичайна Cargo-збірка `sens-cli` компілює фізичний Zig ABI за замовчуванням, `sens-trit encode`, `encode-f3`/F3C decode й фізична `.sens` перевірка користуються Zig, а Rust reader перевіряє канонічну граматику і виконує програму. Rust reference залишається як **незалежний контроль**, а збірка Rust-only вмикається тільки явно через `--no-default-features` (не прихований fallback).

## Пін компілятора й інтеграція в міграцію

- Канонічний пін інструмента: `.zig-version` = `0.16.0`.
- `crates/sens-cli/build.rs` перевіряє точний `zig version` перед збіркою фізичного ABI; `ZIG=/path/to/zig` підтримується.
- `scripts/migrate.py preview --zig-codec` і `scripts/migrate-t5m-batch.py --zig-codec` додають незалежний Zig `t5-check` / `t5-roundtrip` та byte-exact SHA-свідок до кожного згенерованого T5 файлу. `scripts/migrate-one-to-sens.py --zig-codec` робить те саме до запису.
- Це **явне включення** перевірки, не прихований автоматичний fallback. Відсутність потрібного Zig або розбіжність байтів зупиняє відповідну Zig-перевірку, але не змінює SENS-законів. Наявні маршрути міграції зберігають попередню поведінку без цього прапорця.
- Парні T5/F3C benchmark scripts приймають тільки `0.16.0` і перевіряють `.zig-version`. Старі історичні бенчмарки з `0.17.0` не підміняють нові результати.

```sh
python3 scripts/migrate.py preview tests/fixtures/migration-d1-cond-cohort \
  --source-era current --mirror /tmp/sens-preview --report /tmp/sens-preview.json --zig-codec
python3 research/zig-codecs/t5/run_paired_bench.py --zig-pin 0.16.0 --pairs 3 --out-dir /tmp/sens-t5-paired
python3 research/zig-codecs/f3c/run_paired_bench.py --zig-pin 0.16.0 --pairs 3 --out-dir /tmp/sens-f3c-paired
```

## Відтворення на Linux з чинним піном Zig 0.16.0

```sh
zig version
zig test research/zig-codecs/tests.zig -lc
zig build-exe research/zig-codecs/transport.zig -O ReleaseFast -lc -femit-bin=target/sens-zig-transport
target/sens-zig-transport t5-check input.sens
target/sens-zig-transport f3c-pack input.sens output.senc
target/sens-zig-transport f3c-unpack output.senc restored.sens
cmp input.sens restored.sens
cargo build --locked -p sens-cli --bin sens-trit
target/debug/sens-trit backend  # transport=zig abi=2 semantic_authority=SENS
target/debug/sens-trit eval input.sens
target/debug/sens-trit eval-f3 output.senc
```

**Типова збірка `sens-cli` тепер потребує Zig в PATH або `ZIG=/шлях/до/zig`.** Показати режим без Zig (лише явна сумісність): `cargo build --locked -p sens-cli --bin sens-trit --no-default-features` і `target/debug/sens-trit backend` → `transport=rust-reference semantic_authority=SENS`. Ця опція НЕ змінює формат T5/F3C і не є автоматичним fallback.

**Версія Zig впливає на відтворення збірки, не на wire.** Сьогодні центральний `.github/workflows/ci.yml` пінує Zig 0.16.0; ранні бенчмарки GitHub проводилися на 0.17.0. Висновки зі швидкості мають фіксувати точні версії, прапори й сирі SHA бінарників; швидкість `zig-transport` через Rust FFI сама собою не дорівнює microbenchmark цифрам Zig.

## Контракти безпеки

1. `t5-check` гарантує **лише транспорт**, не граматику і не право виконувати програму. Нативний SENS canonical D2+evaluator зберігає останнє слово.
2. F3C `.senc` декодується **тільки явно**; невірний маркер, байти чи недоведена форма — відмова. Немає автоматичного fallback на T5.
3. Відсутність економії означає використання T5, а не помилку вже канонічної програми.
4. Перед виконанням недовіреного `.senc` потрібен довірений **SHA-256 фізичного носія**, як у чинному `verify-f3-sha256`/`eval-f3-sha256`; проста внутрішня F3C мітка не забезпечує захист від підміни.
5. Діагностика кожного red має бути інформативною; semantic PASS вимагає реального нативного SENS виконання, не Rust/Zig самооцінки.

## Статус релізу

**Zig T5/F3C злитий у `main` через PR #5780; за новим прямим рішенням власника `zig-transport` — DEFAULT FEATURE лише пакета `sens-cli`.** У звичайній збірці `sens-trit` Zig створює фізичні байти, Rust/SENS core здійснює допуск і виконання. Для незалежного reference-run без Zig треба *явно* задати `--no-default-features`; якщо Zig відсутній у типовій збірці, збірка падає, а не відступає мовчки на Rust.

**Межа:** це НЕ зміна типової фізичної структури (`.sens` T5 і `.senc` F3C залишаються як були), не ввімкнення Zig у `sens` core/WASM/freestanding/FPGA, не завершення E1/E2/E3 і не оголошення зеленого релізу. Rust reference збережено до повного corpus-паритету. Загальний CI має відомий окремий RED SID8/D8 (#5778) — не маскувати. F3M лишається дослідним профілем. Конверт Zig не може змінювати SENS-семантику.

Докази: [T5/F3C real paired benchmarks](../research/zig-codecs/RESULTS-2026-10-14.uk.md), [#5766](https://github.com/juv4uk/sens/issues/5766), [#5767](https://github.com/juv4uk/sens/issues/5767), [#5768](https://github.com/juv4uk/sens/issues/5768), [#5770](https://github.com/juv4uk/sens/issues/5770), [#5771](https://github.com/juv4uk/sens/issues/5771).

## ABI v2, без Rust layout → SENS (14.10.2026)
- Основний `sens-trit` передає механічні слова Zig як caller-owned послідовність трійок байтів `[exact_width_u8, payload_MSB_u8, payload_LSB_u8]`. Це **тільки внутрішній ABI шлюзу**, не новий wire-format і не мовне значення SENS.
- Фізичні T5 байти виробляє тільки Zig; Rust передає ширину й біти як opaque payload, без доменних номерів, host-enum, `repr(C)` або native endian.
- `sens_zig_t5_encode_be3` відхиляє нецілі трійки, нульову/непідтримувану ширину, надлишковий payload і недостатню місткість буфера.
- `sens_zig_codec_abi_version() == 2`; попередній експорт `sens_zig_t5_encode` збережений для старого ABI-клієнта, але **за замовчуванням не викликається** із `sens-trit`. Поза межами host не переносити `usize/isize` у фізичний конверт.
- Доказ в `research/zig-codecs/transport_abi.zig`: різні фізичні T5 для D1:1 та D2:01, позитивний golden і негативні перекручені triplets. Це mechanical gate; семантичне рішення належить SENS.

## Обов'язкові парні бенчмарки кожного коміту · рішення власника 14.10.2026

**За прямим рішенням власника T5 та F3C benchmarks є обов'язковими для кожного GitHub push / PR**, незалежно від назви гілки або changed paths. Виконуються **тільки** в чинному автоматичному `.github/workflows/ci.yml`: Zig 0.16.0 (перевірений pinned download) ↔ Rust `--locked --release`, по **3 зовнішні парні серії** для кожного кодека на одному runner з перемішаним порядком запуску.

- До кожного timing підтвердити **побайтову ідентичність** Zig↔Rust (фізичний T5/F3C, не SENS-семантику). Parity mismatch, missing sample, невірний SHA / pin / invalid elapsed / відсутній артефакт **блокують CI**. Жодного мовчазного skip.
- Повинні існувати `STATUS`, `environment.json` із Git SHA, compiler version та SHA бінарників, `samples.jsonl`, `summary.md`. Обов'язковий evidence-gate звіряє **240 T5** та **120 F3C** рядків, обидва backend, рівно 3 пари. Окремий `upload-artifact` виконується навіть після помилки; відсутність артефакту — помилка.
- **Швидкість не є семантичною істиною**, і самі плинні таймінги GitHub-hosted runner не мають hardcoded fail-порогу. CI блокує непідтверджені/неповні виміри, а не повільніший Zig або Rust. Немає неправдивих заяв про 95% K–J interval чи продуктивність усього SENS.
- Це **обов'язковий фокусний mechanical benchmark**, а не автоматичне покриття всіх профілів, великий corpus, cross-target ESP32 або freestanding proof. Для цих задач вимоги #5770/#5771/#5772–#5775 залишаються відкритими.

Локальне відтворення (Zig 0.16.0 і Rust/Cargo доступні в PATH):
```sh
python3 research/zig-codecs/t5/run_paired_bench.py --zig-pin 0.16.0 --pairs 3 --out-dir /tmp/sens-t5-paired
python3 research/zig-codecs/f3c/run_paired_bench.py --zig-pin 0.16.0 --pairs 3 --out-dir /tmp/sens-f3c-paired
```


## Очищення транспортного ABI · 14.10.2026

У `research/zig-codecs/transport_abi.zig` прибрано неактивний
`sens_zig_t5_encode` на padded `extern struct` і `c_allocator`.
Єдиним підтримуваним входом кодування T5 через межу Zig↔Rust є
`sens_zig_t5_encode_be3` (ABI v2: `[width, MSB, LSB]`, буфер
надає викликач). Код Rust `sens-trit` використовує саме цей символ;
зовнішнім користувачам колишнього структурного символу потрібна
міграція на v2. Ані `.sens` wire, ані семантика SENS не змінені.

Наявний пакет `research/zig-codecs/tests.zig` містить точковий
`typed ladder via public Zig ABI v2, D10 fail closed`:
D8/D9 — точний двобайтовий T5 і зворотна типізація, D10 — відмова
виконуваного T5 ABI, недостатня місткість — відмова без запису.
Це **механічні тести**; статус PASS можна заявляти тільки після
справжнього запуску компілятора, не за фактом GitHub-коміту.

```sh
zig version
zig test research/zig-codecs/tests.zig --test-filter "typed ladder via public Zig ABI v2"
zig test research/zig-codecs/tests.zig
```

Стан на момент зміни: вихідні файли і зміни в `main` перевірено
через GitHub, але Zig compiler run і device/cross-target proof
ще не підтверджені. Нових CI workflow для цього не потрібно.

## Перевірений стан коридору · 24.10.2026 · `b72a5b4d5d74e90d20edde5113e22b39b8659235`

Це доповнення фіксує стан поточного `main`; історичні записи вище з датою
14.10.2026 не переписуються.

- `sens-trit` має production-шлях T5M через Zig ABI: Rust передає фізичні
  байти Zig, отримує точні width/bits, а SENS reader окремо вирішує, чи є
  відповідна ідентичність у чинній драбині та чи допускається програма до
  виконання. Фізична ширина сама по собі не надає викличності.
- REPL завантажує T5M bootstrap-слова через Zig і виконує їх у SENS. Rust
  лишається інтерактивною оболонкою та обробником людського вводу; це не
  переносить семантичну authority з SENS до Rust.
- D4 `DEFINE` — оператор D4. Точний домен цільового резидента, наприклад
  D9 або D10, є окремою identity слота; механізм D4 може встановити туди
  визначення лише за правилами SENS. Не називати сам `DEFINE` оператором D10.
- На цьому SHA успішно завершились `scripts/check_sterile_zig_corridor.py`,
  `scripts/rust_lisp_sens_edges.py --by-rust`,
  `scripts/check_rust_lisp_sens_io.py` та
  `scripts/check_rust_sens_zig_corridor.py`. Результат першого:
  `STERILE_ZIG_CORRIDOR_PASS`; production Rust source-embed edges — `0`;
  обидва наступні guards повернули `*_OK` / `CORRIDOR_OK`.

Цей доказ покриває перевірені production-маршрути CLI та REPL. Він **не**
стверджує, що незалежний Rust T5 reference-кодек видалено з бібліотеки:
`ternary_transport` і його публічні compatibility-функції ще є, зокрема для
тестових фікстур та явних порівнянь. Наступний кодовий зріз ізоляції має
спершу перевести ці споживачі на Zig або чітко винести reference-профіль,
а тоді прибирати його з типової production-поверхні; неперевірене масове
видалення цих API зламає наявні Rust-перевірки.
