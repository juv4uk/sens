# ENERGY-02 · T01 independent C workload

This is **one** frozen corpus task, not an additional suite or a claim that C is faster.
The canonical specification remains `../manifest.json` (`T01-symbolic-recursion`).
`TASK_N=12` is the correctness input; `TASK_N=24` is the measurement input.
The algorithm uses two **naive recursive calls** at each `n >= 2`, matching
`corpus/javascript/t01_fib.mjs` and Python's `ref_T01`. Output is exactly one
unsigned integer and a newline; invalid inputs are rejected, never replaced
with a default. The limit `0..32` is a safety budget, not a corpus change.

Compile from repository root, using a standard compiler:

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror \
  benchmarks/language-energy-study/corpus/c/t01_fib.c -o /tmp/sens-t01-c
python3 benchmarks/language-energy-study/parity_check.py \
  --task T01-symbolic-recursion --run /tmp/sens-t01-c
TASK_ID=T01-symbolic-recursion TASK_N=24 /tmp/sens-t01-c
```

For the pinned **verify** input the existing `parity_check.py` sets
`TASK_ID=T01-symbolic-recursion; TASK_N=12` and demands exact stdout parity.
For the **measure** input this binary prints `46368`. These two input sizes
must never be silently interchanged for an energy/time comparison.

Negative controls (must exit nonzero without a successful stdout record):

```sh
TASK_ID=T09-bit-operations TASK_N=12 /tmp/sens-t01-c
TASK_ID=T01-symbolic-recursion TASK_N=oops /tmp/sens-t01-c
TASK_ID=T01-symbolic-recursion TASK_N=33 /tmp/sens-t01-c
```

**Evidence boundary:** correctness parity is a prerequisite, not a time, RSS,
energy, or SENS semantic result. This implementation produces no energy number;
without a physical meter use `ENERGY_NOT_MEASURED`. If timing later occurs,
report build flags, compiler version, exact SHA, separate cold/run phases,
independent sessions and raw samples. RAPL CPU-package energy, if ever
measured, includes system background power and is not process-exclusive.

Methodological provenance: Pereira et al. (2017), DOI
`10.1145/3136014.3136031` and Pereira et al. (2021), DOI
`10.1016/j.scico.2021.102609` (same problem and implementation parity before
ranking); Kalibera & Jones (2013), DOI `10.1145/2464157.2464160`
(repetitions and uncertainty, **not** established here); Wilkinson et al.
(2016), DOI `10.1038/sdata.2016.18` (reproducible metadata/provenance);
Green Software Foundation SCI (ISO/IEC 21031:2024) identifies the functional
unit R, but no SCI/CO2e calculation is justified without E/I/M measurements.
