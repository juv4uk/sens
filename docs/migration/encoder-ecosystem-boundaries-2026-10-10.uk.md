# М3: незалежний аудит фізичних меж екосистеми SENS

Дата: 10.10.2026. Батьківський маршрут: [М3 #5447](https://github.com/juv4uk/sens/issues/5447) → [Міграція #5440](https://github.com/juv4uk/sens/issues/5440) → [Епік #5438](https://github.com/juv4uk/sens/issues/5438). Узгодження з [М0 #5444](https://github.com/juv4uk/sens/issues/5444) (задачу взяв Vyasa) і [#5224](https://github.com/juv4uk/sens/issues/5224).

**Статус цього документа: ДОСЛІД / НЕ МІГРАЦІЯ.** Докази нижче — огляд файлів у зафіксованих Git-деревах, **не** результати запуску CI, тестів, FPGA або GPU. Жоден транспорт не переведено на `.senc`; `.sens` залишається канонічним T5, D1–D9 незмінні. Не плутати фізичний SENS-кодек із x86 ISA, UART job-frame, CML IR чи L1 device payload.

## Фіксовані джерела

| Репозиторій | Гілка на момент огляду | SHA |
| --- | --- | --- |
| `juv4uk/sens` | `main` | `02500ea33fb7a16fb534b309590fecf4125030c2` |
| `juv4uk/cml` | `master` | `2bd86998fde248c70d5e9d8c058c67f5d1428d81` |
| `juv4uk/fpga-lisp` | `master` | `f7e366e148a1e9370d0356fa21605d80601b701c` |
| `juv4uk/sens-futhark` | `main` | `c96551c2bd0689215c620726196508ba7bca151b` |
| `juv4uk/wsm-graalvm` | `main` | `e20f21a12d09fb99d2f18afaf5d83a7cf05ccb50` |

Git-дерева каталогів `src`, `scripts`, `host`, `fpga`, `futhark`, `tests` обійдені до файлів без `truncated`. **Це не доказ повної інвентаризації усіх згадок і викликів:** детальний зміст було перевірено тільки для перелічених нижче точок. Повний репозиторний census належить М0, а не цьому документу.

## Межі producer / consumer / validator

| Репозиторій/шлях | Роль | Реальний вхід → вихід / доказ у коді | Поточний носій; статус | Залежність / власна задача |
| --- | --- | --- | --- | --- |
| [CML `tests/core1_t5_to_native_test.rs`](https://github.com/juv4uk/cml/blob/2bd86998fde248c70d5e9d8c058c67f5d1428d81/tests/core1_t5_to_native_test.rs#L19-L49) | validator/consumer | `external/sens/tests/fixtures/core1-domain-canary/second.sens` → `fs::read`, 22 байти, pinned physical SHA-256, `sens::decode_ternary_program` → слова | **T5_REQUIRED**; наявність шляху у SENS upstream підтверджена, CI не запускався | [CML #695](https://github.com/juv4uk/cml/issues/695), М0, #5439 |
| [CML `src/sens_compiler_export.rs`](https://github.com/juv4uk/cml/blob/2bd86998fde248c70d5e9d8c058c67f5d1428d81/src/sens_compiler_export.rs#L90-L108) | consumer/validator | `compiler-semantic-input/1` → `sens::parse_binary_source_words(bits)`, `DomainIdentity`; це **текстовий транспорт слів**, не доказ `.sens`-декодера | **BLOCKED** як кандидат фізичної міграції (інша межа) | CML #695, #5439 |
| [CML `src/sens_c1_artifact.rs`](https://github.com/juv4uk/cml/blob/2bd86998fde248c70d5e9d8c058c67f5d1428d81/src/sens_c1_artifact.rs#L295-L312) | consumer/validator | C1 artifact → SENS admission → typed requests / C2 backend; заборонено виводити семантику з CML transport | **BLOCKED** для `.senc`, не ототожнювати artifact з T5 | CML #695 |
| [CML `src/fpga_transport.rs`](https://github.com/juv4uk/cml/blob/2bd86998fde248c70d5e9d8c058c67f5d1428d81/src/fpga_transport.rs#L1-L36) | producer/transport | ISA-1.1 UART bootloader / post-HALT monitor кадр із program words та регістрами | **BLOCKED** для фізичного SENS-кодека: окремий апаратний протокол | CML #695, FPGA #85 |
| [FPGA `job_transport.py`](https://github.com/juv4uk/fpga-lisp/blob/f7e366e148a1e9370d0356fa21605d80601b701c/job_transport.py#L44-L70) | consumer/producer | `CMLJ` request → валідація довжини/регістрів → UART bootloader bytes | **BLOCKED** для `.senc`; протокол CMLJ не є T5 | FPGA #85, #5295 |
| [FPGA `tests/test_job_transport.py`](https://github.com/juv4uk/fpga-lisp/blob/f7e366e148a1e9370d0356fa21605d80601b701c/tests/test_job_transport.py#L13-L42) | validator | позитивний frame-зразок та негативний duplicate-register test, **не** T5/F3/D2 oracle | **BLOCKED** для T5 доказу; тест не запускався у цьому аудиті | FPGA #85 |
| [FPGA `fpga/rtl/uart.sv`](https://github.com/juv4uk/fpga-lisp/blob/f7e366e148a1e9370d0356fa21605d80601b701c/fpga/rtl/uart.sv#L1-L18) | device transport | `tx_data` і `rx_data` 8 біт; цей модуль не засвідчує фізичний D2/T5 decoder | **BLOCKED/UNVERIFIED** для T5 та реального апаратного PASS | FPGA #85, #5377 |
| [FPGA `fpga/bench/dense_pack/packing_oracle.py`](https://github.com/juv4uk/fpga-lisp/blob/f7e366e148a1e9370d0356fa21605d80601b701c/fpga/bench/dense_pack/packing_oracle.py#L80-L135) | benchmark | оцінка бітової місткості SRAM/ROM; `semantic_authority: False` | **BLOCKED** для еквівалентності T5; не називати FPGA packed-size абсолютним доказом | FPGA #85, #5294 |
| [GPU `host/import_sens_fixture.py`](https://github.com/juv4uk/sens-futhark/blob/c96551c2bd0689215c620726196508ba7bca151b/host/import_sens_fixture.py#L20-L94) | producer/validator | `manifest.json` + `identity_vectors.csv` → SHA-256 + схема CSV → staged import | **BLOCKED** щодо `.sens`: CSV не T5 | GPU #132, М0 |
| [GPU `host/sens_compiler_request.py`](https://github.com/juv4uk/sens-futhark/blob/c96551c2bd0689215c620726196508ba7bca151b/host/sens_compiler_request.py#L80-L105) | consumer/validator | запит `compiler-semantic-input/1` і перевірка schema/digest | **BLOCKED** для `.senc` reader, поки немає М1 | GPU #132, #5445 |
| [GPU `futhark/packed_domain.fut`](https://github.com/juv4uk/sens-futhark/blob/c96551c2bd0689215c620726196508ba7bca151b/futhark/packed_domain.fut#L1-L45) | device reader/validator | L1 `bytes: []i64` з `bit_len` і `(offset,width)`; перевіряє межі/tail і читає точну ширину | **BLOCKED** для прирівнювання L1 до T5/F3; виконання GPU не перевірено | GPU #132, #5439 |
| [GraalVM `Reader.java`](https://github.com/juv4uk/wsm-graalvm/blob/e20f21a12d09fb99d2f18afaf5d83a7cf05ccb50/src/main/java/wsm/graalvm/Reader.java#L26-L56) | consumer/reader | `Reader(String text)` читає Lisp форми і стару декларацію `(binary WIDTH)`; цей код **не доводить** фізичний `.sens` loader | **BLOCKED/UNVERIFIED** для прямого T5/F3 ingress | GraalVM #301, М0, #5445 |
| [GraalVM `ReaderDatum.java`](https://github.com/juv4uk/wsm-graalvm/blob/e20f21a12d09fb99d2f18afaf5d83a7cf05ccb50/src/main/java/wsm/graalvm/ReaderDatum.java#L16-L34) | projection | reader syntax → Lisp values; не є фізичним SENS encoder | **BLOCKED** для транспорту; не переносити власну семантику | GraalVM #301, #5439 |

## Негативна матриця та межі доказу

| Хибна підміна | Незалежний контрприклад/перевірка, яку потрібно мати | Стан |
| --- | --- | --- |
| `CMLJ` UART кадр → `.sens` | Подати CMLJ у канонічний Rust T5 reader; очікується `reject`, без авто-конверсії | **UNVERIFIED**, власник FPGA #85 / CML #695 |
| `identity_vectors.csv` → `.sens` | CSV-фікстура не виконується як T5; лише SHA/schema перевірка свого контракту | **UNVERIFIED**, GPU #132 |
| L1 `(bit_len,offset,width)` → F3 без маркера | Передати L1 payload як `.senc` без F3/F4; `reject` до оцінки | **UNVERIFIED**, GPU #132 і #5439 |
| GraalVM текстова `(binary WIDTH)` → T5 | Заборонити трактувати текстову декларацію як фізичний F3/F4 заголовок | **UNVERIFIED**, GraalVM #301 |
| Фальшивий HW PASS | За відсутності плати/логів вимагати статус `UNVERIFIED`, не `GREEN` | **ПОЛІТИКА**, FPGA #85 |
| Заміна `.sens` у тріаді на `.senc` | `.lisp` + файл без розширення + `.sens` повинні зберегти ідентичні вихідні SHA після досліду | **UNVERIFIED**, М2 #5446 |

Наявність цих рядків — **не** результат запуску тестів. Негативні сценарії є конкретними вимогами до незалежних оракулів #5442, а не виміряним PASS.

## Порядок передачі М0 → М1/М2 → М3

1. **М0 #5444:** доповнити повний git-ls-files маніфест точними downstream path вище; якщо downstream непідконтрольний єдиному manifest, створити окремий дочірній snapshot з SHA та completeness gate; не позначати автоматично всі репозиторії «мігровано».
2. **М1 #5445 + ядро #5439:** надати один перевірений API фізичного T5, експеримент F3/F4 лише з явним opt-in, відмову на неправильному контейнері; downstream поки працює зі своїми чинними payloads.
3. **М2 #5446:** не міняти жодного з трьох канонічних файлів, не створювати другого implicit encoder через Graal/CML.
4. **М3 #5447:** після незалежних тестів зв'язати конкретні producer→consumer із byte SHA, версіями, runtime, HW-свідком чи `UNVERIFIED`; виміряти саме end-to-end на тому самому хості. Відкат = T5 unchanged, вимкнення opt-in F3/F4; не переносити помилку на інший формат.

## Оглядова методика і залишкові ризики

Джерело переліку — GitHub Git Trees із SHA, потім GitHub file reads з blob SHA. Вибірка каталогів не доводить відсутність невиявлених викликів, generated files, git submodule content або runtime-loaded paths. На оглянутих точках немає підтвердженого end-to-end F3/F4 hardware/runtime; це *негативний висновок про наявні докази*, а не про неможливість реалізації. Жоден бенчмарк чи CI тут не запускалися. Повний М0 з негативним тестом «невідомий `.sens` не зникає» — відповідальність окремого виконавця #5444.

## Виконаний незалежний негативний свідок М3

Додано файл tests/test_m3_cross_transport_rejection.py. Він використовує тільки чинний scripts/sens_t5_codec.py, не створює другого T5-кодека. Заморожений позитивний контроль: байт 0x11 дорівнює точному слову D3:001. Негативи: CMLJ, заголовок CSV GPU, текстове (binary 8), F3, F4 і неконічний F2.

Відтворення з кореня репозиторію:

    python3 -m unittest discover -s tests -p test_m3_cross_transport_rejection.py -v
    python3 -O -m unittest discover -s tests -p test_m3_cross_transport_rejection.py -v

Результат локального ізольованого Linux виконання 10.10.2026: 6/6 PASS у двох режимах. Перевірена точна Git blob SHA-1 відповідність виконаних файлів:
- scripts/sens_t5_codec.py — 44a17fc3df78ac13c2223eda2752742122745d4b (main 42e3945c5e8f27902ade6fedf52f54786c56f914).
- tests/test_m3_cross_transport_rejection.py — 55d711c92f5bd6cd59e6c526cac7231e304537ed (цей PR).

Доказ обмежений конкретними зразками, а не усіма UART, CSV, GPU L1 або D2 програмами. Незалежне Rust/D2/eval підтвердження залишається у #5439/#5313. GitHub-hosted CI для цього PR потрібно перевіряти окремо: локальні 6/6 не є загальним GREEN. Канонічний .sens не змінено.
