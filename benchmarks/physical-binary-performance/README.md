# SENS: вимірювання фізичної двійкової мови

Це **вимірювання**, а не тест з фіксованим числом інструкцій чи оголошений рейтинг мов.
Програми читаються з уже наявних фізичних `.sens`-файлів через два реальні
виконавчі CLI. Третя дорога вимірює декодування `.sens → видимі 0/1`.

## Що вимірюється

- `physical_bytes`: реальні байти T5-файлу, а не теоретичний lower bound;
- `visible_binary_bytes`: кількість ASCII-байтів у текстовій проєкції без фінального newline;
- `first_process_ms`: перша виміряна команда після попереднього parity-прогону;
- `median_wall_ms`, `p95_wall_ms`, `wall_cv`: медіана, p95 nearest-rank, коефіцієнт варіації;
- `cachegrind_i_refs`: дійсні instruction references процесу (тільки з `--cachegrind`).

Кожен вимір запускає **окремий процес**. Це показник startup + читання +
декодування + виконання + stdout (залежно від lane), **не** чистий hot evaluator
і **не** число інструкцій мови SENS. Ланки `sens-exec` та `sens-trit-eval`
виконують однаковий фізичний файл, але запускаються різними CLI.

Бенчмарк допускається тільки якщо stdout двох виконавців збігається
байт-у-байт, повтори детерміновані, а `sens-trit open` дає лише 0/1 слова.
Це лише паритет механізмів; семантичний оракул живе в SENS, а не в Rust/Python.

## Відтворення

```sh
cargo build --locked --release -p sens-cli --bin sens --bin sens-trit
python3 benchmarks/physical-binary-performance/run.py \
  --sens target/release/sens \
  --sens-trit target/release/sens-trit \
  --reps 21 --warmup 4 --out /tmp/sens-physical-bench
cat /tmp/sens-physical-bench/report.md
```

Для вимірювання інструкцій CPU встановіть Valgrind і додайте `--cachegrind`.
Таблиці `raw.tsv`, `results.json`, `report.md` включають SHA коміту,
CPU/runner, фізичний розмір, час і за наявності instruction references.

**Порівнювати** результати на одному і тому ж процесорі, зі схожим
навантаженням, тим самим корпусом і версією коду. GitHub-hosted runner може
змінювати фізичний CPU; CI дає вимір, а не абсолютний об'єктивний рейтинг.

Цей стенд не відключає Vertical Day / регресійні оракули: вимірювання
непрацездатної програми не допускається.
