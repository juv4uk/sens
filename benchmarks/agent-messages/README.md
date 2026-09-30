# Агентські повідомлення: SENS проти CPython

Питання: чи має SENS місце там, де агенти обмінюються маленькими програмами й
одразу їх виконують? Бенчмарк міряє саме цю нішу, а не абстрактну швидкість.

**Задача absolute-binary lane:** #1845.

*English layer: a stream of N small, different programs (expressions, lambda
application, a conditional, list access, a small recursion) is received as bytes
and executed immediately in one long-lived session. Cost per message = decode +
execute, in CPU instructions (Cachegrind), plus message size in bytes.*

## Що міряється

Той самий потік із 1000 програм у шести формах:

| форма | що це |
|---|---|
| `sens-fasl` | SENS, двійковий fasl (кеш розбору ядра), функція = 1 байт |
| `sens-wire` | SENS, компактний формат обміну `SW\\x01`: без хешу, малі цілі й короткі списки — 1 байт, довжини — varint |
| `sens-en` | той самий SENS англійським текстом (розбір тексту) |
| `py-src` | CPython, текст Python: `compile` + `exec` |
| `py-marshal` | CPython, заздалегідь скомпільований байткод: `marshal.loads` + `exec` |
| `py-json` | AST у JSON + маленький інтерпретатор на Python |

- Вартість повідомлення = (режим − база) / N. База `base` — старт процесу,
  читання файлу й створення сесії; вона показана окремо як «старт процесу».
- Спершу правильність: відповідь кожної форми на кожне повідомлення звіряється з
  CPython; неправильна відповідь — збій, а не число.
- Генератор детермінований (`--seed 1`).
- **Не змішувати** cold-start, warm-session і size в один слоган «швидший за Python».

```sh
cargo build --release -p sens --example agent_bench
guix time-machine -C channels.scm -- shell -m manifest.scm \
  -m benchmarks/agent-messages/manifest.scm -- \
  python3 benchmarks/agent-messages/run.py \
    --agent-bench target/release/examples/agent_bench --out /tmp/agent-messages
```

## Результат

### Поточний повний прогін (main `86e836be`, 2026-09-30)

`results/20260930/report.md` — усі шість форм, oracle GREEN, Cachegrind.

| форма | байт | warm разом | старт процесу |
|-------|-----:|-----------:|--------------:|
| sens-fasl | 154.1 | **53 438** | ~1.52M |
| sens-wire | **34.3** | 55 848 | ~1.52M |
| sens-en | 44.4 | 144 170 | ~1.52M |
| py-src | 46.4 | 202 302 | ~76M |
| py-marshal | 195.9 | **14 003** | ~76M |
| py-json | 48.4 | 70 324 | ~76M |

1. **Cold / tool-call:** SENS start ~1.5M vs CPython ~76M (~50× на цьому host).
2. **Warm:** fasl ×3.8 vs py-src, ×1.3 vs py-json; **×0.26 vs py-marshal** (програємо).
3. **Size:** wire 34 B — найменший.

### P1 — wire як транспорт контракту

`results/20260930/p1-wire-as-transport.md` — payload-only розклад; wire vs JSON
(size + decode); absolute-binary гіпотеза окремо від виміру.

### Історичний baseline (i5-6400 Guix)

`results/20260927/report.md` — той самий порядок висновків; абсолютні I-refs інші.

### Частковий прогін (без agent_bench)

`results/20260930-partial/report.md` — лише sizes + CPython.

## Межі

- Програми маленькі й прості; для важких обчислень див. `benchmarks/cross-language`.
- `py-marshal` залежить від версії CPython (байткод непереносний між версіями),
  а fasl/wire SENS — ні; у цьому бенчмарку portability не міряється окремо.
- Бібліотека core SENS не завантажується; повідомлення користуються лише
  примітивами мови.
