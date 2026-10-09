# Current physical SENS — first in-process benchmark evidence

Immutable evidence for **2026-10-09**; this is not a new language law.

- Commit: [`84f3e96814e9e4d481252c65ea0ea031991ce411`](https://github.com/juv4uk/sens/commit/84f3e96814e9e4d481252c65ea0ea031991ce411)
- GitHub-hosted workflow: [#37975504242 (success)](https://github.com/juv4uk/sens/actions/runs/37975504242)
- Raw trial artifacts: [sens-physical-runtime-37975504242-1](https://github.com/juv4uk/sens/actions/runs/37975504242) (retention-limited; this table is permanent).
- Build: `cargo build --locked --release -p sens-cli --bin sens --bin sens-trit` and `cargo build --locked --release -p sens --example physical_sens_hot_bench`
- 11 independent samples per phase, single process, work budget 65,536 forms; startup **not included**.

| Forms | Phase | p50 ns/call | p95 ns/call | Forms/s at p50 |
|---:|---|---:|---:|---:|
| 1 | t5_open_d2 | 1,121 | 1,219 | 892,061 |
| 1 | d2_parse | 325 | 370 | 3,076,923 |
| 1 | eval_from_ast | 178 | 180 | 5,617,978 |
| 1 | eval_lowered | 90 | 92 | 11,111,111 |
| 16 | t5_open_d2 | 15,202 | 15,806 | 1,052,493 |
| 16 | d2_parse | 4,247 | 4,268 | 3,767,365 |
| 16 | eval_from_ast | 2,032 | 2,048 | 7,874,016 |
| 16 | eval_lowered | 781 | 805 | 20,486,556 |
| 128 | t5_open_d2 | 117,844 | 121,119 | 1,086,182 |
| 128 | d2_parse | 36,435 | 40,608 | 3,513,106 |
| 128 | eval_from_ast | 16,720 | 17,114 | 7,655,502 |
| 128 | eval_lowered | 5,855 | 5,911 | 21,861,657 |
| 1024 | t5_open_d2 | 1,141,648 | 1,143,849 | 896,949 |
| 1024 | d2_parse | 447,294 | 451,882 | 2,289,322 |
| 1024 | eval_from_ast | 127,100 | 129,096 | 8,056,648 |
| 1024 | eval_lowered | 47,514 | 47,643 | 21,551,543 |

## Interpretation limits

- `t5_open_d2` opens physically packed T5 and validates structural D2.
- `d2_parse` parses already rendered binary source (separate pipeline stage, not additional cost inferred by subtraction).
- `eval_from_ast` includes lowering from parsed expressions; `eval_lowered` runs an already-lowered program in a reused session.
- All forms are bounded D3 QUOTE/empty; this measures hot dispatch, not recursion, exact-rational arithmetic, GC, call-heavy code or native machine execution.
- Shared GitHub runners can vary between runs. Within-run independent phase measurements are observational, not proof of causal speedup.
- Lowered SENS throughput must not be presented as a whole-language comparison to Python, C, Rust, Chez or other VMs.

## Reproduce

```bash
cargo build --locked --release -p sens --example physical_sens_hot_bench
python3 benchmarks/physical-sens-runtime/hot.py --binary target/release/examples/physical_sens_hot_bench --out /tmp/sens-hot --samples 11 --work-budget 65536
```
