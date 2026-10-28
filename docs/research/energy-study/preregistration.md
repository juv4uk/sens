# SENS ENERGY-01 · prospective preregistration and admission protocol

> **State: PROSPECTIVE DESIGN, NOT YET FROZEN FOR CONFIRMATORY CLAIMS.**
> Prepared 2026-10-28 for [#6286](https://github.com/juv4uk/sens/issues/6286)
> under [#6285](https://github.com/juv4uk/sens/issues/6285).
> This document is a time-stamped **planning artifact**, not evidence that the
> October 2026 Python/C/Rust pilot was preregistered before its observations.
> No confirmatory results may be labeled “preregistered” until a complete
> independently reviewable, SHA-pinned `FROZEN` manifest has been committed
> before the first qualifying measurement.

## A. Scientific question and exact claim boundary

**RQ1:** For *validated identical work*, how do elapsed time, CPU-package
energy, and peak resident memory vary across programming-language
implementations **on the same fixed physical host**?

**RQ2 (secondary and only if matched across implementations):** How much
does the measured effect differ between fresh-process launch and warm
repetitions, and between problem families? Do not infer a universal
language ranking from one host, input size, or algorithm.

**H0 (per preregistered contrast and metric):** The paired log-ratio has
zero location difference between candidate and named baseline, under the
declared session/block model. **H1:** It differs in either direction.
These are **implementation-specific hypotheses**. Any conclusion about
“the language” outside the sampled implementations/problems is out of scope.

Existing `benchmarks/language-energy-study/` Rust/C/Python byte-copy results,
all results observed *before* the future freeze SHA, nightly REPL timings
and CI experiments are **EXPLORATORY ONLY** and must not enter the
confirmatory inference set, even if their file format matches.

## B. Functional units, eligibility and negative controls

Each future task in [#6287](https://github.com/juv4uk/sens/issues/6287)
has a frozen task ID, input content hash, **counted unit of work**, reference
result hash or documented numerical error tolerance, algorithmic rules,
language-implementation source revision and launch mode. The task set
must consist of **exactly 8 preregistered heterogeneous tasks** for
this first confirmatory study (list/recursion, exact arithmetic,
parsing/text, sorting, allocation/GC, IO, numeric calculation,
persistent/symbolic structures). This list is *classes*, **not yet
frozen concrete programs**. #6287 must pin all eight before any
confirmatory measurements. A language unsupported for a task is marked
`N/A` **before** outcomes and remains visible as a missing cell; no
replacement task after inspecting its performance.

Functional unit `R` = **one verified complete invocation of that fixed
task with its frozen work count**, not one AST node, hardware
instruction, `:завантажити` request, or arbitrary declared “operation”.
For byte-copy pilot `R` = one process executing 8192 copies of a buffer;
this pilot is separate from the future confirmatory task matrix.

Every measured implementation must provide the same output and effective
work (full output comparison or a pinned valid tolerance, explicit count
where relevant) **before** receiving a comparable measured row.
A cross-language parity checker validates **task outputs**, not
SENS language laws. SENS semantic conformance is independently proven
through its existing real REPL/Zig/T5M positive and negative witnesses.

**Predefined falsifiers:** wrong input digest; wrong output; missing
`parity=PASS` evidence; changed work count; inability to execute;
meter not readable; ambiguous RAPL wrap; unrecorded compiler/version
change; CPU mismatch; invalid memory observation. Any such case is
`BLOCKED` for the corresponding conclusion, **not a zero, PASS, or a
reason to delete the task after observing a bad result**.

## C. Contrasts and multiplicity (frozen before measurement)

The prospective first comparison slate is `C/Rust`, `Python/Rust`
and `SENS/Rust` **within each of the 8 tasks**, if eligibility is
proven for both implementations. Baseline means the pinned *Rust
implementation*, never a statement that Rust is a truth oracle.
Compare the same task/input/algorithm and host. Do not compare absent
SENS functionality as a slowdown.

| Endpoint | Units for one `R` | Inference | Physical boundary |
|:--|:--|:--|:--|
| CPU-package energy | J / verified task | **Primary**, only with validated calibrated physical sensor | Whole CPU package, includes idle and other processes; not SENS process J |
| Wall elapsed | ns / verified task | **Primary** | Same bracket around child process; cold or warm reported separately |
| Peak resident memory | KiB / verified task | **Primary** | Peak RSS of process, not sum of peak across children |
| CPU user/system time | s / verified task | Secondary / descriptive | OS accounted child resource usage |
| Startup/compile/JIT/GC | ns by stated phase | Secondary; never silently merged | Distinct mutually documented timing boundaries |

The planned confirmatory family contains **8 × 3 = 24
candidate/baseline contrasts per endpoint, 72 total endpoint claims**,
subject to pre-frozen missing cells. Avoid writing “72 significant
findings”: these are *potential* tests. The multiplicity family is
**all admissible preregistered contrasts × the three primary endpoints**
within the same host and execution mode. Plan: two-sided
familywise Holm correction at `alpha=0.05`. Interval estimates
(paired effect size, 95% uncertainty interval) and **adjusted inference**
must both be reported; a plain uncorrected 95% CI is not itself a
Holm-corrected rejection test. If #6290 cannot validate the method
or provide valid adjusted inference, report descriptive intervals and
`INCONCLUSIVE`, **not significant**. An all-missing energy endpoint
has no energy inference. No selective reclassification of secondary
metrics as primary.

**Practical relevance threshold (descriptive, not a p-value):**
5% relative effect (ratio ≤0.95 or ≥1.05). A merely statistically
detectable sub-5% effect is reported as small. Neither threshold
proves equivalence; equivalence requires a separately preplanned
two-one-sided testing design and sample size.

## D. Execution conditions, randomization and stopping

- **Unit of analysis:** a session on one **physically identified**
  host; measurements inside one session/block are correlated.
  Container restarts, samples or process invocations on the **same
  shared runner** do not become independent machines.
- **Eligibility:** fixed bare-metal host with a verified accessible
  CPU package counter (e.g. Linux RAPL) or a documented calibrated
  wattmeter. Physical machine ID, CPU/microcode, socket count, memory,
  power sensor path, maximum energy range, OS/kernel, CPU affinity,
  governor/turbo, temperature, ambient/idle protocol, dependency
  versions and commit SHAs are pinned in the lock manifest.
- **Balanced execution:** pair order AB/BA alternates within each
  session and task, with candidate/task order shuffled using the
  frozen integer seed. Preserve the generated order in raw records.
  Unmeasured warmups occur *before* measured trials.
- **Levels:** **minimum 4 sessions on at least 2 calendar days,
  4 balanced AB/BA pairs per task/contrast/session**; actual
  confirmatory repetition count is frozen after an **independent
  variance-only pilot**. This is a minimum layout, **not a power
  claim**. Record between-session variance and an a-priori precision
  target of ≤10% relative half-width for each primary time effect;
  if a pre-study estimate cannot support it within declared resource
  budget, mark **underpowered** and do not assert a confirmatory
  claim. Do not choose N after looking at confirmatory effects.
- **Cost cap:** preflight calculates task-bytes × iterations × total
  invocations and the upper wall-time budget; each task invocation
  must stay ≤3 GiB declared physical buffer traffic (when applicable).
  No unbounded automatic CI or paid runners; resource envelope
  approved **before** a run and stored in the manifest.
- **Stop rule:** fixed N, no significance-based early stopping.
  Stop immediately for physical safety or correctness/parity failures
  with reason and keep all raw collected records. Underpowered or
  interrupted studies remain **INCONCLUSIVE**.
- **Failures/exclusions:** logged with original sample ID, cause,
  timestamp and raw logs. Only **predefined invalidity conditions**
  (sensor invalid, failed process, parity failure, unrelated hardware
  outage) can exclude a measurement; never exclude because a time/J
  observation appears too large or changes a ranking. Failed cell
  keeps its place as `BLOCKED` or `NOT_MEASURED`.
- **Phase-specific claims:** compiled and interpreter start costs
  included in cold task if declared; compiler invocation outside
  task unless separately reported, JIT and GC exposed where possible;
  warm measurements require a separately documented in-process
  exercise path and cannot be compared to cold samples as identical.

## E. Energy and carbon attribution

`energy_uj` or calibrated wattmeter readings are *measured quantities*.
Package Joules include background/idle. Report raw sensor start/end,
`max_energy_range_uj`, rollover decision, elapsed bracket, sensor
identity and data-resolution limits. `J/R` is whole-package J per
*verified task invocation*; not isolated application J/R. Idle
subtraction may be published as **exploratory sensitivity only**, never
to replace raw package J.

If powercap is unavailable: `ENERGY_NOT_MEASURED`. No zero energy,
TDP × time proxies, shared-runner “energy league table” or fake
CO₂e. SCI follows `SCI=(E×I+M)/R`, but is **not computed** until
a consistent system boundary plus verified E/I/M inputs are available.

## F. Locking and provenance (prospective registration gate)

A reviewer must lock the companion **JSON manifest** *before* the
first qualifying confirmatory observation. The manifest is not a
second benchmark registry: it is one immutable protocol snapshot
per study version, for use by #6287/#6289/#6290. Run the
local structure checker (research-only, no automatic release gate):

`python3 docs/research/energy-study/check_preregistration.py PATH_TO_MANIFEST.json`

Minimum manifest schema:
- `schema="sens-energy-prereg-v1"`, `state="FROZEN"`,
  ISO-8601 UTC `locked_at_utc` and `first_confirmatory_at_utc`;
  `protocol_sha` and `analysis_sha` of length 40 SHA-1 hex and
  a non-empty `lock_review_url`.
- `host_id`, `host_cpu`, `energy_sensor` (`RAPL_PACKAGE` or
  `CALIBRATED_WATTMETER`), `energy_scope`, `sensor_proof_url`,
  and `max_work_bytes_per_invocation` ≤ 3 GiB.
- `random_seed` integer, ≥4 `sessions`, ≥4 **even**
  `pairs_per_session`, `variance_pilot_sha` (different source
  data from confirmatory observations), `precision_target`=0.10,
  `alpha`=0.05, `multiplicity`=`HOLM_FWER`,
  `analysis_state`=`VALIDATED` only after #6290 actually validates it.
- exactly 8 `tasks`: unique IDs, full lowercase 64-character
  `input_sha256`, integer `verified_units` > 0,
  `reference_output_sha256`, and `implementations` listing
  language+source SHA with Rust baseline and at least one candidate.
- `contrasts` must reference **only frozen task IDs**,
  match the pinned input digest, name candidate + Rust baseline
  both found in the task, and declare `wall_time_ns`,
  `peak_rss_kib` and `energy_uj` where supported.

The checker verifies **structure and contradictions**, never
machine measurement, cryptographic truth of an arbitrary SHA, a
pre-commit historical timeline, semantic correctness or scientific
significance. Recorded locks and physical sensor proofs must still
be independently audited. A complete manifest is **NOT yet present**:
#6287, #6289 and #6290 own its missing facts. In the meantime this
document is a **prospective design draft**, not a completed
preregistration, and the existing pilot remains exploratory.

**Amendments:** append-only `amendments/YYYY-MM-DD.md` with reason,
pre/post observation boundary, affected contrasts, new SHA and
reviewer. New hypotheses after results are *exploratory*, not
retroactively confirmatory. Publish failed/null observations and
all missing cells.

## G. Derived outputs and acceptance of claims

- Raw package-energy and time readings, unit counts, peak RSS,
  ordered AB/BA samples and quality logs for each condition.
- Contrast-level log-ratio, uncertainty interval, corrected
  inference status (if validated), number of **independent sessions**,
  counts of invalid/missing observations, and practical relevance.
- Side-by-side cold and warm results **never pooled** without a
  preregistered mixed model. Between-platform differences descriptive
  unless a multi-host balanced design is separately registered.
- Fail closed: no `READY_FOR_CONFIRMATORY_ANALYSIS` with any missing
  or altered lock field, failed parity, missing energy on energy
  contrast, or observed performance-driven exclusions.
- Independently reproducible material from source/input hashes,
  executable version/compiler flags, sensor metadata and raw JSON/TSV.
  Graphs can be regenerated and show confidence bounds.
- No scientifically justified universal language ranking can follow
  from only these eight tasks / one machine. A failure to reject H0
  does not establish equivalence.

## H. Sources and rationale (read before drafting)

1. Pereira et al., *Energy Efficiency across Programming Languages:
   How Do Energy, Time, and Memory Relate?*, SLE 2017,
   https://doi.org/10.1145/3136014.3136031 —
   establishes multi-task, multi-language energy/time/memory
   comparison; **does not** validate this SENS data.
2. Pereira et al., *Ranking programming languages by energy efficiency*,
   Science of Computer Programming 205 (2021) 102609,
   https://doi.org/10.1016/j.scico.2021.102609 —
   includes systematic measurement and additional validation of
   rankings on implementations from Rosetta Code.
3. Kalibera & Jones, *Rigorous Benchmarking in Reasonable Time*,
   ISMM 2013, https://doi.org/10.1145/2464157.2464160 —
   motivates analysis of uncertainty at build / invocation /
   within-run levels and time-efficient repeat design; our
   existing hierarchical bootstrap is **not their exact estimator**.
4. Green Software Foundation, Software Carbon Intensity specification,
   https://sci.greensoftware.foundation/ —
   defines a carbon functional unit and E/I/M/R accounting; it
   does **not** justify calculating SCI from partial RAPL data.

**Linked tasks:** plan #6286; workloads #6287; physical validation
#6289, #6275–#6276; inference #6290; external replication #6291.
**Release coordination #6183 is unaffected.**
