# Benchmark laboratory index

> **GENERATED FILE — DO NOT EDIT BY HAND.**
> Sources: `benchmarks/*/bench.json`.
> Generator: `scripts/benchmark_registry.py`.
> This is discovery metadata only: presence in this table does not grant semantic authority or increase evidence strength.

Bootstrap rule: existing unregistered stands remain explicit backfill debt tracked by #4172. Any newly created benchmark stand must carry `bench.json`; #4171 guards that ratchet.

**Registered stands:** 3

| Stand | Wing | Role | Question | Claim boundary | Witness | Status | Generation | Axis | Reproduce |
|---|---|---|---|---|---|---|---|---|---|
| `d8-zip-unzip-orientation` | D8 orientation research | `RESEARCH`<br>`FALSIFIER` | What orientation, if any, is earned by the historical ZIP/UNZIP pair under the current D8 research laws? | Produces bounded orientation evidence and falsifiers only; it does not admit a D8 coordinate, resident, or callability by itself. | `run.py`<br>`../../docs/research/3710-d8-zip-unzip-orientation.md`<br>`../../docs/research/3710-d8-zip-unzip-orientation.uk.md` | PRODUCT-CANDIDATE-TYPED | unknown | `d8/zip-unzip/orientation` | `python3 benchmarks/d8-zip-unzip-orientation/run.py --out /tmp/d8-zip-unzip-orientation` |
| `execution-ladder-objective` | Execution Ladder | `MEASUREMENT`<br>`CONFORMANCE` | What structural transmission cost does exact-width canonical representation have after L0↔L1 parity is validated? | Measures structural transmission cost for the validated corpus only; it does not establish wall-clock speed, safety, or arbitrary-channel suitability. | `README.md`<br>`run.py`<br>`results/bounded-d1-d3.json` | ACTIVE | unknown | `execution-ladder/structural-transmission-cost` | `python3 benchmarks/execution-ladder-objective/run.py benchmarks/execution-ladder-conformance/artifacts/bounded-d1-d3.jsonl --out /tmp/execution-ladder-objective.json` |
| `store-air-load` | STORE → AIR → LOAD | `MEASUREMENT`<br>`CONFORMANCE`<br>`FALSIFIER` | Can canonical exact-width payload identity be preserved while storage, transport, and load costs are measured as separate physical axes? | Measures STORE/AIR/LOAD accounting and validates exact-width recovery for declared fixtures; transport overhead does not become language semantics. | `README.md`<br>`run.py`<br>`validate.py`<br>`fixtures.json`<br>`schema.json` | ACTIVE | unknown | `store-air-load/physical-separation` | `python3 benchmarks/store-air-load/run.py --out /tmp/store-air-load.jsonl --bitrate-bps 2 && python3 benchmarks/store-air-load/validate.py /tmp/store-air-load.jsonl` |

## Rules

The registry answers *where to look* and *what strength a stand may claim*. Semantic authority remains where the language contract says it lives. A benchmark result is evidence, not a ratification mechanism.

Regenerate or verify from the repository root:

```bash
python3 scripts/benchmark_registry.py
python3 scripts/benchmark_registry.py --check
```

After #4172 backfills the historical laboratory, CI can switch to `--strict`, which rejects every top-level benchmark directory without a manifest rather than only rejecting newly introduced ones.
