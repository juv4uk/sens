# SENS Native Machine Benchmark №1

Міряємо реальну роботу, а не проголошуємо перевагу над іншими мовами.

Два різні корпуси — **не порівнювати їхні числа між собою**:

1. **CAR(CONS(2,3)) / CDR(CONS(2,3))**: Lisp-сумісний evaluator проти x86-64 через існуючі Lisp-owned lowering, admission та native-call-u64-raw. Обидві ланки перевіряють незалежні очікувані результати 2 та 3. Якщо native не пройшов фактичне виконання, він має явний BLOCKED та жодного ratio. Це ще не повністю фізична двійкова програма: числа й Lisp-сумісний surface — окремий міграційний борг.
2. **Фізичний T5**: наявні immutable transport-артефакти для D3 CAR/CDR та EQ/COND. Вимірюємо eval_t5_program в одному процесі: фізичний T5 decode, D2 parse, виконання. Незалежні фіксовані очікувані результати перевіряються *до* таймінгів.

Обидві гілки вимірюють один процес, але кожна ітерація виконує parser. Нативна гілка також включає lowering, admission, кодування байтів, executable memory та hardware call; це **не** latency самих CPU-інструкцій. T5 не включає startup чи stdout.

## Команди

    cargo build --locked --release -p sens-host --example native_machine_bench
    target/release/examples/native_machine_bench --reps 15 --warmups 4 > raw.tsv
    python3 benchmarks/native-machine-1/summarize.py raw.tsv --out /tmp/native-machine-1

Стенд працює лише на Linux x86-64. Вихід: raw.tsv, results.json, report.md. GitHub Actions завантажує сирі результати артефактом, не лише підсумки. p50 та p95 — опис вимірювання, а не жорсткі CI-пороги.

## Стан операцій

Доказ фізичного native route наразі обмежений u64 пару; ATOM/EQ/COND не мають підтвердженого окремого нативного виконання в цьому benchmark. Жоден fallback не видається за native. Не робити загальних тверджень про швидкість SENS, FPGA, GPU або C/Rust із цих даних.
