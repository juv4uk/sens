# Фізичний SENS: чесний T5→AST benchmark (2026-10-09)

**Ключове порівняння:** дві повні реалізації *одного* завдання —
прочитати ті самі фізичні байти T5 і побудувати канонічний D2 AST.
Це не порівняння мови SENS з Python або англійським Lisp.

- GitHub-hosted release-прогін: [#37980668949](https://github.com/juv4uk/sens/actions/runs/37980668949) — **success**.
- Вимірюваний SHA: `54a5b2ed8a26d40eedd009e54df979167da25930`.
- Виконавець: `crates/sens/examples/physical_sens_hot_bench.rs`.
- Середовище: GitHub-hosted `ubuntu-24.04`; один процес із прогрівом,
  11 незалежних серій, фіксований сумарний work budget.
- Перед заміром усі AST-шляхи виконувалися чинним evaluator та звіряли
  однаковий спостережуваний результат. Це перевірка паритету реалізації,
  а не незалежний доказ семантичного закону.

| D3 QUOTE форми | Точний фізичний T5 | T5→текст→D2 AST, p50 | T5→типовані слова→D2 AST, p50 | Текст/двійковий |
|---:|---:|---:|---:|---:|
| 1 | 4 Б | 946 нс | 401 нс | 2,359× |
| 16 | 55 Б | 12 902 нс | 4 592 нс | 2,810× |
| 128 | 435 Б | 105 742 нс | 35 924 нс | 2,943× |
| 1024 | 3 482 Б | 1 119 179 нс | 406 346 нс | 2,754× |

**Важлива поправка до старого scoreboard:** `t5_open_d2`
лише відкриває T5 як текст і **не** будує AST.
Порівняння `t5_open_d2 / t5_words_d2` не було рівноцінним.
Справедлива пара — `t5_visible_parse_d2 / t5_words_d2`:
обидва шляхи повністю обробляють фізичний T5 до того самого D2 AST.
Зміна застосована в [`043f39e8`](https://github.com/juv4uk/sens/commit/043f39e8081d88c57fff72122d62d4545afa964b).

## Що вимірюємо, а чого ні

- **Так:** вартість повного читання T5→D2 AST для цього corpus,
  на одному SHA/runner; щільність фактичних T5-байтів.
- **Ні:** швидкість довільної SENS-програми, незалежну Lisp semantic parity,
  GPU/FPGA, перевагу над CPython або міжмашинний коефіцієнт.
- Вивід p50 змінюється від шуму shared runner; порівнювати лише
  парні вимірювання в одному прогоні, не змішувати SHA.
- Пріоритет наступного заміру: реальні D5 рекурсія, копіювання та MAP
  поруч із повним reader pipeline та `eval_lowered`.

Відтворення на GitHub-hosted runner:
```sh
cargo build --locked --release -p sens --example physical_sens_hot_bench
python3 benchmarks/physical-sens-runtime/hot.py \
  --binary target/release/examples/physical_sens_hot_bench \
  --sizes 1,16,128,1024 --samples 11 --work-budget 65536 \
  --out /tmp/sens-physical-bench
python3 benchmarks/current-en-vs-d1d8/performance_scoreboard.py \
  --physical-hot-json /tmp/sens-physical-bench/hot-results.json \
  --out /tmp/sens-physical-bench/scoreboard.md
```

**Головний принцип:** на benchmark-first шляху кожне твердження
про прискорення має точно визначати дві рівноцінні роботи,
однакові фізичні входи, спосіб вимірювання, SHA та runner.
