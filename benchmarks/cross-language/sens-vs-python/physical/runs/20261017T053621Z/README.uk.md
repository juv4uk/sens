# Фізична SENS-програма проти Python source: D5 LABEL COPY

**Статус: один валідний source-to-result research pilot; не повний benchmark мов.**
SENS-сторона запускає поточний production `sens-trit eval` на фізичному T5
файлі, а Python-сторона — CPython безпосередньо на `.py` source. Порівнюються
вхідні представлення й повний виклик двох конкретних рушіїв; немає файлу
попередньо збереженого Python `.pyc` і немає твердження, що SENS вже має
native compiler або machine code.

SENS-вхід походить із tracked `examples/binary/d5-label-copy.bits`: кожне
джерельне слово є exact-width координатою, а T5-кодек лише переносить ці
слова фізичними тритами. Benchmark створив T5-файл **до таймера**, перевірив
production `sens-trit open`, а потім виконував `sens-trit eval`. Python source
рекурсивно копіює таку саму proper pair-list. Обидві сторони до вимірювання і
в кожному запуску видали точно `(1 0 ())\n`.

## Результат

Один збалансований запуск: 10 warmup-пар, потім 100 пар із перемішаним
порядком сторін; усі 100 пар пройшли перевірку stdout. Median — звичайна
медіана 100 спостережень; p95 та p99 — nearest-rank. Кожен sample — новий
процес, отже це навмисно end-to-end latency, а не CPU-only steady state.

| Вимір | SENS `sens-trit eval` · T5 | CPython · `.py` source |
|---|---:|---:|
| n вимірів / warmup-пар | 100 / 10 | 100 / 10 |
| median wall time | 2.915 ms | 20.414 ms |
| p95 wall time | 4.188 ms | 25.696 ms |
| p99 wall time | 6.404 ms | 28.872 ms |
| окремий процесний peak RSS | 3,028 KiB | 10,520 KiB |

Медіани цього запуску дають описове відношення Python/SENS **7.00×**. Воно
включає запуск CLI та CPython, читання фізичного/текстового файла, T5 decode
або CPython source compilation, виконання, stdout і завершення процесу. Для
такого короткого алгоритму startup помітний і результат не відокремлює його
від виконання. Окремий RSS-показник виміряний одним викликом GNU `time` на
сторону; це peak усього процесу, не median, не delta алгоритму та не пам'ять
лише pair-list.

Графіки: [boxplot](boxplot.svg) · [гістограма](histogram.svg). Повний масив
усіх 100 тривалостей і provenance: [`source-copy-raw.json`](source-copy-raw.json).
Машинні агрегати, обчислені без зміни raw samples: [`summary.json`](summary.json).
Окрема одноразова RSS-спостережна точка та точна команда: [`memory-observation.json`](memory-observation.json).

## Provenance

- Benchmark/source repository HEAD: `00be8c4b611e9d585f8338473d9982d2e35c533c`
- Фізичний T5 SHA-256: `42ce3dcd631b2ac9081ea7f3764a50b3bf81f025b3e109793eef2527490b54a5`
- Вихідні exact-width слова `examples/binary/d5-label-copy.bits` SHA-256:
  `8151048e0fc8140c7417de7a38e8a594f60e6e077587aa667bdfb3f143984847`
- Python fixture `recursive_pair_copy.py` SHA-256:
  `ff72d75edb19990c64734011d1508efbdca9e0f71d4e6149734d9c8b2b75bee6`
- `sens-trit` binary SHA-256:
  `988e233a439f5a2b7fcdc9b996d5d3207e5b34929b6685d60ba308cd0eeec038`
- Бінарник зібраний із worktree commit
  `d5141f0287eed1c4a35c16755bd0ce457048c2c5`; перевірено, що версія цього
  commit і HEAD `00be8c4b` ідентичні для `Cargo.toml`, `Cargo.lock`, `crates/sens`,
  `crates/sens-cli/Cargo.toml` та `sens-trit.rs`.
- Entry point CLI: `crates/sens-cli/src/bin/sens-trit.rs`.
- Хост: WSL2 x86-64, Intel Core i5-6400 @ 2.70 GHz; kernel
  `Linux 6.18.33.2-microsoft-standard-WSL2`; CPython `3.12.12`; Rust
  `1.99.0`; pinned Zig `0.16.0`.
- Preflight перед заміром: `wsm-agent bench-ready` → `READY`, load1 `0.35`.

Часовий прогін відтворюється з кореня SENS так:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  benchmarks/cross-language/reality-matrix/physical-sens/source_copy_bench.py \
  --sens-trit /home/agents/work/sens-vs-python-benchmark/target/release/sens-trit \
  --reps 100 --warmups 10 --seed 20261018 --out OUT.json
```

RSS знімався окремим одноразовим запуском GNU `time -f 'max_RSS_KiB=%M'` над
тим самим бінарником `sens-trit eval` і Python fixture. Відтворення (виконуйте
з кореня checkout SENS; `sens-trit` має бути зібраний із pinned Zig):

```sh
rss_dir=$(mktemp -d /tmp/sens-physical-rss.XXXXXX)
cp examples/binary/d5-label-copy.bits "$rss_dir/d5-label-copy.lisp"
target/release/sens-trit encode "$rss_dir/d5-label-copy.lisp"
/usr/bin/time -f 'max_RSS_KiB=%M' \
  target/release/sens-trit eval "$rss_dir/d5-label-copy.sens"
/usr/bin/time -f 'max_RSS_KiB=%M' \
  python3 -B benchmarks/cross-language/reality-matrix/physical-sens/fixtures/recursive_pair_copy.py
```

Обидва окремі процеси видали той самий stdout; у JSON часу збережений кожен
парний sample та порядок.

## Що поки не можна чесно порівнювати

У репозиторії є ще фізичні D5 witnesses `d5-label-recursion` та
`d5-label-map`; їхній фізичний запуск повернув відповідно `1` і
`((1) (0) (()))`. Це підтверджує виконуваність, але поки немає перевірених
Python source-аналогів із точним спільним описом поведінки, тож лише збіг
stdout не достатній для включення їх у timed table.

Початкові стандартні workload-и `binary-trees`, `fib`, `Ackermann`, n-body,
Mandelbrot, regex та JSON не мають тут доведених пар «поточний executable
фізичний T5 + семантично ідентичний Python source». Попередні три evaluator
прогони не закривають цю прогалину: вони використовували Rust `Session` із
заздалегідь розібраною SENS-програмою, а не фізичний T5 ingress. Тому повний
план 3–5 стандартних workload-ів залишається **BLOCKED**, і цей pilot не
дозволяє оголосити загального переможця.
