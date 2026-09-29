# Root lifecycle inventory (GitHub issue juv4uk/my-lisp#23)

Перший прохід класифікує кожен файл у корені репозиторію за полями
задачі #23. **Це лише класифікація: у цьому проході нічого не
переміщується й не видаляється**, доки безпечність такого кроку не
доведена окремо.

Метод: `git grep` за кожним ім'ям у `.rs`/`.lisp`/`.md`/`.sh`/`.yml`.
Відсутність збігу означає `unknown`, а не автоматичну непотрібність.
This inventory is classification-first: absence of a textual consumer is
evidence to investigate, never permission to delete an artifact.

## Semantic authority / contract

| File | Owner | Consumers found | Mutability | Lifecycle | Root required? |
|---|---|---|---|---|---|
| `language-contract.lisp` | my-lisp core | Level 1/2 contract, read by `crates/my-lisp` at build/runtime via `include_str!`-style loading and by `docs/cml-semantic-export-v1-design.md`'s producer | Owner-ratified only | active | Yes — root is this ecosystem's established convention for the contract file (`repo.lisp` siblings in cml/my-idea etc. reference it there) |
| `my-lisp-constitution.lisp` | my-lisp core | `crates/my-lisp-cli/tests/constitution_projection.rs`, `crates/my-lisp/tests/mccarthy.rs`, `scripts/build-constitution.lisp`, `tasks.lisp`, 8+ docs | Owner-ratified only | active | Yes — same convention as `language-contract.lisp` |

## Machine entrypoint / build & reproducibility metadata

