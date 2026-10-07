# D10 all-repository donor audit v2

**Authority:** #4049  
**Scope:** all 87 repositories visible in the `juv4uk` owner namespace.

This is a **semantic ownership audit**, not a claim of original authorship and not an admission list.

## Classification

```text
CORE-LANGUAGE-DONOR       1
CORE-HISTORICAL-DONOR    11
BACKEND-OR-MECHANISM     11
PACKAGE-OR-DOMAIN        32
REFERENCE-OR-UPSTREAM    31
REVIEW-REQUIRED           1
---------------------------
TOTAL                    87
```

Only the first two classes may feed direct missing-Core review. Backends feed only #4054/#4036 seam-law factorization. Package/domain repos retain their native semantics. Reference/upstream repos are provenance/comparison only.

Deep README review corrected several misleading name-based assumptions: CML, FPGA Lisp and WSM execution repos explicitly defer language authority to sens; Panini/Panca/Spanda are domain systems; Tauricode/Ecosystem Observer are tooling; several Basalt/Hydra/Maitreya/TH/Chebupelka repositories are upstream/reference corpora.

## Work queues

- #4053 — 11 historical Lisp-family donors.
- #4054 — execution/backend seams only.
- #4036 — minimal Core island bridge semantics.
- #4055 — resolve vault-semantic-mcp scope.

The matrix is machine-readable at `knowledge/d10-owner-repo-donor-matrix-v2.json`.
