# T01 C/JavaScript/SENS: transcript-derived physical triad archive

**Status: EXPLORATORY_ONLY / NO_INFERENCE / ENERGY_NOT_MEASURED.** This directory preserves *visible TSV rows from a real GitHub Actions job log* prior to the 3-day artifact expiration; it is NOT a byte-for-byte copy of the separate 32-file Actions ZIP.

## Original physical provenance

- Repository: `juv4uk/sens`; [run 40730987210, job 122966914730](https://github.com/juv4uk/sens/actions/runs/40730987210/job/122966914730) — **completed SUCCESS**.
- Workflow PR HEAD: `d5ef7c0938abeb0a4af59b1af221d2e812af0b1f`. Actual `git rev-parse HEAD` inside runner: `6a27d38494a76eb03840e0110a76b1712ff94546` (GitHub PR synthetic merge ref). Do **not** conflate these revisions.
- Original [artifact #12835002526](https://github.com/juv4uk/sens/actions/runs/40730987210/artifacts/12835002526): `t01-triad-40730987210`, 32 files, original ZIP SHA-256 `6b6f7733340d8f054e356a6a6bed74dc81520cdaed94680f1178665e30968dc6`, retention 3 days (reported by upload-artifact action). **Neither ZIP nor per-process stdout/time files were downloaded or reproduced here.**
- Files here: `environment.log-transcribed.tsv` = exact visible lines 638–650 and `samples.log-transcribed.tsv` = lines 651–660 of the original job log, preserving tabs and a terminal LF. Independent pinned SHA-256 of these *transcriptions*, not of original ZIP:
  - environment: `d81f733b4bb200d162eef6eb004b4fce086e2f4654b8dcec8cfe59d173b6795f`
  - samples: `f3c37fc90af183c837f861cbe50cb7e02ffceeb71c975d0a9d76f6144ede0980`
- Runner metadata *as physically printed*: Linux `7.0.0-1017-azure`, Intel Xeon 6973P-C, `sens 0.42.3`, Node `v22.23.4`, GCC `13.3.0`. Three balanced process rounds for frozen **Fibonacci(12) → 144**, C `-O2`, SENS Rust debug, compilation and Zig/T5M mint outside timing.
- Nine output-admitted child processes (stdout matched `144\n` with `cmp` and exit 0): C wall `0.00/0.00/0.00`, JS `0.10/0.02/0.02`, SENS `0.01/0.01/0.01` s. Peak child RSS available per row in KiB. All from **ONE shared GitHub-hosted job**, not independent sessions.
- **Important negative result:** C wall `0.00` is censored by GNU time `%e` centisecond reporting; it **does not** mean zero execution time and cannot justify any finite language speed ratio or ranking. The already merged `benchmarks/language-energy-study/t01_clock_floor.py` rejects inferential admission. Short `n=12` is a *verification-size* experiment, not frozen `n=24` MEASURE-size comparison.

## Offline exact evidence verification

```sh
python3 -m unittest -v benchmarks/language-energy-study/test_t01_triad_archive.py
python3 benchmarks/language-energy-study/t01_clock_floor.py \
  --samples artifact/energy-study/observations/t01-triad/samples.log-transcribed.tsv \
  --out /tmp/t01-triad-clock-audit.json
```

The unit test requires exact SHA-256 for both transcript files, checks the physical environment, the 9-row balanced output/exit/RSS format and verifies that **no speed ratio, confidence interval, physical energy or independence claim** is accepted. A synthetic mutation rejected by this test is a software test, not a new measurement.

## Scientific limits and rationale

The frozen task corpus and the prospective plan in `docs/research/energy-study/preregistration.md` forbid retrospective confirmatory admission and require multiple physical sessions and precisely matched functional work. Kalibera & Jones (2013, ISMM, abstract at https://kar.kent.ac.uk/33611/) emphasizes uncertainty and repetition across experimental levels. Pereira et al. (SLE 2017, https://doi.org/10.1145/3136014.3136031) distinguishes energy/time/memory. Wilkinson et al. (2016 FAIR, https://doi.org/10.1038/sdata.2016.18) motivates durable, traceable raw provenance. Green Software Foundation (https://greensoftware.foundation/standards/sci/) requires an explicit functional unit; **no energy sensor, joules, carbon intensity or embodied-emissions measurement** exists here, so SCI cannot be computed. These decisions use the accessible abstract/spec sections, not a claim to have read the full manuscripts.

**No SENS semantic law is established by this archive**: SENS laws remain dependent on native positive/negative witnesses.
