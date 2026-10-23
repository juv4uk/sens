# Три незалежні бенчмарки SENS: Rust, Zig, Lisp/SENS

Це **діагностика механізмів та фізичного мовного виконавця**, не порівняння
швидкості трьох мов і не нове джерело семантики. Відхилення продуктивності
на спільному CI-runner не блокує реліз без каліброваного бюджету.

| Шар | Реалізація | Фактична операція | Проби | Метрика |
|---|---|---|---|---|
| Rust / I/O | `crates/sens-cli/tests/mechanism_file_io_benchmark.rs` | `std::fs::read` байтів справжнього `benchmarks/lists.lisp` | 3 warmup + 11 timed samples; кожен ≥25 ms | raw sample + p50/p90/min/max ns/read, bytes |
| Zig / носій | `research/zig-codecs/tests.zig` | чинний `transport_abi.zig`: точний D8 BE3 → T5 | 1 batch warmup + 7 timed samples; кожен ≥25 ms, batches адаптивні | raw elapsed/word counts + p50/p90/min/max ns/word |
| Lisp → Zig/T5M → SENS | `benchmarks/{lists,arithmetic,parser,recursion}.lisp` і `tests/semantic/` | чотири нативні мовні навантаження, лише після успішного Lisp-закону | 11 + контрольний прогін | p50/p90 wall-time процесу, AST та розмір носія |

Для D11 окремо діють `benchmarks/d11-families.lisp` та пара
`tests/semantic/d11-families-benchmark-{law,mutant}.lisp`.
Їхні вердикти видає **тільки SENS**, а Zig/T5M передає точні слова.
Використовуємо повний `scripts/prove-lisp-semantic-t5m.sh`:
нативний Lisp, mint, Zig open/verify, paired і standalone.

## Відтворення

```sh
# Rust: власний механізм читання, без виклику Lisp evaluator.
cargo test --locked -p sens-cli --test mechanism_file_io_benchmark -- --include-ignored --nocapture

# Zig 0.16, -lc для CLOCK_MONOTONIC. Механічні тести й виміри разом.
zig test -lc research/zig-codecs/tests.zig

# Фізичний SENS: спочатку наявна збірка, далі лише реальне виконання.
cargo build --locked -p sens-cli --bin sens --bin sens-trit --features benchmark-ast-visits
bash scripts/prove-lisp-semantic-t5m.sh \
  "$PWD/target/debug/sens" "$PWD/target/debug/sens-trit" \
  "$PWD/target/sens-benchmark-evidence"
```

## Правила достовірності

1. Rust міряє лише файловий I/O. ОС може кешувати файл; вимір **warm-cache**,
   без SENS bootstrap чи семантики. Рівність байтів перевіряємо **після**
   таймера.
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
