# Batch amortization benchmark

Цей benchmark відповідає на практичне питання: **чи окупається fixed metadata overhead, якщо передавати не одну, а багато програм?**

Для детермінованих префіксів одного validated corpus порівнюються:

- canonical text bytes;
- dense semantic payload bytes;
- framed semantic package bytes із header, artifact digest, case IDs, observable digests, exact widths і frame lengths.

Запускаються batch sizes `1, 2, 4, 8, 16, N`, де `N` — кількість cases у corpus-і. Порядок — стабільне сортування за `case_id`.

## Запуск

```sh
ART=benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl
python3 benchmarks/execution-ladder-objective/batch_amortization.py "$ART" \
  --out benchmarks/execution-ladder-objective/results/batch-bounded-d1-d3.json
```

## Межі

Це вимірювання конкретної research-моделі framed package. Воно не є законом для будь-якого wire format: production protocol може мати інший header, dictionary, compression, signatures або shared metadata.

`framed_minus_text_bytes > 0` означає лише, що **ця доказова упаковка** більша за text для відповідного batch. Це не означає, що semantic transport загалом невигідний.
