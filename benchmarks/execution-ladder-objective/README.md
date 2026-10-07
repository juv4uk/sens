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

## Generation boundary

Current CI regenerates the bounded D1-D3 corpus under **Contract 11.8** from
the checked-out SHA before measuring it. The committed
`execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl` file is an
immutable **Contract 11.6 historical artifact**; it is not the current input.

To validate that historical artifact explicitly:

```sh
python3 benchmarks/execution-ladder-conformance/validate.py \
  --contract 11.6 \
  benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl
```

For fresh/current evidence, use the CI producer or generate a Contract 11.8
artifact with `generate_bounded.py` and pass that artifact to the objective
tools. Do not relabel the committed 11.6 results as current.

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

Benchmark не вимірює wall-clock latency і не робить висновків про semantic equivalence за межами проваленого/пройденого artifact-а. Для D4–D9 потрібні окремі валідовані artifacts; D1–D3 bounded result не можна автоматично розширювати до всієї ladder.
