# ENERGY-02 / T04 · C11 exact parity evidence

Issue #6287 (parent #6285); [CLAIM](https://github.com/juv4uk/sens/issues/6287#issuecomment-6473168104).

## Frozen functional unit

The unchanged corpus/manifest.json (blob 9bdebd688c908a0665847ea7b0421ab20a0c7fa6) defines T04 sorting: generate N unsigned 64-bit LCG words, sort numerically without losing low bits, SHA-256 the comma-separated **unsigned decimal** representation. VERIFY: N=500, seed=7. MEASURE: N=200000, seed=12345. The source limits N to 1,000,000 to cap memory/time.

The C11 source performs real uint64_t wrapping arithmetic, qsort and OpenSSL EVP SHA-256. The digest is a *physical output parity check*, not a definition of SENS language semantics. Neither source nor test changes any shared corpus, REPL, workflow, RAPL or release file.

## Local independent results · 2026-10-28

| Input (N, seed) | Exact observed C stdout digest | Python reference | Node JS |
| --- | --- | --- | --- |
| 1, 0 | 58697eb5920fcb07ce9392429838b23b91544f283b342da296f90c797981721b | MATCH | not tested |
| 101, 2^64-1 | dfe7456c467e27675b1e5232d4567fc80a2ba9c8ccd3587512adb4820d68b220 | MATCH | not tested |
| 500, 7 | 57c115c4025b936b01ed85e4e32d7519b41d7a5c4f197815f3e2e3f896948c32 | MATCH | MATCH |
| 200000, 12345 | 2bc53d1b0a72010352750fbdb094c0064ebedca0dac16210eb333028d0f6c037 | MATCH | MATCH |

- C compile: cc -std=c11 -O2 -Wall -Wextra -Werror t04_sort.c -lcrypto: PASS.
- Targeted unittest: 7 / 7 PASS (including nine invalid variants, missing input, unsigned wrap, repeatability and Node parity).
- Linking proof: nm -D reports qsort, EVP_DigestInit_ex, EVP_DigestUpdate, EVP_DigestFinal_ex. Observable hash over each sorted element prevents wholly eliding the workload; no claim about instruction count.
- OS: Linux 6.18.55 x86_64. GCC Debian 14.2.0, Python 3.13.5, Node 22.16.0, OpenSSL 3.5.5.
- Exact Git blobs confirmed identical to locally compiled/tested copies: t04_sort.c 57599d0552d606dee40fcd0a44c2341d506db375; test_t04_sort.py ecc16f915eecf7f82b63c2671af083ac8e72d386; existing Node baseline 07888827b7319c0dcaca1ad3f98dd3e4c018fba1.
- Container had no GitHub network, so offline unit-test execution used a faithfully transcribed **T04-only subset** of parity_check.py (same frozen ref_T04 algorithm and VERIFY/MEASURE params). Full upstream parity_check.py invocation and PR CI are **NOT_VERIFIED**, to be checked on an actual checkout.
- No time or memory comparative study attempted. **ENERGY_NOT_MEASURED**; no physical power sensor measured. No language rankings, no SCI/CO2e, no claims about RAPL process energy.

## Reproduce in a clean PR checkout

1. Run: python3 -m unittest -v benchmarks/language-energy-study/corpus/c/test_t04_sort.py
2. Compile: cc -std=c11 -O2 -Wall -Wextra -Werror benchmarks/language-energy-study/corpus/c/t04_sort.c -lcrypto -o /tmp/sens-t04-sort
3. Verify: TASK_ID=T04-sorting TASK_N=500 TASK_SEED=7 /tmp/sens-t04-sort
4. Validate upstream: python3 benchmarks/language-energy-study/parity_check.py --task T04-sorting --run /tmp/sens-t04-sort
5. Unavailable Node is reported as SKIP for the JS-only cross-check, not a PASS.

## Scientific decisions and sources

- Pereira et al. 2017 ([DOI](https://doi.org/10.1145/3136014.3136031)) compare language implementations of **the same** defined problems with time, energy and memory as separate outcomes. We require identical workload inputs/output.
- Pereira et al. 2021 ([DOI](https://doi.org/10.1016/j.scico.2021.102609)) emphasize strict benchmark problem contracts. The corpus/manifest.json definition is not modified after observation.
- Kalibera and Jones 2013 ([DOI](https://doi.org/10.1145/2464157.2464160)) emphasize independent repetition and uncertainty. A single parity run is not a performance or variance claim.
- Wilkinson et al. 2016 FAIR ([DOI](https://doi.org/10.1038/sdata.2016.18)): code, algorithms and workflows also need provenance, hence recorded blob hashes, tool versions, commands, observed outputs, and incomplete checks.
- Green Software Foundation SCI ([specification](https://greensoftware.foundation/standards/sci/)) requires explicit functional unit R and measured/modelled energy, carbon intensity I and embodied emissions M for a SCI score; these are unavailable here and no score is claimed.

Next: upstream parity and full unittest on exact PR head; later physical measurement in #6289 and uncertainty in #6290. Neither changes SENS semantics.
