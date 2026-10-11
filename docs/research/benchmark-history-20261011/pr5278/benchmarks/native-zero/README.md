# SENS Native Zero v1 — реальне виконання фізичного T5

**Мета:** виміряти на одному CPU вже наявний шлях виконання
`.sens` → T5 (п'ять тритів на байт) → слова точних доменів D1–D9
→ читач структури D2 → виконавець SENS, **без Core4**.

Цей експеримент **не** є новим інтерпретатором, машинним кодом, LLVM,
вимірюванням CUDA/FPGA чи підтвердженим прискоренням. Жодного SID8,
текстового Lisp-роутера або словника англійських імен у фізичному шляху.
Інтерпретатор та закони D1/D2/D3 залишаються незміненими.

## Команда

```bash
cargo build --locked --release -p sens --example sens_native_zero_bench
target/release/examples/sens_native_zero_bench --samples 9 --iterations 128 \
  > /tmp/native-zero.jsonl
python3 benchmarks/native-zero/verify_report.py \
  --input /tmp/native-zero.jsonl --summary /tmp/native-zero.md
```

Перший корпус: реальний зафіксований 4-байтовий файл
`tests/fixtures/migration-quote-cohort-main/quote-legacy.sens`, який
має байти `63 89 06 a1`, плюс фізично упаковані (поза таймером)
коди D1 YES та D3 ATOM від структурного EMPTY. Вони перевіряють:
відтворення точного двійкового вигляду, канонічне перепакування, ідентичний
результат фізичного й видимого шляхів, D1 YES або D3 структурне EMPTY,
відсутність неочікуваного виводу, відмову на фізичному байті 243 та
незакритій структурі D2. **Якщо оракул відрізняється, виміри заборонено.**

## Протокол вимірювання

Для кожного прикладу — дев'ять пакетів зі 128 повторів, перед якими
є 16 прогрівів. Порядок двох шляхів чергується між пакетами.
Складові вимірюються окремо й не віднімаються одна від одної:

- **Фізичний T5, теплий bare-Session:** `eval_t5_program`, включаючи
  декодування, читач D2, зниження та виконання.
- **Видимий точний двійковий текст, теплий bare-Session:**
  `parse_canonical_binary` і той самий виконавець.
- **Новий bare-Session на кожен виклик:** обидва порівнянні повні шляхи.
- Діагностичні лінійки **декодер + граматика D2** та **виконання попередньо
  зниженої програми**; це не самостійне прискорення.

`ratio_visible_over_physical` — лише відношення двох виміряних медіан;
**понад 1** означає швидший фізичний шлях у цій вибірці, **менше 1** —
повільніший. Немає порога на «гарне» прискорення. Пам'ять, старт ОС,
файлове читання, холодний кеш диска, GPU, FPGA, x86 AOT та інша апаратура
не вимірюються.

GitHub workflow `.github/workflows/sens-native-zero.yml` створює
`native-zero.jsonl`, `summary.md` і `hardware.txt` та зберігає їх як
артефакт. Тільки фактичні дані конкретного запуску можуть потрапити в
підсумкову таблицю. Старі CI-блокери **не вимикаються**.

## Native Zero v2: once-validated reusable physical programs

The optional `prepare_t5_program(physical_bytes)` performs the SAME
canonical T5 transport validation, ratified exact-width D2 parse and existing
lowering ONCE. It returns an immutable `PreparedT5Program`. Its
`execute(&mut Session::bare())` invokes the existing evaluator. Execution
never caches semantic results, environment state or truth values, and does
not bypass wrong-domain exact D1 controls. Program preparation is required
before first execution; raw invalid bytes never enter this API.

```bash
cargo test --locked -p sens --test physical_t5_execution -- --nocapture
cargo build --locked --release -p sens --example sens_native_zero_prepared_bench
target/release/examples/sens_native_zero_prepared_bench --samples 9 --iterations 128 \
  > /tmp/native-zero-prepared.jsonl
python3 benchmarks/native-zero/verify_prepared_report.py \
  --input /tmp/native-zero-prepared.jsonl --summary /tmp/native-zero-prepared.md
```

The second benchmark contrasts **different workloads**: the direct physical
path decodes, parses and lowers on EVERY call, whereas prepared reuse pays
those costs ONCE, outside the timed repeat phase. The one-time preparation
duration is reported alongside the repeated costs. A large amortization ratio
is not evidence that one T5 decode became faster. This is a measured
predecode mechanism, **not** native x86 AOT, an interpreter replacement,
or a justification to skip still-failing integration gates.

User-controlled sessions remain fresh or warm as labeled. D3 QUOTE (committed
physical bytes), exact D1:YES and D3 ATOM produce matched exact semantic
results under both modes and reject malformed transport at preparation.

## Окремий запуск фізичного файлу (без Core4)

```bash
cargo build --locked --release -p sens --example sens_native_zero_file
target/release/examples/sens_native_zero_file \
  tests/fixtures/migration-quote-cohort-main/quote-legacy.sens
```

Очікуваний структурний результат: `VALUE=()`, `KIND=NON-D1`.
Це явний запуск **справжнього файла .sens**, а не переведення текстового
імені та не автоматичне виконання при відкритті. Спочатку файл проходить
фізичну T5 / D2 admission, після чого виконується на `Session::bare()`.
Виконання не завантажує Core4 і не надає I/O / GPU / host capabilities.
Невалідний T5, незакрита D2-структура або файл без розширення `.sens`
не запускаються.
