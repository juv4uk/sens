# Cross-language native baseline

Порівнює одну exact-integer задачу в чотирьох доступних реалізаціях:

- C через GCC `-O2`;
- Rust через `rustc -O`;
- CPython;
- Node.js з `BigInt`.

## Workload

```text
sum(i² for i = 0..n)
```

Для default `n=200000` очікуваний результат однаковий у всіх реалізаціях. Correctness/parity перевіряється **до** вимірювання.

Розділяються:

- source/artifact bytes;
- compile wall time для C/Rust;
- cold process wall time;
- median та p95;
- точність результату.

```bash
python3 benchmarks/cross-language/native-baseline/run.py \
  --n 200000 --reps 9 --warmups 2 --out /tmp/native-baseline
cat /tmp/native-baseline/report.md
```

Це не універсальний рейтинг мов. Це контрольне порівняння конкретних toolchain-ів на одному host і одному workload. Воно також не є SENS runtime evidence: SENS повинен мати окремий current-authority lane з власною семантичною parity-перевіркою.

## Recursive-tree + delivery cost

Друга вісь використовує recursive checksum tree з однаковою глибиною та seed
для всіх чотирьох реалізацій. Окрім cold-process median/p95, вона записує
`source bytes`, `gzip source bytes`, `compiled artifact bytes` і compile time.

```bash
python3 benchmarks/cross-language/native-baseline/tree_run.py \
  --depth 18 --reps 7 --warmups 2 --out /tmp/native-tree
cat /tmp/native-tree/report.md
```

Це дає окремі осі для питання "швидше виконати" та питання "дешевше
передати"; їх не можна зводити в один магічний score.
