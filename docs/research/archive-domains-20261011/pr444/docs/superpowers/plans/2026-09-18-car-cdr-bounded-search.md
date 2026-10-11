# План експерименту #432: bounded/fixed-point пошук для CAR/CDR

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Фальсифіковано перевірити, чи `PRIM_CAR` або `PRIM_CDR` можна отримати з явно слабшої структурної бази без прихованого pair-destructuring; не змінювати семантику мови.

**Architecture:** Дослідження має два незалежні докази. Перший — конкретний RED для Church-pair маршруту: звичайний `cons`-pair не є callable selector-carrier. Другий — Lisp-owned abstract fixed-point search для бази `B = {Canon 0, quote, atom, eq, cons, cond, lambda/define composition}` без `car/cdr`: він відстежує, чи може свіжий runtime-атом, який існує лише всередині input pair, з'явитися як top-level result. Метапошук може використовувати `car/cdr` для обходу власних research-даних; це не є candidate derivation і не входить у базу `B`.

**Tech Stack:** my-lisp `.lisp` research scripts, existing CLI/evaluator, GitHub Actions у stacked verification-only PR.

**Spec:** GitHub issue #432, parent #419.

## Global Constraints

- База: fresh `main@23cfdc141ef1e7ab4275d27c536a99d1018f3292`.
- Не змінювати `language-contract.lisp`, ADR-004, Canon registry, evaluator/runtime, `tests/fixtures`, `knowledge/`, `evidence/` або production `lib/**`.
- Не торкатися файлів активних #421, #422/#418/#410/#406/#396, #427, #328, #402/#403, #409/#424 family, #317, #305 family.
- Жодного нового Rust semantic oracle.
- Вхідні payload-атоми створюються runtime `gensym`, тому candidate literals не можуть їх hard-code.
- `no witness` у finite syntactic search означає лише bounded negative evidence.
- Fixed-point abstract result є відносним до явно названої бази `B`; він не доводить абсолютну незвідність проти всіх можливих майбутніх primitives.
- Будь-який один `pair-eliminator`, який заміняє `car+ cdr`, класифікується окремо як basis-compression/basis-exchange, а не як derivation з поточної нижчої бази.

---

### Task 1: RED для Church-pair маршруту

**Files:**
- Create: `docs/research/432/church-pair-car-red.lisp`
- Create: `docs/research/432/church-pair-cdr-red.lisp`

**Interfaces:**
- Consumes: current `cons`, ordinary function application.
- Produces: два executable probes, які повинні завершитися Type/NotCallable-подібною помилкою саме при спробі викликати pair як функцію.

- [ ] **Step 1: Створити CAR probe**

```lisp
(def pair-value (cons (quote fresh-left) (quote fresh-right)))
(pair-value (lambda (left right) left))
```

- [ ] **Step 2: Створити CDR probe**

```lisp
(def pair-value (cons (quote fresh-left) (quote fresh-right)))
(pair-value (lambda (left right) right))
```

- [ ] **Step 3: У verification-only workflow вимагати nonzero exit саме з callable/type failure**

Очікування: failure походить від того, що ordinary `cons` data pair не є callable Church pair. Parser/Cargo/CLI failure не зараховується.

### Task 2: Fresh-atom fixed-point checker

**Files:**
- Create: `docs/research/432/fresh-atom-fixed-point.lisp`

**Interfaces:**
- Consumes: research-only abstract states і transfer rules, що відповідають observable ролям `quote/atom/eq/cons/cond`.
- Produces: structured result `(fresh-atom-search ...)` з rounds, stabilization status і `fresh-top-level` reachability.

- [ ] **Step 1: Визначити closed abstract domain**

```text
static-atom      ; literal atom independent of runtime input
static-pair      ; pair containing no fresh runtime payload
fresh-nested     ; fresh runtime payload exists only inside a pair/structure
record-pair      ; atom/eq structured result record
undefined        ; route is not defined (e.g. eq on a pair)
fresh-top-level  ; forbidden target capability: extracted runtime payload atom
```

- [ ] **Step 2: Визначити transfer rules**

