# Delivery-cost benchmark

`delivery_cost.py` розширює structural benchmark і порівнює чотири моделі для **того самого validated corpus**:

1. canonical text UTF-8;
2. dense semantic payload — лише bit payload;
3. framed semantic package — research-format header, artifact digest, case IDs, observable digests, exact word widths і payload;
4. self-contained package — framed package плюс фактичний файл runtime, якщо його передати через `--runtime`.

## Запуск

```sh
ART=benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl
python3 benchmarks/execution-ladder-objective/delivery_cost.py "$ART" \
  --out benchmarks/execution-ladder-objective/results/delivery-bounded-d1-d3.json
```

Якщо потрібно побачити ціну конкретного runtime:

```sh
python3 benchmarks/execution-ladder-objective/delivery_cost.py "$ART" \
  --runtime target/release/examples/ci_bench
```

`--runtime` нічого не вигадує: вимірюється фактичний розмір переданого файла.

## Межі

Framed package є **дослідницькою моделлю**, не production network protocol. У ньому немає compression, encryption, signature, channel coding, retries, loader, dependency closure або OS image. Тому він не доводить, що packed delivery завжди дешевша за executable binary.

Коректний висновок має форму:

> Для конкретного artifact-а і явно заданої моделі overhead можна порівняти structural bytes. Загальний binary-vs-text verdict потребує окремо зафіксованого runtime, loader і transport contract.
