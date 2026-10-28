# Три незалежні бенчмарки SENS: Rust, Zig, Lisp/SENS

Це **діагностика механізмів та фізичного мовного виконавця**, не порівняння
швидкості трьох мов і не нове джерело семантики. Відхилення продуктивності
на спільному CI-runner не блокує реліз без каліброваного бюджету.

| Шар | Реалізація | Фактична операція | Проби | Метрика |
|---|---|---|---|---|
| Rust / exact-width ingest | `crates/sens/examples/packed_vs_visible_bench.rs` | Видимі exact-width слова проти packed-носія, той самий D2 AST; межі ширин передаються явно | 32 парні warmup + 15 чергованих проб у кожному напрямку, кожна ≥25 ms | Сирі проби, p50/p90 ns/program, співвідношення, байти й semantic bits |
| Zig / ABI | `research/zig-codecs/tests.zig` | Перевірка фізичного транспортного ABI, без логічного оракула | Виконується перед вимірюванням T5M | Тестовий вердикт коридору, не швидкість |
| Zig / T5M | `bench_t5m.zig` (ручний конкурс; центральний `ci.yml` окремо) | Реальний `benchmarks/lists.sens`: encode/decode з канонічною byte parity | прогрів + 11 адаптивних проб, кожна ≥25 ms | raw elapsed/operation counts + min/p50/p90/max ns/op; фізичні негативи окремо |
| SENS / логіка | `tests/semantic/бенчмарк-структура-{law,mutant}.lisp` через `scripts/prove-бенчмарк-структура.sh` | Нативний позитивний закон і негативний мутант; Zig/T5M як коридор | 11 часових проб після обох свідків | p50/p90 мкс на нативний CLI-прогін, без висновку про прискорення |

Для D11 окремо діють `benchmarks/d11-families.lisp` та пара
`tests/semantic/d11-families-benchmark-{law,mutant}.lisp`.
Їхні вердикти видає **тільки SENS**, а Zig/T5M передає точні слова.
Цей D11-корпус **не входить** до ручного workflow конкурсу: без розширення релізного scope.

Центральний `ci.yml` не змінюється. Існуючий `native-rust-zig-sens-bench.yml` — **тільки `workflow_dispatch`**, три незалежні jobs, без Python/JSON і без зміни семантики або релізного гейта.

## Відтворення

```sh
# Rust: механічний exact-width reader, 15 проб на кожен із 5 випадків.
cargo run --locked --release -p sens --example packed_vs_visible_bench -- --samples 15

# Zig: спершу транспортні негативи, потім 11 фізичних T5M-проб.
zig test -lc research/zig-codecs/tests.zig
zig test -O ReleaseFast -lc bench_t5m_test.zig
zig run -O ReleaseFast -lc bench_t5m.zig

# SENS: лише сам SENS вирішує закон і мутант; shell фіксує фактичний вихід.
cargo build --locked -p sens-cli --bin sens
bash scripts/prove-бенчмарк-структура.sh "$PWD/target/debug/sens"
```

## Правила достовірності

1. Rust exact-width ingestion вимірює лише механізм і перевіряє однакову D2/domain-AST форму до таймера;
   межі ширин подано окремим розкладом і вони **не входять** у packed payload.
   Кожна Rust-проба адаптивно триває щонайменше 25 ms. Це порівняння reader paths,
   не self-describing container і не вимір семантики.
2. Zig вимірює **реальний** ABI T5 encode, не імітацію D8. Час
   `CLOCK_MONOTONIC` включає виклик кодувальника, перевірку статусу та
   накладні витрати циклу; це не незалежне вимірювання CPU instructions.
3. SENS перевіряє позитивний закон і негативний мутант у власній мові;
   Rust або Zig не оголошують семантичного PASS. Діагностика часу ніколи не приховує RED.
4. **Не порівнювати числові p50 між стовпцями:** Rust вимірює читання
   exact-width форм, Zig — T5M транспорт, SENS — цілий процес;
   різні знаменники і прогрів.
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
