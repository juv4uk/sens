# Архівація історичної гілки — branch-sweep triage (9 жовтня 2026)

**Статус:** збережено первинні джерела у `main` як неактивні архівні свідчення; **не** відновлено старий процес `branch-sweep`, CI workflow, застарілі семантичні контракти чи інструкції створювати нові гілки.

**Джерело:** `juv4uk/sens`, гілка `agent/chatgpt/sweep-triage-addendum-20261009`, head commit `5dba2ce7cee6f0c6aa272d9cd70a9651605ca825`.

| Історичний шлях | Git blob SHA | Архівний файл у main |
|---|---|---|
| `docs/research/branch-sweep-triage-20261009.md` | `a14d4092f404e9b535c3fee74462c202d32fe7ce` | `branch-sweep-triage-20261009-source.md` |
| `docs/audit/safe-branch-sweep-20261009-triage.tsv` | `daea3d57a929853e04fa4c03838e7494ba0395df` | `safe-branch-sweep-20261009-triage.source.tsv` |
| `.github/workflows/branch-sweep-triage.yml` | `5b4331c20e467930a1c2e74019c45a2168feaf53` | `branch-sweep-triage-workflow-20261009.source.txt` |
| `scripts/triage_branch_sweep.py` | `2c402a8d946eea8a2544781ac09629827bed5088` | `triage_branch_sweep-20261009.source.txt` |
| `tests/test_triage_branch_sweep.py` | `c92e6329f6a209e9ff131437a9c44f1519b60c7b` | `test_triage_branch_sweep-20261009.source.txt` |

Архівні файли мають тотожний вміст до оригінальних Git blobs; перенос виконано без створення нової branch. Відмінність історичного `ahead_by` від нуля не є підставою знову запускати `branch-sweep`: тепер діє власникове правило **main only, no new branches**. Інші дочірні гілки (зокрема `agent/chatgpt/sweep-triage-ledger-20261009`) потребують окремого дедупу — не позначати їх завершеними автоматично.
