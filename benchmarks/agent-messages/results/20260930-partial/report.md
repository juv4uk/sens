# Agent messages — partial remeasure 2026-09-30

**Issue:** #1845  
**SHA target:** main @ `c63a7b70` (not a full SENS binary run)  
**Host:** connector sandbox (Linux), Python 3.12.3, Cachegrind  
**N / seed:** 1000 / 1 (same generator as `run.py`)

## Що виміряно тут

| шар | статус |
|-----|--------|
| payload size (text / marshal / json) | ✅ |
| CPython decode+full Cachegrind | ✅ |
| sens-fasl / sens-wire / agent_bench | ❌ blocker — немає release `agent_bench` + full crate build у цій сесії |

Baseline з заліза власника лишається авторитетним для SENS binary:  
`results/20260927/report.md`.

## Payload size (байт / повідомлення, без length-prefix)

| форма | 20260927 (i5-6400) | 20260930 (цей host) |
|-------|-------------------:|--------------------:|
| sens-en | 44.4 | 44.4 |
| sens-text (8×0/1 digits) | — | 69.1 |
| py-src | 46.4 | 46.4 |
| py-marshal | 195.7 | 189.9 |
| py-json | 48.4 | 48.4 |
| **sens-wire** | **34.3** | *(потрібен agent_bench encode)* |
| sens-fasl | 154.1 | *(потрібен agent_bench encode)* |

Розміри текстових форм детерміновані генератором — збіг із baseline очікуваний.

## CPython Cachegrind на цьому host (медіана 2 повторів)

| форма | base | decode | full | (full−base)/N |
|-------|-----:|-------:|-----:|--------------:|
| py-src | 75 934 934 | 272 613 398 | 278 252 176 | ~202 k |
| py-marshal | 76 043 754 | 85 031 258 | 90 101 931 | ~14.1k |
| py-json | 75 946 262 | 100 785 590 | 146 225 959 | ~70.3k |

Порівняно з 20260927 (94M base, py-src ~241k/msg): **порядок той самий**, абсолютні I-refs інші (інший CPU/образ). Не змішувати абсолютні числа між машинами.

## Висновки для #1845 (без прикрас)

1. **Wire лишається найкращим кандидатом на agent envelope за розміром** (34 B у baseline) — менший за JSON/py-src/sens-en.
2. **Warm CPython:** marshal ≪ json ≪ src — як у baseline; SENS fasl/wire (~58k у baseline) між json і src, програє marshal.
3. **Cold start** у baseline (~1.5M SENS vs ~94M CPython) тут для SENS не переміряний; для Python base ~76M на цьому host.
4. **Наступний обов’язковий крок:** повний `run.py` з `agent_bench` на Guix/self-hosted → `results/YYYYMMDD/`.

## Команда для повного прогону

```sh
cargo build --release -p sens --example agent_bench
python3 benchmarks/agent-messages/run.py \
  --agent-bench target/release/examples/agent_bench \
  --out benchmarks/agent-messages/results/YYYYMMDD
```
