# Execution ladder objective benchmark

Цей benchmark перевіряє вузьку, вимірювану гіпотезу:

> Для того самого валідованого canonical program exact-width ladder може мати малу структурну ціну передачі.

Він **не** стверджує, що програма швидша, безпечніша або придатна для довільного мережевого каналу. Він рахує лише:

- кількість semantic bits у canonical source words;
- щільно упакований lower bound у байтах;
- розмір canonical textual source у UTF-8;
- текстовий overhead від пробілів і розділювачів;
- parity L0 oracle ↔ L1 exact-width round-trip.

Correctness перевіряється першою. Якщо L1 не має `PASS` або його observable digest не дорівнює L0 oracle digest, benchmark завершується помилкою і не видає size ratio.

## Запуск

Із кореня `sens`:

```sh
python3 benchmarks/execution-ladder-conformance/validate.py \
  benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl

python3 benchmarks/execution-ladder-objective/run.py \
  benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl \
  --out benchmarks/execution-ladder-objective/results/bounded-d1-d3.json
```

Щоб перевірити відтворюваність:

```sh
python3 benchmarks/execution-ladder-objective/run.py \
  benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl \
  --out /tmp/ladder-a.json
python3 benchmarks/execution-ladder-objective/run.py \
  benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl \
  --out /tmp/ladder-b.json
cmp /tmp/ladder-a.json /tmp/ladder-b.json
```

## Межі

`dense_packed_bytes_lower_bound` — це не розмір готового пакета. Він не враховує framing, metadata, integrity tag, compression, encryption, retransmission або channel coding. Це structural lower bound для порівняння представлень.

Benchmark не вимірює wall-clock latency і не робить висновків про semantic equivalence за межами проваленого/пройденого artifact-а. Для D4–D8 потрібні окремі валідовані artifacts; D1–D3 bounded result не можна автоматично розширювати до всієї ladder.
