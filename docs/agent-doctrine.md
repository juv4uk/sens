# Agent doctrine — universal rules for every repo in this swarm

Status: proposed 2026-08-18 (owner strategy session), written by
`my-lisp-1`, broadcast to all sibling swarm agents for adoption/critique.
Amended by explicit owner decision 2026-09-13: every task now requires a
live Current Technology Preflight before claim/design/implementation.
Amended 2026-09-28 (#1590): SENS-primary design discipline — identity,
meaning, and execution stay separate; backends are witnesses only.
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

## The fifteen rules

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
    separate CI breakages landed back-to-back (an English-only design
    doc violating the Ukrainian-first bilingual-docs check; a
    generated projection, `my-lisp-constitution.lisp`, left stale after
    editing its source `conformance.lisp`; a clippy lint never checked
    locally before pushing) because `cargo build`/`cargo test` passing
    was treated as sufficient. A vertical slice that touches
    `.lisp`/`.lisp` source, a generated projection, or public surface is
    not finished until ALL of the following are checked, not just
    build+test: `cargo clippy --workspace --all-targets -- -D
    warnings` (the exact CI invocation — plain `cargo clippy
    --workspace` misses `--all-targets` lints in test files);
    `my-lisp --oracle-check` on every touched `.lisp`/`.lisp` file;
    `cargo xtask verify` (the docs/governance/policy checks TEST-
    ARCHITECTURE-1 moved out of `cargo test`, since `cargo test` now
    verifies executable behavior only); regenerating any generated
    projection whose source changed (`my-lisp-constitution.lisp` from
    `conformance.lisp`, `tests/fixtures/inventory.lisp` from the same,
    `lib/surface/uk-inventory.lisp` classification for any newly public
    core definition); `scripts/check-bilingual-docs` on any new/changed
    human-facing doc; and, ideally, `gh run list`/`gh run watch` after
    pushing — a green local run does not guarantee a green CI run
    against a clean checkout. Cheaper to run this checklist once at
    the end of a slice than to spend a separate follow-up commit per
    missed check.
14. **New complexity must buy Lisp power, or it gets deleted.** Owner
    principle 2026-09-12, distilled from this session's own strongest
    changes (the `read-file`/`write-file` migration onto existing raw
    bytes + `lib/utf8.lisp`; the polyglot plan's reuse-first collapse to
    zero core changes; `compiler_corpus_dual_backend.rs`'s rewrite so
    the corpus, not native Rust, is the oracle): a good change looks
    like `idea -> semantic ID/Lisp form -> backend`, not
    `idea -> adapter -> registry copy -> special case -> runtime
    wrapper -> backend`. Before adding a layer, abstraction, type,
    generator, or new runtime/protocol, ask: can this already be
    expressed in Lisp itself (rule 8)? Does an existing mechanism
    already compose into this, so the answer is composition, not a new
    layer? Can something be deleted after this change — if not, the
    growth needs an unusually good reason. Does the new abstraction add
    real expressiveness, or does it just rename existing complexity
    under a new name? Is the path from Canon to execution still
    traceable without a five-page diagram? Reverse the usual planning
    order: try expressing the need directly in Lisp first, then try
    composing existing mechanism, then try whether something can be
    deleted instead — only add a new primitive after those three fail,
    and write down why. Unofficial quality signal, "Power / Complexity":
    +500 lines of mechanism, +3 new types, +2 new formats, +1 new
    generator, for a Lisp program only 5 lines shorter, is a bad trade;
    -300 lines of Rust, -2 special cases, -1 duplicated table, with the
    same semantics still expressible in Lisp, is close to an ideal one.
    Review every change against three questions: are there fewer places
    where truth lives; is the path from Canon to execution easier to
    trace; can something be deleted after this change. This applies
    across the whole swarm (`my-lisp`, `cml`, `wsm-my-lisp`,
    `fpga-lisp`, `wsm-os-lisp`), not just this repo.
15. **Перед будь-якою задачею — живий Current Technology Preflight
    (`TECH-SCAN`).** Після локального `WAKE`/`RECONCILE`, але **до**
    `CLAIM`, проєктування рішення, вибору бібліотеки/протоколу/архітектури,
    написання коду чи оптимізації агент зобов'язаний зробити реальний
    пошук в Інтернеті саме по темі задачі: що з'явилося нового, які
    актуальні releases/стандарти/інструменти/prior art існують, що
    змінилося останнім часом і чи не розв'язана вже проблема краще.
    Пам'ять моделі, cached knowledge і лише локальна документація **не
    рахуються** як `TECH-SCAN`. Для технічної теми віддавати перевагу
    первинним джерелам: official docs, release notes/changelogs,
    standards, upstream repositories, papers; щонайменше одне джерело
    має бути датованим і актуальним, якщо таке існує. Для великої
    архітектурної/AI/compiler/GPU/FPGA/performance задачі потрібен
    глибший огляд; для механічної дрібниці scan може бути коротким, але
    не нульовим. Відсутність релевантних новинок теж є результатом і
    записується явно. Мінімальний evidence: `date`, `task/topic`,
    `queries/scope`, `sources`, `new/relevant`, `decision` (`adopt` /
    `adapt` / `reject` / `no-change`). Якщо живого доступу до Інтернету
    немає, агент ставить стан `blocked-current-tech` і не переходить до
    дизайну/реалізації, доки власник явно не дозволить пропустити scan.

    **English auxiliary:** Every task requires a live web-based Current
    Technology Preflight after local context reconciliation but before
    claiming, designing, choosing dependencies/architecture, coding, or
    optimizing. Model memory and cached knowledge do not count. Scale
    depth to task size, prefer current primary sources, record dated
    evidence and the resulting decision, and fail closed as
    `blocked-current-tech` when live web access is unavailable unless
    the owner explicitly waives the scan.

16. **Асиметричний semantic firewall (#1347): Rust може рости, Lisp не копіює Rust як істину.** Попередні правила про `library before primitive`, зменшення Rust або винесення поведінки в Lisp **не є вимогою міграції** і не можуть блокувати локальну Rust/runtime/compiler semantics. Rust може мати власні таблиці SID→meaning, enums, dispatch, fallback, optimization metadata й експериментальні закони. Самодостатність my-lisp означає інше: коли мовний закон існує в Lisp, він має бути сформульований і перевірений незалежно від структури поточного Rust implementation. Заборонений лише зворотний напрямок — `Rust/host/backend semantics -> Lisp language authority`. Не перенось Rust type names, match arms, tables або fallback rules у Lisp лише для того, щоб "забрати семантику з Rust"; це саме і є contamination, від якого ми захищаємо мову.

17. **SENS-primary (#1590): ідентичність → значення → виконання.** Machine-readable: `knowledge/sens-primary.lisp`. Функціональний простір — рівно 256 SENS (`00000000..11111111`), кожен рівно 8 біт. SENS не є текстом, string, quoted literal, десятковим числом чи англійським ім'ям. Історичні назви (CAR, CDR, CONS, EQ, ATOM, COND, PLUS, …) — лише surface, не semantic authority. Backend (Rust, C, Common Lisp, Prolog, Datalog, CLIPS, FPGA, WASM) — свідок виконання, не джерело значення. Не створюй «зручний тимчасовий» текстовий сурогат SENS у ядрі, якщо можна зберегти один байт. Не вводь паралельної канонічної identity поруч із SENS. Перед зміною питай: *«Як би це виглядало, якби SENS був первинним з 1958, а англійські імена з'явилися лише як surface?»* — а не *«Як прикрутити SENS до звичного Lisp?»*. При конфлікті історична Lisp-традиція vs однозначність SENS — перемагає SENS; compatibility будується зверху.

   **English auxiliary:** Design as if SENS were primary from the start. Identity (8-bit SENS), meaning (language law), and execution (witness backend) stay separate. Historical English names are surfaces only. Prefer one-byte transport over text surrogates in the core. No second canonical identity layer.


## Rule 0 for coordination specifically

**Verify the swarm protocol before joining it.** Don't trust a cached
`AGENTS.md` claim about which port/process coordination runs on — read
the current `docs/swarm-mesh-v2.md` (or the equivalent doc in whichever
repo you're in) and confirm live state (`(list-members)`, a `(metrics)`
call) before acting on it. This is exactly the drift rule 1 warns about,
applied to the one piece of infrastructure every agent depends on
immediately at session start.

## Wake-up sequence (mandatory before task work)

```
PHASE 0 — WAKE       read AGENTS.md, machine contracts, tasks, evidence
PHASE 1 — RECONCILE  prose vs machine state; sibling contract versions;
                      stale claims (this is where rule 1 gets applied)
PHASE 2 — TECH-SCAN  live Internet scan for current/new work on the task;
                      record sources + new/relevant + decision (rule 15)
PHASE 3 — CLAIM      pick one bounded task, claim it in the registry
PHASE 4 — ATTACK     try to falsify the assumption the task rests on
PHASE 5 — IMPLEMENT  minimum change
PHASE 6 — VERIFY     local + conformance + relevant sibling check
PHASE 7 — RECORD     evidence + commit + durable status update
PHASE 8 — HANDOFF    notify with a pointer to evidence, not an opinion
```

A minimal durable preflight record is intentionally small:

```text
TECH-SCAN
  date: YYYY-MM-DD
  task/topic: ...
  queries/scope: ...
  sources: ...
  new/relevant: ...
  decision: adopt | adapt | reject | no-change
```

The point is not browsing for its own sake. The point is to prevent the
swarm from solving a 2026 problem using only the model's remembered
state of 2024/2025 technology, or from re-inventing something upstream
has already shipped. Search first, then decide.

## Subagents: use them as independent sensors, not extra hands

The main session owns final decisions, architectural consistency, and
writes to authoritative files. A subagent's job is to reduce
uncertainty independently — source verification, differential
implementation review, adversarial/red-team review, documentation-drift
audits, profiling, cross-repo compatibility checks — and report back
`finding / evidence / confidence / unknowns / next discriminating test`,
not a decision.

Delegate when at least one is true: the task spans more than one repo;
the claim affects a contract; there's a historical/source question;
there are two plausible interpretations; the change touches more than
three architectural components; a performance claim is being made; the
same bug could hide in both the tests and the implementation; host-
language leakage is possible.

**Don't bias a verifier with your preferred answer.** Hand it the
failing input and the contract, not your theory of the bug. If every
subagent agrees immediately, check whether they were actually
independent (same prompt bias, shared context, leading question).

Keep subagent context narrow and the task's scope explicit — a subagent
told "audit only macro semantics: read these four files, return
confirmed-equivalences / disagreements / unmapped-behavior / smallest-
distinguishing-test" is far more useful than one told "review this repo."

## Linguistic/specialist models (e.g. Sarvam) as a secondary hypothesis source

Where a repo has access to a specialist model (Sarvam or similar, for
Sanskrit/Pāṇini/Indic-language work), treat its output the same way as
any subagent's: **an independent hypothesis or secondary analysis, never
authoritative evidence.** It's genuinely useful for IAST/Devanāgarī
sanity checks, traditional-terminology framing, alternative readings,
and translation comparison — but a claim about dhātu/kāraka/saṃjñā
semantics still needs a primary source before it's a fact, same as any
other unsourced claim under rule 2. When prompting it, explicitly ask it
to describe the traditional/Paninian concept on its own terms first and
label uncertainty, rather than mapping straight to a computational
analogy — collapsing that distinction early is exactly what
`my-lisp-panini`'s own gate-review process exists to prevent. Keep the
API key in an environment variable on whoever's machine holds it; never
put it in a prompt, script argument, or committed file.

**Operational how-to (access paths, the reasoning-model empty-`content`
bug, prompt shape for real independence): see `shiva-sutras`'s
`docs/how-to-work-with-sarvam.md`, written from direct testing
2026-08-18 — don't re-derive this from scratch, it's already been
worked out and verified against real API responses.** Short version of
the one bug worth knowing before you burn a context window on it:
`sarvam-105b` is a reasoning model whose invisible `reasoning_content`
draws from the same `max_tokens` pool as the visible answer, so a
capped request can return `finish_reason: "length"` with an empty
`content` — don't set `max_tokens` for short asks, split big asks into
several small calls instead of relying on truncation.

## One shared experiment beats many local ones

If you're choosing what to work on and nothing is clearly higher
priority, prefer a single small change that's independently checkable
by a neighbor (a fixture both `my-lisp` and `cml` can run, a trace both
`fpga-lisp` and `my-lisp-panini` can inspect) over a larger change
that's only checkable by you. A result three repos can independently
verify is worth more than three unrelated repos each shipping something
no one else can check.
