[Reading 41 lines from start (total: 41 lines, 0 remaining)]

# #2209 D3/D4 dispatch benchmark

- calls/workload: 200,000
- repetitions: 3
- compiler: gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- valgrind: valgrind-3.22.0
- cpu: AMD EPYC 9V74 80-Core Processor
- git: e640e256b4dfc40c6517baa3118670bf11666a44

Parity first:
~~~text
parity	flat	selectors=6	mismatches=0
parity	prefix	selectors=6	mismatches=0
parity	direct	selectors=6	mismatches=0
~~~

| workload | candidate | I refs/call | branches/call | lookups/call | bits/call | gens/call | prepared bytes |
|---|---|---:|---:|---:|---:|---:|---:|
| repeat-d3 | u8-flat-ready | 21.000 | 4.000 | 1.000 | 0.000 | 0.000 | 768 |
| repeat-d3 | d3d4-prefix-ready | 12.000 | 3.000 | 0.000 | 3.000 | 0.000 | 0 |
| repeat-d3 | direct-static | 8.000 | 2.000 | 0.000 | 0.000 | 0.000 | 0 |
| random-d3 | u8-flat-ready | 21.000 | 4.000 | 1.000 | 0.000 | 0.000 | 768 |
| random-d3 | d3d4-prefix-ready | 12.501 | 3.501 | 0.000 | 3.000 | 0.000 | 0 |
| random-d3 | direct-dynamic | 23.001 | 4.000 | 0.000 | 0.000 | 0.000 | 0 |
| repeat-d4 | u8-flat-ready | 28.000 | 5.000 | 1.000 | 0.000 | 0.000 | 768 |
| repeat-d4 | d3d4-prefix-ready | 31.001 | 4.000 | 0.000 | 4.000 | 1.000 | 0 |
| repeat-d4 | direct-static | 11.001 | 3.000 | 0.000 | 0.000 | 0.000 | 0 |
| random-d4 | u8-flat-ready | 28.000 | 5.000 | 1.000 | 0.000 | 0.000 | 768 |
| random-d4 | d3d4-prefix-ready | 31.001 | 4.000 | 0.000 | 4.000 | 1.000 | 0 |
| random-d4 | direct-dynamic | 26.001 | 5.000 | 0.000 | 0.000 | 0.000 | 0 |
| mixed | u8-flat-ready | 25.656 | 4.665 | 1.000 | 0.000 | 0.000 | 768 |
| mixed | d3d4-prefix-ready | 25.317 | 6.164 | 0.000 | 3.665 | 0.665 | 0 |
| mixed | direct-dynamic | 24.996 | 4.665 | 0.000 | 0.000 | 0.000 | 0 |

Interpretation boundary:
- u8-flat-ready is a favorable 256-slot mechanical baseline, not a claim that the historical Function8 table contained a symmetric row for every D4 selector.
- d3d4-prefix-ready uses the ratified 101/110 roots and one D4 suffix bit; no descendant row lookup.
- direct-static is used only for repeated fixed call sites and is the compile-away lower-bound lane.
- direct-dynamic remains a switch-based control for random/mixed streams; it is not a compiled lower bound.
- identity parsing/framing is intentionally excluded; #1993 owns framing cost.


[executed on device: desktop (4fe47fce-cddf-44b3-9f53-0350f286048d)]