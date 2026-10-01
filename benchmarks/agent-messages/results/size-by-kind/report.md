# Agent-messages size by kind

**Agent:** grok-xai  
**Harness:** `python3 benchmarks/agent-messages/size_by_kind.py`  
**Corpus:** N=1000, seed=1 (same generator as `run.py`)  
**Host:** connector sandbox; pure Python size only (~50 ms)

## Measured average bytes / message

| kind | n | sens-en | sens SID-text | py-src | py-json | py-marshal |
|------|--:|--------:|--------------:|-------:|--------:|-----------:|
| expr | 200 | 19.5 | 41.2 | 29.5 | 25.7 | 103.0 |
| if-eq | 200 | 45.7 | 77.8 | 47.7 | 43.3 | 142.2 |
| let | 200 | 39.8 | 62.6 | 49.8 | 54.9 | 259.1 |
| nth | 200 | 38.9 | 55.8 | 30.7 | 24.2 | 142.4 |
| sum | 200 | 78.2 | 108.2 | 74.2 | 94.2 | 302.9 |
| **ALL** | 1000 | **44.4** | **69.1** | **46.4** | **48.4** | **189.9** |

## Published binary wire (full harness, not re-run here)

From `results/20260930` (Cachegrind host):

| form | avg bytes | warm I-ref/msg |
|------|----------:|---------------:|
| **sens-wire** | **34.3** | 55 848 |
| sens-fasl | 154.1 | 53 438 |
| sens-en | 44.4 | 144 170 |
| py-src | 46.4 | 202 302 |
| py-marshal | 195.9 | 14 003 |

## Takeaway

1. **Size niche:** binary **wire (34 B)** beats every text/JSON/marshal form in the published full run; SID-as-text is *worse* than English surface — packaging matters.  
2. **Kind skew:** `sum` / recursion-shaped messages dominate text size; `expr` stays tiny.  
3. **Warm execute:** marshal still wins I-refs; SENS wins **cold start** and **wire size** (see main README).

Do not collapse size + warm + cold into one slogan.
