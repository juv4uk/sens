# Агентські повідомлення: SENS проти CPython

Питання: чи має SENS місце там, де агенти обмінюються маленькими програмами й
одразу їх виконують? Бенчмарк міряє саме цю нішу, а не абстрактну швидкість.

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

```sh
cargo build --release -p sens --example agent_bench
guix time-machine -C channels.scm -- shell -m manifest.scm \
  -m benchmarks/agent-messages/manifest.scm -- \
  python3 benchmarks/agent-messages/run.py \
    --agent-bench target/release/examples/agent_bench --out /tmp/agent-messages
```

## Результат

Див. `results/20260927/report.md` (main `2f2611b9` + ця гілка; i5-6400; Guix
за `channels.scm`). Висновки нижче — з цього прогону.

1. **Один процес на повідомлення — SENS у ~60 разів легший.** Старт SENS
   ≈1,5 млн інструкцій, CPython ≈94 млн. Для агента, що запускає окремий процес
   на кожен виклик інструмента, це вирішальне.
2. **У довгоживучій сесії SENS fasl швидший за текст Python (×4) і за
   JSON-інтерпретатор на Python (×1,3), але повільніший за готовий байткод
   CPython (`marshal`) приблизно в 3,7 раза.** Декодування fasl і marshal
   однакове (~10 тис. інструкцій); різницю дає виконання: ~48 тис. проти
   ~5,5 тис. — дерево з іменами проти байткоду зі слотами.
3. **fasl більший за текст (~154 байти проти ~44), а SENS wire — найменший: ~34
   байти**, менше за англійський текст SENS (44), текст Python (46) і JSON (48),
   у 4,5 раза менше за fasl. Декодування wire коштує стільки ж, як fasl
   (~10,4 тис. проти ~10,0 тис. інструкцій). Місце у fasl забирав формат, а не
   коди СЕНС: заголовок із 32-байтовим хешем, числа як f64 (10 байтів), довжини
   як u32 (5 байтів на список). fasl лишається для кешу ядра (там хеш потрібен).

## Межі

- Програми маленькі й прості; для важких обчислень див. `benchmarks/cross-language`.
- `py-marshal` залежить від версії CPython (байткод непереносний між версіями),
  а fasl SENS — ні; у цьому бенчмарку це не міряється.
- Бібліотека core SENS не завантажується; повідомлення користуються лише
  примітивами мови.