```text
x(pair-with-fresh) -> fresh-nested
quote(atom)        -> static-atom
quote(pair)        -> static-pair
atom(any-defined)  -> record-pair
eq(nonpair,nonpair)-> record-pair
eq(pair,*)         -> undefined
cons(a,b)          -> fresh-nested if a/b carries fresh payload, otherwise static-pair
cond(...)          -> union of branch result capabilities; cond creates no new payload
lambda/define      -> composition/binding only; creates no projection capability
```

- [ ] **Step 3: Iterate closure until stable or round bound 8**

Expected: closure stabilizes without ever adding `fresh-top-level`.

- [ ] **Step 4: Fail closed**

If `fresh-top-level` appears, checker returns `(result witness-found)` and includes the generating rule. If stabilization does not occur by round 8, return `(result insufficient-bound)`; do not call it proof.

### Task 3: Concrete runtime assumption witnesses

**Files:**
- Create: `docs/research/432/lower-basis-runtime-witness.lisp`
- Verification-only child workflow only: `.github/workflows/verify-432-car-cdr-research.yml`

**Interfaces:**
- Consumes: current evaluator.
- Produces: fresh observations that the abstract transfer assumptions match current runtime behavior where executable without inventing an oracle.

- [ ] **Step 1: Use `gensym` for fresh payloads**

Construct runtime pairs whose head/tail symbols cannot occur in candidate source literals.

- [ ] **Step 2: Check `atom` and `cons` observations**

Require explicit canonical results: pair inputs classify as `(structural-kind pair)`; constructed cons remains a pair and never returns an embedded fresh atom as top-level value.

- [ ] **Step 3: Separate RED for `eq` on pair**

Run a small probe that calls `eq` on pair operands. Require the current named Type failure; do not let a crash/parser error count.

- [ ] **Step 4: Check canonical `cond` branch preservation**

Use explicit three-part dispatch and fresh payload values to show `cond` returns the selected branch value but does not transform/extract data from it.

### Task 4: Verification-only execution

**Files:**
- Child branch: `verify/432-car-cdr-research`
- Add only temporary workflow and, if needed, verification marker data.

**Interfaces:**
- Consumes: Tasks 1–3 research files.
- Produces: GitHub Actions run with exact logs; child PR is NEVER MERGE.

- [ ] **Step 1: Open stacked draft PR against `research/432-car-cdr-bounded-search`**

- [ ] **Step 2: Run both Church RED probes**

Expected: both fail for the intended pair-not-callable reason.

- [ ] **Step 3: Run fixed-point checker**

Expected: `fresh-top-level` unreachable and closure stabilized by <=8 rounds.

- [ ] **Step 4: Run concrete runtime witness and `git diff --check`**

- [ ] **Step 5: Inspect logs before interpreting result**

Infrastructure/Cargo/parser failures are not semantic evidence.

### Task 5: Feed result back conservatively

**Files:**
- No semantic authority files.
- Update issue #432 comment; parent #419 only receives a coordination/result comment after observed execution.

**Interfaces:**
- Produces: exact classification boundary.

- [ ] **Step 1: Record the strongest defensible claim**

Allowed if GREEN:

```text
Within declared basis B, the fresh runtime component cannot be generated as a top-level result without a pair-destructuring capability; the tested Church-pair route is falsified.
```

Forbidden:

```text
CAR/CDR are absolutely irreducible in every possible Lisp basis.
```

- [ ] **Step 2: Keep #419 classification globally conservative**

`PRIM_CAR`/`PRIM_CDR` may move from generic `insufficient-evidence` only to a relative/basis-qualified finding unless owner review defines a stronger classification vocabulary.

- [ ] **Step 3: Separate basis-compression follow-up if warranted**

A single eliminator such as conceptual `pair-elim(pair, k)` with

```lisp
(car-derived p) = (pair-elim p (lambda (left right) left))
(cdr-derived p) = (pair-elim p (lambda (left right) right))
```

is a different hypothesis: one destructor replacing two projectors. Treat it as basis-compression/basis-exchange, not evidence that `car/cdr` were derivable from the current lower basis.
