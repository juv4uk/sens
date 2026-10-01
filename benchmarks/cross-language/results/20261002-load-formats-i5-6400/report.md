# Load formats: SENS FASL vs CPython source vs CPython .pyc

Primary metric: Cachegrind I refs, median repeated runs, process startup subtracted.

> SENS lane is historical Function8 FASL, not current D1-D4 whole-program evidence.

Startup I refs: SENS 1,517,355; CPython 49,876,294.

| workload | SENS FASL | CPython source | CPython .pyc | source/SENS | pyc/SENS | source/pyc |
|---|---:|---:|---:|---:|---:|---:|
| fib | 35,404 | 16,558,116 | 8,562,220 | x467.69 | x241.84 | x1.93 |
| loop | 29,365 | 16,486,801 | 8,573,834 | x561.44 | x291.97 | x1.92 |
| ackermann | 42,632 | 16,639,994 | 8,497,903 | x390.32 | x199.33 | x1.96 |
| closures | 44,473 | 16,791,864 | 8,737,315 | x377.57 | x196.46 | x1.92 |
| evenodd | 41,585 | 16,650,580 | 8,591,932 | x400.40 | x206.61 | x1.94 |

Geomean source/SENS: **x434.55**.
Geomean pyc/SENS: **x224.58**.
Geomean source/pyc: **x1.93**.

## Artifact bytes

| workload | SENS FASL | CPython .py | CPython .pyc |
|---|---:|---:|---:|
| fib | 325 | 232 | 689 |
| loop | 288 | 210 | 661 |
| ackermann | 389 | 255 | 752 |
| closures | 408 | 306 | 977 |
| evenodd | 387 | 273 | 793 |

Interpretation boundary:
- CPython source lane = read UTF-8 + compile().
- CPython .pyc lane = validate magic/header + marshal code object; no import-system/module setup.
- SENS lane = decode prebuilt historical Function8 FASL; encode excluded.
- Fresh D1-D4 comparison is blocked on #1668 and must replace, not relabel, the SENS lane.

