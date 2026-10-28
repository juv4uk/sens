# Три незалежні бенчмарки SENS: Rust, Zig, Lisp/SENS

Це **діагностика механізмів та фізичного мовного виконавця**, не порівняння
швидкості трьох мов і не нове джерело семантики. Відхилення продуктивності
на спільному CI-runner не блокує реліз без каліброваного бюджету.

| Шар | Реалізація | Фактична операція | Проби | Метрика |
|---|---|---|---|---|
| Rust / I/O | `crates/sens-cli/tests/mechanism_file_io_benchmark.rs` | `std::fs::read` байтів справжнього `benchmarks/lists.lisp` | 3 warmup + 11 timed samples; кожен ≥25 ms | raw sample + p50/p90/min/max ns/read, bytes |
| Rust / exact-width ingest | `crates/sens/examples/packed_vs_visible_bench.rs` | Видимі exact-width слова проти packed-носія, той самий D2 AST; межі ширин передаються явно | 32 парні warmup + 9 чергованих проб у кожному напрямку, кожна ≥25 ms | Сирі проби, p50/p90 ns/program, співвідношення, байти й semantic bits |
| Zig / ABI | `research/zig-codecs/tests.zig` | `transport_abi.zig`: точний D8 BE3 → T5 | 1 batch warmup + 7 timed samples; кожен ≥25 ms, batches адаптивні | raw elapsed/word counts + p50/p90/min/max ns/word |
| Zig / T5M | `bench_t5m.zig` (виконується центральним `ci.yml`) | Реальний `benchmarks/lists.sens`: encode/decode з канонічною byte parity | прогрів + 11 адаптивних проб, кожна ≥25 ms | raw elapsed/operation counts + min/p50/p90/max ns/op; фізичні негативи окремо |
| Lisp → Zig/T5M → SENS | `benchmarks/{lists,arithmetic,parser,recursion}.lisp` і `tests/semantic/` | Чотири мовні навантаження, вимір лише після успішного Lisp-закону | 11 + контрольний прогін | p50/p90 wall-time повного процесу (CLI + bootstrap + eval), AST та фізичний розмір |

Для D11 окремо діють `benchmarks/d11-families.lisp` та пара
`tests/semantic/d11-families-benchmark-{law,mutant}.lisp`.
Їхні вердикти видає **тільки SENS**, а Zig/T5M передає точні слова.
Використовуємо повний `scripts/prove-lisp-semantic-t5m.sh`:
нативний Lisp, mint, Zig open/verify, paired і standalone.

## Відтворення

```sh
# Rust: власний механізм читання, без виклику Lisp evaluator.
cargo test --locked -p sens-cli --test mechanism_file_io_benchmark -- --include-ignored --nocapture

# Rust: exact-width visible/packed ingestion; verifies matching D2 AST before timing.
bash benchmarks/rust-packed-visible/run.sh /tmp/rust-packed-visible

# Zig 0.16: точний ABI і adaptive ≥25 ms samples, без SENS-семантики.
zig test -lc research/zig-codecs/tests.zig

# Центральний CI викликає цей exact-corpus T5M benchmark і fail-closed negatives.
zig run -O ReleaseFast -lc bench_t5m.zig

# Фізичний SENS: спочатку наявна збірка, далі лише реальне виконання.
cargo build --locked -p sens-cli --bin sens --bin sens-trit --features benchmark-ast-visits
bash scripts/prove-lisp-semantic-t5m.sh \
  "$PWD/target/debug/sens" "$PWD/target/debug/sens-trit" \
  "$PWD/target/sens-benchmark-evidence"
```

## Конкурс: межі відповідальності

Це **три окремі номінації**, а не змагання Rust проти Zig проти SENS
за одне число. Рейтинг у кожній номінації складають **тільки** для
однакового навантаження, одиниці роботи та апаратного середовища.

| Номінація | Що може перевіряти й вимірювати | Що категорично не вирішує |
|---|---|---|
| Rust — **механізм** | Читання, алокації, пам'ять, виклики, CPU I-refs, wall-time, Linux RAPL (Дж) | Очікувану відповідь Lisp, істинність D1/D3/Dn, арифметику, закони предикатів |
| Zig — **коридор** | Кадри, T5M, точність ширини, байтову інверсію, ABI, пропускну здатність, затримку | Мовну семантику й арифметичні еталони SENS |
| SENS — **семантика й логіка** | Виконувані `.sens`/українські `.lisp` закони, істину/хибу, алгоритмічну правильність, негативні мутанти, еквівалентність задач | Фізичну вартість Rust-механізму або Zig-носія без вимірювання |

