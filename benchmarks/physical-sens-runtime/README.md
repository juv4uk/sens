# Фізичний SENS — об’єктивний runtime benchmark

Вимірюються **реальні виконувані файли** `.sens` у release-збірці з точним
T5-транспортом, канонічною D2-структурою та D3 QUOTE-послідовностями.

Стенд навмисно відділяє:
- **`sens-exec`** — запуск `sens file.sens`, включно з cold process, T5, D2 і виконанням;
- **`sens-trit-eval`** — другий CLI тієї ж реалізації; parity обов'язкова, це *не* конкурент іншою мовою;
- **`rust-t5-view`** і **`python-t5-view`** — незалежні реалізації відкриття й відображення того самого T5 без виконання;
- **обсяг файлів** — packed T5 проти пробільного ASCII-перегляду, у байтах.

Проведення: 3 прогрівальні і 19 вимірюваних запусків кожної lane
на кожному навантаженні (1, 16, 128 і 1024 незалежних форм).
Порядок lane чергується; записуються **сирі наносекунди**, медіана, p95,
пропускна здатність у формах/с, SHA-256 і версії середовища.

```bash
cargo build --release --locked -p sens-cli --bin sens --bin sens-trit
python3 benchmarks/physical-sens-runtime/run.py \
  --sens target/release/sens \
  --sens-trit target/release/sens-trit \
  --out /tmp/sens-physical-bench --reps 19 --warmups 3
```

Вихід: `raw.tsv`, `results.json`, `environment.json`, `report.md`.
На GitHub — workflow `physical-sens-benchmark.yml`, GitHub-hosted runner.

**Заборона хибних висновків:** час із запуском процесу не є чистим часом
обчислень; однаковий SENS oracle в обох CLI не є міжмовною перевіркою.
Спільний runner має фонове навантаження, тому окремі p50/p95 — свідчення,
не жорстка регресійна межа. Немає доказу переваги над Python як
повноцінною мовою без окремого спільного алгоритмічного workload.

## Гарячі фази — без вартості запуску процесу

```bash
cargo build --locked --release -p sens --example physical_sens_hot_bench
python3 benchmarks/physical-sens-runtime/hot.py \
  --binary target/release/examples/physical_sens_hot_bench \
  --out /tmp/sens-physical-bench --samples 11 --work-budget 65536
```

Цей експеримент **окремий від cold startup**. Він вимірює чотири фази
одного процесу: `t5_open_d2`, `d2_parse`, `eval_from_ast` та
`eval_lowered`. Для кожного розміру — 11 незалежних серій з
однаковим бюджетом сумарно оброблених форм; результат кожної серії
записано в `hot-raw.tsv`, агрегати в `hot-results.json`, середовище
в `hot-environment.json`, таблицю в `hot-report.md`.

`eval_from_ast` включає lowering кожного виклику, а
`eval_lowered` працює зі зниженим представленням і повторно
використовує сесію. Попередня перевірка тотожності результатів
не входить у замір; числові бенчмарки не ратифікують нових законів.
Варіюється кількість незалежних форм D3 QUOTE, а не алгоритмічна складність.

## Новий прямий шлях без проміжного тексту

[Перший успішний пінований baseline direct T5→D2 від 2026-10-09](direct-t5-baseline-2026-10-09.md)
містить точні p50, p95, байти, physical subprocess і in-process вимірювання,
прив'язані до коміту `29890ccb504fa1b266a9f16cd1172dbee8d3cdfd` та
[успішного GitHub-hosted run #37978341427](https://github.com/juv4uk/sens/actions/runs/37978341427).

Самодостатній direct T5→D2 швидший за наявний T5→текст→D2 **на цьому
вузькому корпусі**. Не переносити ratio на довільний SENS-код або інші машини.

## Прямий читач типованих слів — typed-word fast path

Після фізичного декодування T5 кожне слово вже знає точну ширину D1–D9.
Тому новий канонічний адаптер `parse_canonical_word_sequence` передає слова
в *той самий* D2 reader без зайвого `pack_binary_source_words` та
`unpack_binary_source_words`. Цей шлях використовують `sens file.sens`,
`sens-trit eval` і внутрішня перевірка T5-структури.

Нові фази у `hot-report.md`:

- `t5_direct_d2`: **попередній** шлях T5→типовані слова→щільне пакування→розпакування→D2;
- `t5_words_d2`: **новий** шлях T5→типовані слова→D2 без повторного пакування.

Обидва сценарії починаються з *тих самих байтів*, використовують один D2
читач і до таймінгу мають дати ідентичний спостережуваний результат.
Відношення `old/new` обчислюється з медіан одного GitHub runner і є лише
доказом для конкретного навантаження та SHA, не універсальним прискоренням.
