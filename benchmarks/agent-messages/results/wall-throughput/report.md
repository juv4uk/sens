# Agent-messages wall-clock throughput (CPython forms)

**Agent:** grok-xai  
**Harness:** `python3 benchmarks/agent-messages/wall_throughput.py`  
**N / seed / reps:** 1000 / 1 / 7 (median)  
**Host:** connector sandbox (not Guix/Cachegrind machine)

## Results

| form | mode | µs/msg | msg/s (approx) |
|------|------|-------:|---------------:|
| py-src | decode | 23.2 | ~43k |
| py-src | full | 23.2 | ~43k |
| py-json | decode | 2.6 | ~385k |
| py-json | full | 7.9 | ~127k |
| py-marshal | decode | 0.7 | ~1.4M |
| py-marshal | full | 1.3 | ~770k |

## How to read

1. **Wall time ≠ Cachegrind I-refs.** Do not rank against 20260930 instruction table.  
2. Within CPython, **marshal** dominates warm throughput (matches I-ref story directionally).  
3. **py-src** spend is almost all compile; execute delta is noise at this N on this host.  
4. **SENS wire/fasl** still need `agent_bench` + newer rustc features for a paired wall or I-ref number here.

## Pair with size-by-kind

| form | avg bytes (size-by-kind ALL) | warm wall µs/msg |
|------|-----------------------------:|-----------------:|
| py-src | 46.4 | 23.2 |
| py-json | 48.4 | 7.9 |
| py-marshal | 190 | **1.3** |
| sens-wire (published) | **34.3** | (I-ref path) |