Порядок приймання кандидата: **SENS law PASS → Zig exact-byte/ABI PASS →
Rust measurement**. Якщо SENS-вердикт відсутній чи RED, результати
механічних вимірів допустимо зберігати як діагностику, але **конкурс
правильних програм = BLOCKED**. `cmp` двох виводів не доводить
математичної правильності, а лише фізичну тотожність спостережень.

Для енергії використовувати доступні `perf power/energy-*` або
`/sys/class/powercap/intel-rapl/.../energy_uj` з Linux: дві проби
навколо повторюваного пакета, `J/op = ΔJ/N`, сирі джоулі й точну
одиницю роботи. `energy-ram` та інші RAPL-домени опційні;
WSL2 не вважати апаратним енергетичним доказом без доступного лічильника.
Ті самі `SHA`, корпус, прогрів, порядок A/B і середовище записувати
для всіх трьох смуг. Не прирівнювати `ns/read`, `ns/word` і
`ns/evaluated form`.

**Поточне обмеження:** `benchmarks/contest-uk/judge.sh` і
`run-native.sh` ще містять Bash-таблиці очікуваних результатів.
Поки ці еталони не перенесено до виконуваних SENS-свідків,
не оголошувати конкурс доказом повної семантичної суверенності.

## Правила достовірності

1. Rust/I/O міряє лише файлове читання **warm-cache**, без SENS bootstrap чи семантики.
   Rust exact-width ingestion перевіряє однакову D2/domain-AST форму до таймера;
   межі ширин подано окремим розкладом і вони **не входять** у packed payload.
   Кожна проба адаптивно триває щонайменше 25 ms. Це порівняння reader paths,
   не self-describing container і не вимір семантики.
2. Zig вимірює **реальний** ABI T5 encode, не імітацію D8. Час
   `CLOCK_MONOTONIC` включає виклик кодувальника, перевірку статусу та
   накладні витрати циклу; це не незалежне вимірювання CPU instructions.
3. SENS визначає D1:1/D1:0 у `.lisp` і `.sens`; Rust або Zig не
   оголошують семантичного PASS. Діагностика часу ніколи не приховує RED.
4. **Не порівнювати числові p50 між стовпцями:** Rust вимірює файл, Zig
   окреме слово, SENS — цілий процес; різні знаменники і прогрів.
5. Для тверджень про прискорення потрібні однаковий корпус, машинне оточення,
   контроль компіляцій і парний дизайн ABBA/BAAB, як у
   `benchmarks/bench-methodology/README.md`. Поточні цифри — `MEASURED`,
   не `CERTIFIED_SPEEDUP`.

## Актуальні зразки методики

- [Criterion.rs](https://criterion-rs.github.io/book/) — прогрів,
  статистичні інтервали, виявлення шуму для Rust мікробенчмарків. Не додано
  нової залежності, щоб зберегти `Cargo.lock` та `cargo --locked`.
- [hyperfine](https://github.com/sharkdp/hyperfine) — окремі прогріви,
  багатократні запуски CLI, експорт сирих даних.
- [Zig Bench](https://github.com/zig-utils/zig-bench) — адаптивна кількість
  ітерацій, час прогріву та p50/p75/p99; беремо ці ідеї, не нову залежність.
- [Common Lisp cl-bench](https://cl-bench.common-lisp.dev/) — приклад
  розділення I/O, числових, рядкових, бітових і пам'яттєвих навантажень.
  Це набір для Common Lisp, не прямий performance ranking SENS.
- [Zig 0.16 release notes](https://ziglang.org/download/0.16.0/release-notes.html)
  і [приклад проблеми std.time.Timer](https://github.com/mattrobenolt/zig-benchmark/issues/1)
  — Linux Zig-бенчмарк використовує `CLOCK_MONOTONIC`.

Жоден із цих інструментів не підміняє фізичний виконуваний SENS-коридор.