| File | Owner | Consumers found | Mutability | Lifecycle | Root required? |
|---|---|---|---|---|---|
| `Cargo.toml` / `Cargo.lock` | Rust workspace | cargo itself | Cargo-managed | active | Yes — Cargo convention, non-negotiable |
| `.gitattributes` / `.gitignore` | git tooling | git itself | manual | active | Yes — git convention |
| `guix.scm` / `manifest.scm` / `channels.scm` | reproducibility (Guix) | `scripts/deploy.sh`, `AGENTS.md`, `.agents/skills/guix/SKILL.md`, several docs | manual | active | Yes — Guix convention expects these at repo root |
| `LICENSE` | governance | standard OSS convention, no code consumer needed | owner-set (VOLNOST per `tasks.lisp`'s `VOLNOST-ECOSYSTEM-TRANSITION`) | active | Yes — universal convention |
| `mylisp-cml-export.lisp` | my-lisp (this session, commit 1116836) | cml's `contracts/mylisp-cml-export.lisp` vendors this file's digest; `crates/my-lisp-cli/src/bin/cml-export.rs`'s own tests read it back from the repo root | generated (regenerate via `cargo run --bin cml-export`, do not hand-edit) | active, generated projection | Yes for now — path is hard-coded into the two guarding tests (`committed_artifact_matches_producer_output`); relocating requires updating that test's path first |

## Agent entrypoint / coordination surface

| File | Owner | Consumers found | Mutability | Lifecycle | Root required? |
|---|---|---|---|---|---|
| `AGENTS.md` | ecosystem convention | read by every agent session entering the repo (root discovery convention across all sibling repos) | living document | active | Yes — root is the universal cross-tool discovery convention (Claude Code, Codex, OpenCode all check here first) |
| `repo.lisp` | Swarm Contract v0.1 | scope/authority declaration, referenced by swarm dashboard tooling per `my-idea`'s parallel `repo.lisp` | owner/lead-set | active | Yes — same discovery convention as `AGENTS.md` |
| `NOTE-FOR-CODEX.md`, `NOTE-FOR-SAKSHI.md`, `NOTE-FOR-SWARM-NODE-AGENT.md`, `NOTE-FROM-OPENCODE.md` | individual agent-to-agent mailbox notes, each self-dated (2026-08-11 through 2026-08-23) | no code consumer; consumed by the *named* agent reading the file directly, per each note's own stated delivery mechanism ("this file is how they reach you") | append-or-reply-in-place, per convention stated in `NOTE-FOR-CODEX.md` | **transitional** — each note is scoped to a specific historical exchange between two named agents; none reference an ongoing/repeating protocol | Root was required *at the time* for cross-tool discoverability (no shared inbox existed then). Worth asking the owner whether these are now safe to archive to e.g. `docs/agent-notes/` now that this session's swarm has richer messaging (`send_message`) — flagging as **archive-candidate pending owner confirmation**, not moving unilaterally |

## Active operational state

| File | Owner | Consumers found | Mutability | Lifecycle | Root required? |
|---|---|---|---|---|---|
| `tasks.lisp` | swarm task coordination | read/written by every swarm agent session (this session included), `docs/*` review docs, `scripts/build-constitution.lisp` | continuously mutated by agents, oracle-checked before each commit | active | Yes — this is the swarm's live coordination surface; every sibling repo's swarm tooling expects it at root by convention |
| `ecosystem-status.md` / `ecosystem-status.lisp` | ecosystem-lead reporting | `AGENTS.md`, `NOTE-FOR-CODEX.md`, `NOTE-FROM-OPENCODE.md`, `docs/cross-substrate-evidence-matrix.md`, `docs/ecosystem-sync.md`, `docs/swarm-coordination.md`, `evidence/README.md`, `knowledge/swarm-no-live-callers-audit.lisp` | updated by ecosystem-lead agent role | active | Yes — same discovery convention |
| `STATUS.md` | quick-glance status | `knowledge/guard-reference.lisp` | manual | active | Not strictly required by any hard-coded path found beyond the one guard-reference cross-reference — low-confidence **possible archive-candidate**, needs the guard-reference author to confirm before moving |

## Active research / proposal

| File | Owner | Consumers found | Mutability | Lifecycle | Root required? |
|---|---|---|---|---|---|
| `memory-layout-contract.lisp` | layout mechanism research / GC-adjacent history | GC/review docs only; 2026-09-29 re-audit found no runtime, CI, or cross-repo machine consumer beyond vendored SENS copies | mechanism/design evidence, not semantic authority | transitional mechanism design | No hard requirement found; keep in root only until #23 chooses a documented relocation |
| `PLAN.md` | roadmap | referenced from `lib.rs` doc comments (TCP library entry, item 21) and multiple docs as the plan-of-record | living document | active | No hard requirement found, but is the established roadmap-of-record; moving needs the doc-comment cross-references in `crates/my-lisp/src/lib.rs` updated first |
| `CLEAN_CODE_PLAN.md` | code-quality roadmap | none found via grep | manual | **unknown** — no consumer found, but per issue's own rule this is not proof of irrelevance; may be read manually by agents/owner without being grepped-for | No requirement found; candidate for relocation to `docs/`, pending confirmation it isn't referenced by convention/memory rather than by text search |
| `typed-buffer-proposal.lisp` | research proposal | `crates/my-lisp/tests/typed_buffer_proposal.rs` — a real, live test | test-referenced | active research/proposal, not yet ratified | Path is load-bearing for its own test; do not move without updating that test |
| `Розуміння Володимира.md` | shared health/wellbeing context note (Vyasa, commit c6fc1d2) | no code consumer; read directly by agents per this session's own standing instruction that this context is now shared swarm-wide | append-friendly, living note | active | No hard path requirement, but per this session's own established practice this is meant to be easily found by any agent entering the repo — moving it need not break anything but should preserve easy discoverability |

## Historical residue / superseded — unknown, not yet proven irrelevant

| File | Owner | Consumers found | Mutability | Lifecycle | Root required? |
|---|---|---|---|---|---|
| `contract-consumers.lisp` | unclear | none found beyond itself | unknown | **unknown** | No requirement found |
| `demo-tasks.lisp` | unclear | none found | unknown | **unknown** | No requirement found |
| `task-demo.lisp` | unclear | none found | unknown | **unknown** | No requirement found |
| `tasks-info.lisp` | unclear | none found | unknown | **unknown** | No requirement found |
| `tasks-summary.lisp`, `tasks-summary2.lisp` | unclear | none found | unknown | **unknown** — the `2` suffix suggests an ad hoc regeneration, not a maintained pair | No requirement found |
| `task-stats.lisp` | unclear | none found | unknown | **unknown** | No requirement found |

Per the issue's own explicit rule, "historical-looking files remain in
place when their lifecycle is `unknown`; uncertainty is not evidence
of obsolescence" — none of these six are proposed for archival or
deletion in this pass. They are flagged as needing an owner (or the
original author, if identifiable from git blame/log) to state their
purpose before any further classification is possible.

## Out of scope for this table: gitignored local build output

`my-lisp-bin` and `span` are present in some working trees' root
(ELF binaries, Guix-linked interpreter paths) but are `.gitignore`d
(`.gitignore:38-39`) and therefore never enter the repository proper —
they are local build artifacts, not root clutter in the sense this
issue is auditing. No action needed.

## Also found: an unrelated, untracked directory (flagged separately, not part of this audit)

A `my-lisp/` directory exists in at least one working tree's repo
root, containing an Obsidian vault (`.obsidian/` config,
`Вітаємо.md`), untracked, with zero git history. This is unrelated to
the tracked root artifacts this issue asks about — investigated and
reported separately this session; not moved or deleted per the
owner's explicit "не видаляй" instruction.

## Next step

This is a first pass, not a final answer for every row — six files
remain genuinely `unknown` and two (`STATUS.md`, `CLEAN_CODE_PLAN.md`)
are low-confidence archive-candidates pending confirmation. Per the
issue's own deliverable ("create a checked-in root lifecycle
inventory/table... do not move files... unless independently proven
safe and trivial"), this table is the deliverable for this pass; no
files have been relocated.
