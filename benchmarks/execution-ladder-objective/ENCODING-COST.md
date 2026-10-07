# Encoding-density benchmark

Цей benchmark вимірює, **що саме дає економію** в ladder representation. Для одного й того самого validated corpus порівнюються:

- `canonical_text_bytes` — UTF-8 canonical source;
- `dense_exact_width_bytes` — усі exact-width bits зібрані в один потік;
- `byte_aligned_word_bytes` — кожне D2/D3 слово окремо округлене до байта;
- `fixed_d3_stream_bytes` — наївний слот по 3 біти на кожне слово.

## Запуск

```sh
ART=benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl
python3 benchmarks/execution-ladder-objective/encoding_cost.py "$ART" \
  --out benchmarks/execution-ladder-objective/results/encoding-bounded-d1-d3.json
```

## Межі

`fixed_d3_stream` — контрольна модель щільності, а не новий reader або wire protocol. Вона не доводить сумісність чи семантичну коректність. Єдиним джерелом parity залишається validated L0/L1 artifact.

Цей benchmark вимірює лише encoding density. Він не враховує headers, signatures, runtime, loader, compression, encryption, retries чи канал передачі.
