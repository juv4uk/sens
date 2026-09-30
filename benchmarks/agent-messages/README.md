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
| `sens-wire` | SENS, компактний формат обміну `SW\x01`: без хешу, малі цілі й короткі списки — 1 байт, довжини — varint |
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

### Повний baseline (SENS + CPython)

Див. `results/20260927/report.md` (i5-6400; Guix). Висновки:

1. **Один процес на повідомлення — SENS у ~60 разів легший.** Старт SENS
   ≈1,5 млн інструкцій, CPython ≈94 млн.
2. **Warm session:** fasl швидший за py-src (×4) і py-json (×1,3), повільніший за
   py-marshal (×3,7). Decode fasl≈marshal (~10k); різниця в execute.
3. **SENS wire найменший: ~34 байти** (проти en 44, py-src 46, json 48, fasl 154).

### Частковий remeasure 2026-09-30

`results/20260930-partial/report.md` — розміри + CPython Cachegrind на іншому
host; **без** `agent_bench` (SENS binary encode/run). Підтверджує детерміновані
розміри text/json/marshal і порядок warm CPython: marshal ≪ json ≪ src.

## Межі

- Програми маленькі й прості; для важких обчислень див. `benchmarks/cross-language`.
- `py-marshal` залежить від версії CPython (байткод непереносний між версіями),
  а fasl/wire SENS — ні; у цьому бенчмарку portability не міряється окремо.
- Бібліотека core SENS не завантажується; повідомлення користуються лише
  примітивами мови.
