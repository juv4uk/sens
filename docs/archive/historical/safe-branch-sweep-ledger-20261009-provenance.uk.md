# Історична гілка branch-sweep-ledger — повне архівне збереження diff (2026-10-11)

- Джерело: `juv4uk/sens`, `agent/chatgpt/sweep-triage-ledger-20261009`, snapshot head `21c4f4726c751f7b342d45a0cc4e91bd65fd8189`.
- Ціль: `main`. Збережені файли **архівні, не чинні інструкції**, вони не повертають скасований процес створення `sweep` гілок і не заміняють поточний history census.
- Semantic status: `ARCHIVED-HISTORICAL-SOURCE`, не `MERGED-ACTIVE-CODE`. Результати зведені за донорськими blob SHA. Історичні коміти не переписано.

| Original Git path | Blob SHA | Archived path in main |
|---|---|---|
| `docs/audit/safe-branch-sweep-20261009-triage.tsv` | `0ae931a568c4b34c03133682e4790f659c24463a` | `docs/archive/historical/safe-branch-sweep-ledger-20261009-triage.source.tsv` |
| `docs/merge-audits/safe-branch-sweep-20261009.md` | `c0d29d932cedefb4ddc6c937a58ff5fa4e6b8335` | `docs/archive/historical/safe-branch-sweep-ledger-20261009.source.md` |
| `docs/research/branch-sweep-triage-20261009.md` | `326a8caac9f90e280f9d9fcac387e91394b2ef63` | `docs/archive/historical/branch-sweep-ledger-20261009-triage.source.md` |

Ці три історичні source blobs збережено байт-точно окремими файлами через GitHub Contents API. Унікальні дії/обчислення з цієї гілки не затверджувались. Рішення видалити ref — лише після перевірки всіх унікальних історичних результатів single-writer #5041. Не створювати нових гілок.
