# D5 hot execution — перший відтворений p50/p95 baseline

**Важливо:** це вимірювання реальних `.sens`-програм, а не Rust unit test або
гіпотетична швидкість. Результат стосується **одного GitHub-hosted runner**
та одного SHA, без права переносити коефіцієнт на інші машини.

- **Успішний прогін:** [Current physical SENS performance benchmarks #37980058462](https://github.com/juv4uk/sens/actions/runs/37980058462).
- **Точний SHA:** `856423265ae5e368c092a21499903e5b731fe88a`.
- **Корпус:** `examples/binary/d5-label-recursion.bits`, `d5-label-copy.bits`,
  `d5-label-map.bits`, без текстових імен у виконуваній програмі.
- **Файл:** точні слова `parse_words` → фізичний T5 `encode_words` →
  production `decode_ternary_words` → `parse_canonical_word_sequence` → evaluator.
- **Метод:** 9 незалежних серій по 64 операції після прогріву, `Instant`,
  p50 і p95 із сирих samples, таймінг **без запуску нового процесу**.
- **Перед вимірюванням:** тотожні stdout від production `sens` і `sens-trit eval`;
  обидва CLI та hot example отримують **однакові фізичні байти T5**.
  AST/lowered результати та стійкість між серіями також звірено.
  Ці перевірки **не є незалежним семантичним оракулом**.

| D5 двійкова програма | Фізичний T5 | T5→D2, p50 / p95 | eval AST, p50 / p95 | eval lowered, p50 / p95 |
|---|---:|---:|---:|---:|
| LABEL recursion | 54 Б | 5 537 / 6 224 нс | 7 628 / 8 462 нс | **5 335 / 5 726 нс** |
| LABEL copy | 66 Б | 6 650 / 7 098 нс | 11 826 / 15 529 нс | **9 050 / 9 488 нс** |
| LABEL MAP | 95 Б | 9 926 / 10 155 нс | 16 155 / 16 854 нс | **12 752 / 13 982 нс** |

Усі клітинки — виміри **окремих фаз**. `eval AST` здійснює lowering при
кожному виклику; `eval lowered` використовує попередньо підготовлений код.
Це порівняння вартості підготовки в **тому самому evaluator**, а не
порівняння SENS з Python або Lisp-субстратами.

Примітка про наступні оптимізації: сам T5→D2 коштує на цих
малих програмах порівнянно з одним викликом evaluator. Тому
оптимізувати cold-start і hot execution треба **окремо**, а не
маскувати одне середнім часом запуску процесу.

### Як відтворити

```sh
cargo build --locked --release -p sens-cli --bin sens --bin sens-trit
cargo build --locked --release -p sens --example physical_sens_d5_hot_bench
python3 benchmarks/physical-sens-runtime/d5_hot.py \
  --helper target/release/examples/physical_sens_d5_hot_bench \
  --sens target/release/sens \
  --sens-trit target/release/sens-trit \
  --reps 9 --iterations 64 \
  --out /tmp/sens-d5-hot
```

`d5-hot-raw.tsv`, `d5-hot-results.json`, `d5-hot-environment.json` і
`d5-hot-report.md` збережено як GitHub Actions artifact цього прогону;
коміт із цим Markdown лише фіксує інтерпретацію пінованих вимірювань.
