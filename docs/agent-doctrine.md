# Agent doctrine — universal rules for every repo in this swarm

Status: proposed 2026-08-18 (owner strategy session), written by
`my-lisp-1`, broadcast to all sibling swarm agents for adoption/critique.
Amended by explicit owner decision 2026-09-13: every task now requires a
live Current Technology Preflight before claim/design/implementation.
Amended 2026-09-28 (#1590): SENS-primary design discipline — identity,
meaning, and execution stay separate; backends are witnesses only.
Amended 2026-09-28: rule 18 — share discoveries (board #1599).
Applies to `my-lisp`/`sens`, `cml`, `fpga-lisp`, `my-idea`, `my-lisp-panini`,
`shiva-sutras`, and any future sibling. Each repo's own `AGENTS.md` stays
authoritative for repo-specific detail; this file is the cross-cutting
constitution none of them should contradict.

## Why this exists

Seven-plus agents working on tightly-coupled repos without shared
discipline produces two failure modes: (1) prose documentation drifts
from the machine-readable contracts it describes (confirmed case,
2026-08-18: this repo's own `AGENTS.md` said "contract currently 1.0"
and described `:9999`-based coordination, while the live contract was
2.0 and coordination had moved to `swarm-node` six days earlier — fixed
in this commit), and (2) agents quietly absorb a neighbor's assumption
as their own fact, so a hypothesis in one repo becomes an unquestioned
premise three repos downstream with no traceable evidence chain.

## The rules

1. **Read the map before the code.** Authoritative contract → current
   task/status → recent evidence → recent commits. Machine-readable
   source of truth (a versioned `.lisp`/`.rkt` file, a fixture, a schema)
   always outranks prose (`AGENTS.md`, `README`, this file included) —
   if they disagree, the contract wins and the prose is a bug.
2. **Never state a claim stronger than its evidence.** Use `confirmed` /
   `partial` / `broken` / `unresolved` / `indeterminate-external`, not
   `works`/`doesn't work`/`proved` without scope.
3. **Don't duplicate a neighbor's semantics.** `my-lisp` owns language
   meaning, `fpga-lisp` owns the hardware mechanism, `cml` owns
   translation, the Pāṇini repos own research evidence, `my-idea` owns
   presentation. If you're tempted to re-derive a neighbor's fact
   locally, ask why you can't reference their contract/fixture/data
   instead.
4. **A neighboring repo is an external authority, not a file to edit.**
   Don't change a neighbor's code to make your own test pass. Produce a
   finding/evidence/request/handoff and let the owning layer decide.
5. **Disagreement is a result, not an emergency.** `Rust != Racket`,
   `source != witness`, `agent A != agent B` — classify first
   (implementation bug / contract bug / underspecified territory / host
   leakage / bad experiment / external failure), then decide whether it
   needs fixing at all.
6. **Break it before you extend it.** Try a counterexample, boundary
   case, resource limit, or differential test against the current
   assumption before adding a feature on top of it.
7. **Minimize change surface.** If one fixture + one law + five lines
   fixes it, that's the fix — not an architecture rewrite, absent a
   demonstrated need for one.
8. **Library before primitive** (esp. `my-lisp`): if it's expressible in
   the host language itself, it belongs in `lib/*.lisp`, not in the Rust/
   Racket/hardware implementation layer.
9. **An event is not evidence.** A swarm `notify`/`emit` message is a
   doorbell, not a fact — verify against `evidence/` or a commit before
   treating "X passed" as true.
10. **Reproducibility is part of the proof.** Durable claims carry commit
    SHA, exact command, environment (Guix channel revision where
    relevant), expected vs. actual.
11. **Correctness before optimization.** Same observable semantics
    first, speed second — true for a JIT, an FPGA opcode, a compiler
    pass, or the swarm protocol itself.
12. **Finish with proof, not a status message.** claim → small
    experiment → result → tests → evidence → commit → durable status
    update → notify peers with a pointer to the evidence, not a
    conclusion.
13. **"Tests pass" is not "done."** Owner review 2026-09-12, after
    ~670 commits in 6 days: architecture/semantic-authority direction
    scored ~9/10, but integration hygiene scored ~7-7.5/10 — three
    separate CI breakages landed back-to-back because `cargo build`/`cargo test`
    passing was treated as sufficient. A vertical slice is not finished until
    ALL of: `cargo clippy --workspace --all-targets -- -D warnings`;
    oracle-check on touched `.lisp`; `cargo xtask verify`; regenerate
    projections; bilingual docs check; ideally watch CI after push.
14. **New complexity must buy Lisp power, or it gets deleted.** Prefer
    `idea -> semantic ID/Lisp form -> backend` over adapter stacks. Ask:
    can this be Lisp? composition? deletion? Only then a new primitive.
15. **Перед будь-якою задачею — живий Current Technology Preflight
    (`TECH-SCAN`).** Після WAKE/RECONCILE, до CLAIM — реальний пошук в
    Інтернеті по темі задачі. Пам'ять моделі не рахується. Evidence:
    date, task/topic, queries/scope, sources, new/relevant, decision
    (adopt|adapt|reject|no-change). Без доступу — `blocked-current-tech`.
16. **Асиметричний semantic firewall (#1347): Rust може рости, Lisp не
    копіює Rust як істину.** Заборонений напрямок
    `Rust/host/backend semantics -> Lisp language authority`.
17. **SENS-primary (#1590/#3020): ідентичність → значення → виконання.**
    Machine-readable: `knowledge/sens-primary.lisp`. Канонічна
    ідентичність SENS — це **точний домен + точні біти + закон домену**;
    ширина є частиною identity. Немає універсального 8-бітного
    функціонального простору і немає semantic fallback через
    Sens8/Sid8/u8. `D1:1`, `D2:01`, `D3:001` і `D4:0001` —
    різні exact-width identities, навіть якщо host/container може
    фізично зберігати їх у ширшому слові. SENS не є текстом і не є
    «скомпільованим binary executable»: біти є канонічною семантичною
    identity, а executable/object/FASL/byte container — лише механізм.
    Історичні та людські назви — surface/projection; вони генеруються з
    двійкової authority і не можуть відновлювати її у зворотному
    напрямку. Backend — свідок. Не створюй текстовий, byte-width або
    opcode-сурогат SENS у ядрі. Перед зміною спочатку класифікуй шар:
    **identity / law / source structure / storage container / transport /
    execution mechanism / human projection**. Перед зміною: *«Як би це
    виглядало, якби SENS був первинним з 1958?»*
18. **Ділися відкриттями з роєм (discovery board).** Finding, що змінює
    поведінку інших агентів (M8 fallout, surface/binding колізія,
    transport, bench gap, island admission), **не** лишається лише в
    локальній пам'яті чи закритому PR-коментарі. Запиши в
    `knowledge/agent-discoveries.lisp` і/або коментар на issue **#1599**
    у форматі: `kind` / `claim` / `evidence` (PR·SHA·path) / `status`
    (`confirmed`|`partial`|`hypothesis`) / `action` для інших. Перед
    CLAIM — прочитай hot-facts у цьому файлі та свіжі коментарі
    #1590/#1599. HANDOFF = pointer на evidence + discovery, не «готово»
    без сліду.

   **English auxiliary (18):** Share discoveries that affect peers. Write
   to `knowledge/agent-discoveries.lisp` and/or issue #1599. Read the
   board before claiming work. Handoff points to evidence, not opinion.

## Rule 0 for coordination specifically

**Verify the swarm protocol before joining it.** Don't trust a cached
`AGENTS.md` claim about which port/process coordination runs on — read
the current `docs/swarm-mesh-v2.md` and confirm live state before acting.

## Wake-up sequence (mandatory before task work)

```
PHASE 0 — WAKE       read AGENTS.md, machine contracts, tasks, evidence
PHASE 1 — RECONCILE  prose vs machine; read knowledge/agent-discoveries.lisp + #1599 (rule 18)
PHASE 2 — TECH-SCAN  live Internet scan (rule 15)
PHASE 3 — CLAIM      one bounded task
PHASE 4 — ATTACK     falsify assumptions
PHASE 5 — IMPLEMENT  minimum change
PHASE 6 — VERIFY     local + conformance
PHASE 7 — RECORD     evidence + commit
PHASE 8 — HANDOFF    pointer to evidence and discovery if peers need it (rule 18)
```

## Subagents: independent sensors, not extra hands

Report `finding / evidence / confidence / unknowns / next discriminating test`,
not a decision. Don't bias a verifier with your preferred answer.

## One shared experiment beats many local ones

Prefer a single small change independently checkable by a neighbor over
a larger change only checkable by you.
