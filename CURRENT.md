# CURRENT — where the truth actually lives

Українською: це єдина точка входу для "що зараз чинне". Якщо будь-який інший документ (включно з архівом, застарілими планами чи старими рев'ю) суперечить джерелам нижче — **джерела нижче перемагають беззастережно**. Ніхто не має права цитувати `docs/archive/**` як специфікацію.

This file exists per [`DOC-AUTHORITY-ARCHIVE`](https://github.com/juv4uk/ecosystem/issues/5): **one active truth, many preserved histories**. Read this first. On any conflict between this file's authority order and anything else — a design doc, a dated report, a plan, an archived file — this order wins unconditionally.

## Authority order (highest wins)

1. **Machine-readable contracts and Canon** — these are executable, not prose:
   - [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp) — the numeric semantic-ID registry; the single source of truth for which spellings (en/uk/sa/sym) mean which semantic identity.
   - `crates/my-lisp/src/eval/canon.rs` / `necessary_forms.rs` — canon() + McCarthy-7 and DEFINE/LAMBDA evaluator meaning, keyed only by numeric semantic ID.
   - [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) — the implementation-independent behavioral contract (the "oracle corpus"); `my-lisp-constitution.lisp` and `tests/fixtures/inventory.lisp` are GENERATED projections over it, never hand-edited.
   - `language-contract.lisp` (this repo), and the sibling repos' own `isa-contract.lisp` (`fpga-lisp`) / `compatibility.lisp` (`cml`) for cross-repo compatibility.
2. **Active ADRs and ratified design decisions** — see [`docs/adr/`](docs/adr) (if present) and any doc explicitly marked ratified/accepted, not proposed.
3. **Active plans** — the plan actually being executed right now:
   - [`docs/POLYGLOT-SEMANTIC-ORCHESTRATOR-IMPLEMENTATION-PLAN.md`](docs/POLYGLOT-SEMANTIC-ORCHESTRATOR-IMPLEMENTATION-PLAN.md) — polyglot foreign-runtime work (Python, C ABI).
   - [`docs/FFI-FOREIGN-C-ABI-DESIGN-2026-09-12.md`](docs/FFI-FOREIGN-C-ABI-DESIGN-2026-09-12.md) — native C ABI track, explicitly separate from the Python track above.
   - [`docs/COMPILER-AUTHORITY-BOUNDARY.md`](docs/COMPILER-AUTHORITY-BOUNDARY.md), [`docs/COMPILER-ORACLE-CORPUS.md`](docs/COMPILER-ORACLE-CORPUS.md), [`docs/COMPILER-IR-V0.md`](docs/COMPILER-IR-V0.md) — compiler roadmap.
   - [`tasks.lisp`](tasks.lisp) — the live, machine-readable task DAG; `(done . nil)` entries are the actual open backlog, `(status . superseded)` entries are explicitly retired (kept for audit trail, never executed).
4. **Standing doctrine** — [`docs/agent-doctrine.md`](docs/agent-doctrine.md), this repo's own [`AGENTS.md`](AGENTS.md), and [`PLAN.md`](PLAN.md) (the active Advice Taker roadmap) / [`STATUS.md`](STATUS.md) (current milestone snapshot) / [`ecosystem-status.md`](ecosystem-status.md) (cross-repo current-state snapshot — the log of *how* things got decided lives in `cml`'s own copy, this one is the derived, current-only view).
5. **Tests and evidence** — `cargo test --workspace`, `--oracle-check`, and CI (`.github/workflows/ci.yml`) prove the current state actually holds; a claim without a passing test or a cited commit is a hypothesis, not a fact (doctrine rule 2, rule 10).

## What is explicitly NOT authoritative

- **`docs/archive/**`** — see [`docs/archive/README.md`](docs/archive/README.md). Superseded designs, completed plans, research spikes, and dated historical reviews/audits/reactions. Non-normative by construction; never cite as a reason for an implementation decision.
- Any dated report, PoC writeup, or "here's what I found" investigation doc not listed above — read it for context if it helps, but if it disagrees with the contracts/Canon/registry/active plan/tests, it is the document that's wrong, not the code.
- A peer agent's claim, a swarm `notify`/`emit` message, or a cross-session report of "X is fixed" — verify against the actual evidence (commit, test, CI run) before treating it as true (doctrine rule 9).

## For a new agent starting cold

1. Read `AGENTS.md` and `docs/agent-doctrine.md` (the fourteen rules).
2. Read `tasks.lisp` for the current open backlog and its dependency structure.
3. Read `lib/surface/semantic-registry.lisp` before assuming any spelling (English or otherwise) has special authority — it does not.
4. Run `cargo test --workspace` and `cargo clippy --workspace --all-targets -- -D warnings` before trusting that "the docs say it works" — doctrine rule 13.
5. If a design question seems already answered by an old document, check whether a newer active plan superseded it before acting on it.
