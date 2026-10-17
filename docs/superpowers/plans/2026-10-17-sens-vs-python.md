# SENS vs CPython Benchmark Implementation Plan

> **Methodology correction (2026-10-17):** The original implementation below
> timed pre-parsed SENS expressions in a Rust `Session` against CPython
> callables. Those runs are preserved but are **not evidence for physical T5
> programs vs Python source**. The owner rejected that interpretation. The
> corrected, narrower source-to-result pilot and its limits are documented at
> [`physical/runs/20261017T053621Z/README.uk.md`](../../../benchmarks/cross-language/sens-vs-python/physical/runs/20261017T053621Z/README.uk.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
**Historical goal (evaluator benchmark, completed; not a physical T5-vs-Python claim):** Build a reproducible, parity-gated benchmark comparing current SENS source programs with Python source programs on identical workloads and hardware.
**Architecture:** Extend `benchmarks/cross-language/` in a clearly isolated `sens-vs-python/` subtree, preserving its existing historical Function8/FASL harness untouched. Keep workload definitions in paired source files; use a small Rust runner linked to the public `sens` crate to hold one initialized Session and time repeated evaluator calls without process startup; use a Python standard-library runner for the matching functions, raw samples, RSS, and SVG plots. A Python coordinator checks outputs and environment, then writes immutable run artifacts and a Ukrainian report. Unsupported workloads remain explicitly blocked rather than being substituted with legacy execution.
**Tech Stack:** SENS Lisp source, Rust (`sens` crate/public evaluator API), CPython 3.12+, Python standard library, Cargo, Linux `/proc` RSS, JSON, generated SVG.
**Spec:** [2026-10-17-sens-vs-cpython-design.md](../specs/2026-10-17-sens-vs-cpython-design.md)

## Global Constraints

- Work only in `/home/agents/work/sens-vs-python-benchmark`; preserve the unrelated dirty main checkout.
- Put all benchmark implementation files under `benchmarks/cross-language/sens-vs-python/`; do not modify the historical parent `run.py` or overwrite any prior evidence.
- Do not modify SENS runtime semantics, Git branches, CI, or historical benchmark evidence.
- Never use old Function8/FASL or an unrelated host-language substitute as current SENS execution.
- Do not start full suites or long builds without a fresh `wsm-agent bench-ready` and resource-policy check.
- Do not publish a speed winner unless at least three workloads pass semantic parity and all required samples exist.

## Historical evaluator review focus (not applicable to the corrected physical pilot)

- Validate that the timed SENS region measures evaluation of already-parsed calls in one initialized session, while Python likewise excludes import/startup and setup.
- Validate that output parity is a hard prerequisite for timing and that JSON's host-backed parser boundary is reported honestly.
- Validate sample count, nearest-rank percentiles, RSS baseline/peak semantics, and plot generation from raw samples.
- Confirm n-body, Mandelbrot, and regex stay blocked unless current comparable semantics are evidenced.

---

## Task 1: Add benchmark contract and workload inventory

**Files:**
- Add: `benchmarks/cross-language/sens-vs-python/README.md`
- Add: `benchmarks/cross-language/sens-vs-python/workloads.json`
- Add: `benchmarks/cross-language/sens-vs-python/report-template.uk.md`

- [x] **Step 1: Define workload cases and status fields**

Record binary trees N=10, recursive integer workload, JSON parse/serialize, and the existing cross-language Ackermann workload as candidates. For each include stable input, expected output/digest rule, setup boundary, timed operation, parity rule, implementation language boundary, and executable status (`ready`/`blocked`). Mark n-body/Mandelbrot as blocked on comparable current numeric semantics and regex blocked on an evidenced shared regex contract. If JSON is blocked by current exact-callability, use Ackermann as the third executable candidate and retain JSON as an explicit blocker.

- [x] **Step 2: Document execution and interpretation contract**

Document source-vs-source, same-machine/OS, no process startup in timed calls, ten warmups, one hundred samples, nearest-rank p50/p95/p99, p99 limitations at n=100, RSS VmRSS baseline after setup/warmup and VmHWM peak, raw evidence retention, and no winner when fewer than three workloads pass.

- [x] **Step 3: Review contract against the approved spec**

Check every user requirement maps to a recorded field or report item. Do not run workloads in this task.

## Task 2: Implement paired workload source and semantic gates

**Files:**
- Add: `benchmarks/cross-language/sens-vs-python/sens/*.lisp`
- Add: `benchmarks/cross-language/sens-vs-python/python/workloads.py`
- Add: focused tests under `benchmarks/cross-language/sens-vs-python/tests/`

- [x] **Step 1: Write workload fixtures and reference definitions**

Implement only the candidates from Task 1 with fixed inputs. Keep algorithm bodies legible and aligned. Use the current supported SENS source/evaluator path, not compiled historical fixtures. If a workload cannot be expressed or loaded through the current production source path, mark it blocked with the exact error rather than changing the language/runtime.

- [x] **Step 2: Add output normalization and parity checks**

Normalize only representation differences that do not change meaning (for example JSON object key ordering); compare full canonical results, not timing digests alone. Emit explicit PASS/BLOCKED/FAIL per workload before any timing can start.

- [x] **Step 3: Run focused correctness tests**

Verify Python reference outputs against fixed expected results and the pinned binary-trees fixture. Actual SENS↔Python parity and deliberate-mismatch refusal are verified with the Task 3 runner and Task 4 coordinator, because those components are created later. Use the smallest relevant test command here.

## Task 3: Implement persistent SENS evaluator runner

**Files:**
- Add: `benchmarks/cross-language/sens-vs-python/runner/Cargo.toml`
- Add: `benchmarks/cross-language/sens-vs-python/runner/src/main.rs`
- Add: `benchmarks/cross-language/sens-vs-python/runner/tests/` (only if needed)

- [x] **Step 1: Initialize current SENS session once**

Use public `sens::Session`, `sens::load_core_library`, `sens::parse`, and `sens::eval_parsed_expressions` APIs. Load workload definitions before measurement and retain one session. Do not touch the SENS runtime or expose private evaluator internals.

- [x] **Step 2: Implement parity and timing protocol**

Accept a constrained workload/sample request; validate result first, run ten warmups, then collect 100 monotonic-clock durations around evaluation only. Return raw nanosecond samples and canonical output in machine-readable JSON. Record RSS baseline after setup/warmup and peak after measurement, plus compiler/profile/commit metadata.

- [x] **Step 3: Verify runner excludes setup and rejects invalid requests**

Add a tiny smoke invocation proving one session persists across calls and malformed workload/sample requests fail closed. Build only the runner target after fresh resource readiness.

## Task 4: Implement Python runner and coordinator

**Files:**
- Add: `benchmarks/cross-language/sens-vs-python/python/run.py`
- Add: `benchmarks/cross-language/sens-vs-python/python/coordinate.py`
- Add: `benchmarks/cross-language/sens-vs-python/python/tests/`

- [x] **Step 1: Implement Python-side repeated-call runner**

Import workload functions and parse fixed JSON fixture before measurement. Use `time.perf_counter_ns`, ten warmups, 100 samples, and the same output canonicalization and RSS boundaries as the SENS runner. Do not write `.pyc` as benchmark input or include interpreter startup in samples.

- [x] **Step 2: Implement coordinator, guards, and run metadata**

Check CPU/OS/Python/Rust/compiler/build profile, current commit, dirty state, and that both runners target the same host. Refuse to benchmark if parity fails, workload count is insufficient for the headline, sample counts differ, or `bench-ready`/resource checks fail. Store raw output in a timestamped run directory without replacing earlier evidence.

- [x] **Step 3: Test refusal paths without a benchmark run**

Unit-test metadata mismatch, parity failure, invalid sample count, and attempted overwrite handling using fixtures only.

## Task 5: Statistics, visualizations, and report generation

**Files:**
- Add: `benchmarks/cross-language/sens-vs-python/python/report.py`
- Add: `benchmarks/cross-language/sens-vs-python/python/svg.py`
- Add: `benchmarks/cross-language/sens-vs-python/tests/test_report.py`

- [x] **Step 1: Implement deterministic statistics**

Calculate median and p95/p99 using nearest-rank over the raw 100 samples; include raw sample counts, min/max, RSS baseline/peak/delta, and status/reason. Verify with hand-calculated small fixtures.

- [x] **Step 2: Generate plots from raw evidence**

Produce dependency-free SVG boxplots and histograms from the stored samples; axes and labels show units and workload. Plotting must never alter or filter the underlying data.

- [x] **Step 3: Generate Ukrainian results report and limitations**

Report hardware/OS/runtime/build metadata, paired workload methodology, a table, links to raw samples and SVGs, blocked/failed cases, confidence caveats (especially p99 with 100 observations), language/runtime boundary caveats, and no overall winner unless the pass threshold is met.

## Task 6: End-to-end verification and evidence review

**Files:**
- Update: `benchmarks/cross-language/sens-vs-python/README.md`
- Add: `benchmarks/cross-language/sens-vs-python/runs/<run-id>/` (generated evidence; only after explicit preflight)

- [x] **Step 1: Run focused static and correctness checks**

Run formatting/lint and focused parity/report tests. Inspect generated diffs and ensure no historical evidence was replaced.

- [x] **Step 2: Recheck owner-workstation readiness**

Run `wsm-agent bench-ready` and read the resource-policy procedure immediately before the benchmark. If not READY, stop and report the exact blocker; do not bypass limits.

- [x] **Step 3: Run the benchmark only if preflight is READY**

Execute the specified cases on this single host, preserving raw samples. Do not run CI or a full unrelated test suite.

- [x] **Step 4: Independently audit generated claims**

Recompute summary statistics from raw samples, verify parity markers and metadata, inspect each plot, and make report language no stronger than the evidence.

- [x] **Step 5: Report outcome and remaining gaps**

## Task 7: Physical T5 source-to-result pilot and claim correction

**Files:**
- Modify `benchmarks/cross-language/sens-vs-python/README.md` to classify old evaluator runs accurately.
- Modify three prior `runs/*/report.uk.md` files with an explicit evaluator-boundary warning.
- Add `physical/runs/20261017T053621Z/source-copy-raw.json`, `README.uk.md`, `boxplot.svg`, and `histogram.svg`.
- Update this plan and design status to state the 3–5 standard-workload target remains blocked.

- [x] Verify production `sens-trit encode/open/eval` on the tracked D5 `LABEL COPY` physical T5 artifact against an independent Python `.py` source; require exact stdout parity before timing.
- [x] Run 10 warmup pairs and 100 paired fresh-process samples with randomized pair order; retain raw durations and provenance.
- [x] Derive p50/p95/p99, measure one separate process peak RSS per implementation, generate plots, and state that process startup is in the timer.
- [x] Reproduce the exact `sens-trit encode` error for human `fib.call.lisp`; classify the standard suite as `BLOCKED` rather than substituting Rust `Session`.
- [x] Verify runner tests (`test_source_copy.py`: 3 passing) and SVG XML validity; independently recompute aggregates from raw JSON.

**Ruling:** one workload with a verified SENS T5 carrier can support only a narrow source-to-result research observation. Recursion/map fixtures execute physically but lack independently established equivalent Python workload contracts; JSON, n-body, Mandelbrot, and regex remain blocked. No general winner is reported.

Summarize PASS/FAIL/BLOCKED per workload, whether the three-workload threshold passed, key measured values only when actually captured, and all methodological limitations.
