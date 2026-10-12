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
