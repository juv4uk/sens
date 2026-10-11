# Physical SENS: in-process phase evidence

This is an **extension of the existing physical T5 performance stand**, not a
new language implementation, codec, or replacement for the one-shot benchmark.

Reproduce, after building the existing release CLIs:

```sh
cargo build --locked --release -p sens-cli --bin sens --bin sens-trit
cargo build --locked --release -p sens --example physical_t5_phase_probe
python3 -m unittest discover -s tests -p 'test_physical_t5_inprocess_protocol.py' -v
python3 benchmarks/byte-pack/physical_phase.py \
  --helper target/release/examples/physical_t5_phase_probe \
  --sens target/release/sens --trit target/release/sens-trit \
  --out /tmp/sens-inprocess --warmup 3 --reps 11 --inner 200
```

## Evidence admission

Before measuring, physical `.sens` bytes are decoded as typed D1–D9 words,
round-tripped to **the same packed bytes**, parsed by the real D2 reader, and
evaluated by the existing capability-free SENS evaluator. Python separately
requires **byte-identical stdout from both production physical entry points**
(`sens FILE.sens` and `sens-trit eval FILE.sens`). Their result must match
the Rust in-process oracle plus one final LF. No text-to-semantic shortcut,
name-based dispatch or historical-language equivalence is assumed.

## Timed phases (all in the same, already-running process)

| Lane | Work measured | Excluded |
|---|---|---|
| `session` | Create capability-free `Session` | Program |
| `decode_t5` | Packed physical bytes → typed exact-domain words | File I/O, D2, evaluation |
| `parse_d2` | Typed words → D2 AST | Decode, evaluation |
| `eval_hot` | Repeated prepared AST in one persistent Session | Startup, session setup, decode/parse |
| `eval_fresh` | New Session + execute prepared AST | Decode/parse |
| `full_in_memory` | Decode + D2 + fresh Session + eval | Process start, disk I/O |

Each sample measures a batch of `--inner` operations using Rust `Instant`.
The probe cycles phase order, warms batches before recording, and proves the
semantic result after every recorded batch. Evidence contains **raw integer
nanoseconds**, batch sizes and per-operation medians / nearest-rank p95.
The entire bench is fail-closed on missing or duplicate phase samples,
nondeterministic values, mismatched production stdout or corrupt T5 data.

All phases are **independently measured positive durations**. Never subtract
their medians and call the result “decoder time,” nor interpret
`eval_hot` as end-to-end physical program startup. The pre-existing
`physical_t5.py` continues to report process-including wall time, file I/O,
T5 opening and physical size for the *same two tiny admitted programs*.

No numerical claims from the hosted runner transfer automatically to another
CPU, GPU, FPGA, or a general SENS workload. Full D1–D9 performance comparison
remains blocked where the runtime corpus lacks independently proved semantics.
The benchmarking work changes **no** language law, resident, evaluator or
physical file and does not alter the main-branch single-writer rule.

Evidence files: `inprocess.json`, `inprocess-raw.tsv`, `inprocess.md` inside
the same SHA-bound artifact as the existing `report.json` / `raw.tsv`.
