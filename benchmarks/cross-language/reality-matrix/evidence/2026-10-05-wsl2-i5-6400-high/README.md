# Reality Matrix local witness — 2026-10-05

- SENS commit: 9714e8cb714cff7ffc27f37d8a03447d8df094e2
- Contract: 11.6 / current D1-D7
- Host class: WSL2 on i5-6400, 4 logical CPUs visible to WSL
- Load context: high (initial load1=1.25; idle threshold is <1.0 for nproc=4)
- Rust: 10 outer reps x 10000 warm calls
- Wasm: 10 outer reps x 10000 warm calls
- RSS intentionally withheld pending #3698
- Do not compare these absolute times with another machine or an idle-context run.
