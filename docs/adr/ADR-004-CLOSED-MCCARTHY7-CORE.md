# ADR-004: Closed McCarthy-7 Core and Stratified Semantic Taxonomy
# ADR-004: Замкнене McCarthy-7 ядро та стратифікована семантична таксономія

**Статус:** Частково замінено ADR-005 / Partially superseded by ADR-005
**Дата / Date:** 2026-09-05
**Автор / Authority:** Volodymyr / Vova (Owner directive) & Antigravity
**Обсяг / Scope:** Історичне нормативне рішення. Постійне замикання множини примітивів на семи замінене ADR-005; стабільна тотожність Canon 0 + McCarthy-7 та розрізнення семантики й реалізації лишаються чинними. / Historical normative decision. The permanent seven-primitive closure is superseded by ADR-005; the stable identity of Canon 0 + McCarthy-7 and the distinction between semantics and implementation remain in force.

---

## Примітка про заміну / Supersession note

ADR-005 замінює лише правила постійного замикання з цього ADR: заборону восьмого примітива, твердження, що лише сім identities можуть будь-коли мати primitive status, і відповідне правило `PRIMITIVE_SET_VIOLATION`, засноване лише на кількості > 7. McCarthy-7 identities лишаються стабільним історичним/мінімальним коренем.

English auxiliary: ADR-005 supersedes only the permanent closure rules of this ADR: the prohibition on an eighth primitive, the claim that only seven identities may ever be primitive, and the corresponding `PRIMITIVE_SET_VIOLATION` rule based solely on count > 7. The McCarthy-7 identities remain a stable historical/minimal root.

---

## 1. Контекст / Context

`my-lisp` defines itself as a minimal, homoiconic Lisp that grows from within itself. Historically, dialects of Lisp have suffered semantic bloat when host runtime conveniences, specialized evaluator optimizations, or substrate capabilities silently leaked into the language's core axiomatic definition.

The current Rust implementation in `crates/my-lisp` provides a rich set of facilities (arithmetic, exact rationals, closures, strings, I/O, hashing, JSON, date/time, and vectors). Without a strict normative boundary, it is dangerously easy to conflate everything present in the implementation with the fundamental ontological core of the language.

---

## 2. Нормативне рішення / Normative Decision

### Українська:
1. **Замкнене ядро McCarthy-7 складається рівно із семи канонічних семантичних тотожностей:**
   ```text
   { PRIM_QUOTE, PRIM_ATOM, PRIM_EQ, PRIM_CAR, PRIM_CDR, PRIM_CONS, PRIM_COND }
   ```
   Історичні назви Маккарті (`quote`, `atom`, `eq`, `car`, `cdr`, `cons`, `cond`) та відповідники людськими мовами (наприклад, українське `атом`, санскритські позначення) є поверхневими представленнями, що резолвляться в ці тотожності; жодне конкретне написання саме по собі не є семантичною тотожністю.
2. **Канонічні ідентифікатори як онтологічні дескриптори:** Позначення на кшталт `PRIM_ATOM` є нормативними дескрипторами семантичних тотожностей у документації, архітектурі та маніфестах конформності. Реалізація може кодувати їх числовим кодом/опкодом, enum'ом, символом або таблицею розпізнавання — форма представлення не визначає семантику.
3. **Восьмий примітив не може бути доданий.** Жодна реалізація, компіляторний бекенд, рантайм-субстрат, стандартна бібліотека чи майбутнє розширення не мають права розширювати цей набір тотожностей.
4. **Канонічне конформне формулювання:**
   > *«Конформна реалізація може надавати багато мовних можливостей та поверхневих назв, але статус семантичних примітивів мають рівно сім канонічних тотожностей: `PRIM_QUOTE`, `PRIM_ATOM`, `PRIM_EQ`, `PRIM_CAR`, `PRIM_CDR`, `PRIM_CONS`, `PRIM_COND`. Конформність перевіряє саме наявність та семантику цих семи тотожностей, а не текстові ASCII-рядки. Жодна інша можливість не може набути статусу примітива.»*
5. **Зручність реалізації не створює онтологію мови.** Наявність апаратної інструкції (наприклад, FPGA `ADD`, x86 `lea`) або допоміжної функції рантайму субстрату (наприклад, `wsm_add`, `wsm_pci_config_read16`) не робить цю операцію семантичним примітивом `my-lisp`.
6. **Без самостверджувальної інтроспекції:** Мова **не** повинна містити внутрішньої операції переліку примітивів (на кшталт `primitive-names`). Перевірка замкненості множини належить виключно зовнішньому маніфесту відповідності та тестовому harness.
7. **Негативний інваріант:** Будь-який маніфест реалізації чи звіт конформності, який включає додаткові тотожності (наприклад, `add`, `eval`, `lambda`, `read`) до множини примітивів, бракується за правилом fail-closed із результатом `PRIMITIVE_SET_VIOLATION`.

### English:
1. **The closed McCarthy-7 core consists of exactly seven canonical semantic identities:**
   ```text
   { PRIM_QUOTE, PRIM_ATOM, PRIM_EQ, PRIM_CAR, PRIM_CDR, PRIM_CONS, PRIM_COND }
   ```
   Historical McCarthy spellings (`quote`, `atom`, `eq`, `car`, `cdr`, `cons`, `cond`) and all human-language spellings (e.g. Ukrainian `атом`, Sanskrit representations) are surface representations that resolve to these identities; no surface spelling is itself the semantic identity.
2. **Canonical Identifiers as Ontological Descriptors:** Identifiers such as `PRIM_ATOM` are normative descriptors of semantic identity in documentation, architecture, and conformance manifests. An implementation is free to represent them as opcodes, machine integers, enums, symbols, or resolution tables — implementation representation does not define semantics.
3. **No eighth primitive may be admitted.** No implementation, compiler backend, runtime substrate, standard library, or future architectural extension may enlarge this set of identities.
4. **Canonical Conformance Formulation:**
   > *“A conforming implementation may expose many language capabilities and surface spellings, but it shall classify exactly seven operations as semantic primitive identities: `PRIM_QUOTE`, `PRIM_ATOM`, `PRIM_EQ`, `PRIM_CAR`, `PRIM_CDR`, `PRIM_CONS`, and `PRIM_COND`. Verification tests conformance of these seven semantic identities, not textual ASCII spellings. No other capability may acquire primitive status.”*
5. **Implementation convenience cannot create language ontology.** The presence of an instruction in hardware (e.g. FPGA `ADD`, x86 `lea`) or an execution helper in a substrate runtime (e.g. `wsm_add`, `wsm_pci_config_read16`) does not make that operation a semantic primitive of `my-lisp`.
6. **No Self-Proving Introspection:** The language shall **not** define an internal introspection form (such as `primitive-names`). Verification of the closed set belongs exclusively to external conformance test manifests and testing harnesses.
7. **Negative Invariant:** Any implementation manifest or conformance report that admits additional primitive identities (such as `add`, `eval`, `lambda`, or `read`) shall be rejected fail-closed as `PRIMITIVE_SET_VIOLATION`.


---

## 3. Строге розрізнення понять / Strict Non-Equivalence

To prevent semantic leakage, `my-lisp` strictly distinguishes the following categories:

```text
SEMANTIC PRIMITIVE
  ≠ ADMITTED DOMAIN SEMANTICS
  ≠ DERIVED FORM
  ≠ LANGUAGE EXTENSION
  ≠ RUNTIME BUILTIN
  ≠ COMPILER INTRINSIC
  ≠ SUBSTRATE ABI FUNCTION
  ≠ HARDWARE OPCODE
```

- **Semantic Primitive (L0):** One of the seven closed McCarthy operations that cannot be reduced without circularity.
- **Admitted Domain Semantics (L1):** First-class value types and representations recognized by the language (e.g. symbols, pairs, exact integers, exact rationals). Arithmetic over these domains is recognized as an admitted domain capability, **not** a silent expansion of the 7 primitives.
- **Derived Form (L2):** A syntax or operation whose entire semantics is defined by expansion/transformation into strictly lower layers, backed by empirical proof.
- **Language Extension (EXT):** An observable language capability admitted as a separate module or platform feature.
- **Runtime Builtin (IMPL):** An optimized host function in an implementation (e.g. Rust function, C subroutine) providing evaluation speed or host interaction.
- **Compiler Intrinsic:** Direct lowering directive inside a compiler (e.g. CML AST to native assembly).
- **Substrate ABI Function:** Freestanding machine interface (e.g. System V AMD64 integer calling convention in `wsm-os-target`).
- **Hardware Opcode:** Execution primitive of physical silicon (e.g. FPGA Verilog state machine or x86 ALU instruction).

---

## 4. Стратифікована архітектура / Stratified Architecture

Substrates do not sit as a language layer. The language exists purely as semantics, observed across independent implementations:

```text
               MY-LISP SEMANTIC PYRAMID
                          │
  ┌──────────────────────────────────────────────┐
  │ L0: CLOSED CANONICAL PRIMITIVE IDENTITIES    │
  │     PRIM_QUOTE, PRIM_ATOM, PRIM_EQ,          │
  │     PRIM_CAR, PRIM_CDR, PRIM_CONS, PRIM_COND │
  └───────────────────────┬──────────────────────┘
                          ▼
  ┌──────────────────────────────────────────────┐
  │ L1: ADMITTED VALUE DOMAINS                   │
  │     symbols, pairs, exact integers,          │
  │     exact rationals                          │
  └───────────────────────┬──────────────────────┘
                          ▼
  ┌──────────────────────────────────────────────┐
  │ L2: DERIVED LANGUAGE                         │
  │     lambda, def, let, list, cadr, ...        │
  │     (requires verified transformation witness)│
  └───────────────────────┬──────────────────────┘
                          ▼
  ┌──────────────────────────────────────────────┐
  │ L3: KNOWLEDGE / WORLD                        │
  │     SI defining constants (lib/si.lisp),       │
  │     physics, Panini, reasoning, chess        │
  └──────────────────────────────────────────────┘

────────────────────────────────────────────────────────
CANONICAL IDENTITY RESOLUTION (SURFACE LEXICONS):

       surface text:       "atom"         "атом"        "..."
                             │              │            │
                             └───────┬──────┘            │
                                     ▼                   ▼
                           [READER / RESOLVER]
                                     │
                                     ▼
                            CANONICAL IDENTITY:
                                 PRIM_ATOM
                                     │
                                     ▼
                                 SEMANTICS

────────────────────────────────────────────────────────
SUBSTRATES ARE ORTHOGONAL IMPLEMENTATION OBSERVERS:

                   my-lisp contract
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
       Rust core        C core       FPGA fabric
       (software)     (freestanding) (silicon gates)
```

### 4.1 Canonical Identity Table / Канонічна таблиця тотожностей

The canonical identity table is an autonomous normative entity separate from any environment, host runtime, or evaluator dispatch code. It formalizes the relation between the semantic identity and human-language surface signs:

Канонічна таблиця тотожностей є автономною нормативною сутністю, відокремленою від будь-якого середовища обчислення чи коду диспетчеризації. Вона формалізує відношення між семантичною сутністю та людськими знаковими системами:

#### Scope & Semantics Disclaimer / Застереження щодо області визначення
> **Normative Scope:** Semantic equations in this ADR define the canonical `my-lisp` interpretation of McCarthy7 identities and do not claim implementation equivalence with every historical Lisp dialect.

### 4.0 Canon 0: The Empty List / Канон 0: Порожній список

Before any operation can construct, deconstruct, or evaluate, there exists the **canonical ground**: the empty list `()`.

До того як будь-яка операція може сполучити, розібрати чи обчислити, існує **первинний канонічний ґрунт**: порожній список `()`.

```text
CANON 0: CANON_EMPTY_LIST
Surface representation: ()
Semantic class: Canonical Value (Ground Object)
Meaning: The list containing zero elements. The recursive origin of all proper lists.
```

#### Structural Laws of Canon 0 / Структурні закони Канону 0:
1. `(атом? ())` $\to$ `#t` (дискретний булевий факт: `()` не є cons-коміркою, його не можна розібрати на координати).
2. `(pair? ())` $\to$ `#f` (`()` не має лівої чи правої частини).
3. `(proper-list? ())` $\to$ `#t` (базовий випадок індуктивного визначення списку).
4. `eval(())` $\to$ `()` (**Self-Evaluating Law**): `()` обчислюється саме в себе без потреби в лапках `(як-є ())`. Воно є первинним літералом форми.

#### Constructive vs Residual Axioms / Конструктивна та залишкова аксіоми:
Списки не з'являються з повітря — вони виростають із `()`, а деструктуризація повертає структуру назад до `()`:

```text
Зростання структури (через сполучити):
()
  ↓ (сполучити c ())
(c)
  ↓ (сполучити b (c))
(b c)
  ↓ (сполучити a (b c))
(a b c)

Повернення до ґрунту (через решта):
(решта (a b c)) → (b c)
(решта (b c))   → (c)
(решта (c))     → ()  <-- Досягнуто Канон 0!
```

> **Epistemic Principle on NIL:** `()` is the sole canonical empty list. In `my-lisp`, `NIL` is **not** a canonical identity, not a truth-value, and not an autonomous primitive. Any historical spelling `nil` is at most a foreign compatibility alias, never the foundation of the language.

#### Surface Correspondence Principle / Принцип відповідності поверхні

> **A surface name is not a definition of the canonical identity it represents.**
>
> `atom` ≠ definition of `PRIM_ATOM`
> `атом` ≠ definition of `PRIM_ATOM`
> `aṇu`  ≠ definition of `PRIM_ATOM`
>
> All admitted surface signs point to the same canonical identity. None of them *defines* it. A surface name is admitted when:
> 1. It does not contradict the canonical semantic contract.
> 2. It provides good human intuition toward the operation.
> 3. It is natural in its human language.
> 4. It does not introduce new semantics.

> **Принцип:** Поверхнева назва — не визначення канонічної тотожності, яку вона позначає. `atom`, `атом` і `aṇu` — три незалежні людські проєкції однієї й тієї самої canonical identity. Жодна з них не є формальним визначенням операції.

| Canonical Identity | McCarthy 1960 | Українська (`uk`) | Sanskrit (`sa`) | Devanāgarī | Surface Status | Historical Correspondence | Conceptual Witness |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `PRIM_QUOTE` | `quote` | **`як-є`** | **`svarūpa`** | **स्वरूप** | **STABLE** | **STRONG ANALOGUE** | AS 1.1.68 *svaṃ rūpam* |
| `PRIM_ATOM` | `atom` | **`атом?`** | **`aṇu`** | **अणु** | **STABLE** | **PARTIAL ANALOGUE** | VS 7.1.10–11 *aṇu* |
| `PRIM_EQ` | `eq` | **`тотожне?`** | **`abheda`** | **अभेद** | **STABLE** | **PARTIAL ANALOGUE** | TS §80 *abheda* / *tādātmya* |
| `PRIM_CONS` | `cons` | **`сполучити`** | **`saṃyuj`** | **संयुज्** | **STABLE** | **PARTIAL ANALOGUE** | TS §27 $\sqrt{yuj}$ / *saṃyuj* |
| `PRIM_CAR` | `car` | **`перше`** | **`ādi`** | **आदि** | **STABLE** | **WEAK ANALOGUE** | VS 4.2.9 *āditva* |
| `PRIM_CDR` | `cdr` | **`решта`** | **`śeṣa`** | **शेष** | **STABLE** | **PARTIAL ANALOGUE** | NS 1.1.5 *śeṣa* / *śeṣavat* |
| `PRIM_COND` | `cond` | **`за-умовою`** | **`anukrama`** | **अनुक्रम** | **STABLE** | **PARTIAL ANALOGUE** | Mīmāṃsā *pāṭha-krama* |

> **Critical Epistemic Guardrail:**
> **Canonical surface stability ≠ historical semantic identity.**
> *Surface status: STABLE* certifies that these symbols are normative in the `my-lisp` surface grammar. It does **not** claim that ancient Indian philosophy anticipated McCarthy's computational machine. 0/7 are ISOMORPHIC; the Sanskrit terms serve as independent conceptual and comparative witnesses, not normative sources of computation.

#### Canonical Status Breakdown:
- **7 Stable (Complete Canon Ratification):**
  - `PRIM_QUOTE` (**`як-є`**): Suppresses ordinary evaluation mode; instructs the interpreter to take the expression literally *as it is*. Natural operational verb-like phrase in code, completely free from noun collisions with general "data/types" concepts.
  - `PRIM_ATOM` (**`атом?`**): Discrete non-pair predicate. Closed as stable after `(просте? 7)` exposed fatal collision with prime numbers.
  - `PRIM_EQ` (**`тотожне?`**): Ontological atom identity.
  - `PRIM_CAR` (**`перше`**): First coordinate projection $\pi_1$ over cons-cells.
  - `PRIM_CDR` (**`решта`**): Residual coordinate projection $\pi_2$ over cons-cells. Flawlessly passes the Triple Cons Test on proper lists, dotted pairs, and improper lists.
  - `PRIM_CONS` (**`сполучити`**): Dynamic pair constructor.
- `PRIM_COND` (**`за-умовою`** [uk] / **`anukrama`** / **अनुक्रम** [sa]): Sequential short-circuiting decision branch. Ratified as stable: anukrama reflects ordered sequential rule scan (pāṭha-krama).

#### Separation of Core Pair Mechanics from High-Level List Vocabulary:
`PRIM_CAR` and `PRIM_CDR` are primitive pair coordinate projections ($\pi_1, \pi_2$). Their semantics are formally defined on **cons-cells**. Proper list behavior is a derived property of recursive cons structures, NOT part of the primitive operation definition:

```text
PRIM_CAR / PRIM_CDR are pair projections.
Their semantics are defined on cons-cells.
List behavior is derived from recursive cons structure,
not part of the primitive meaning.
```

Canonical Triple Cons-Structure Test (Pair + Proper List + Improper List):
`решта` wins over `друге` due to avoiding cognitive collision on recursive cons-cells:
```lisp
;; 1. Proper List:
(перше '(1 2 3)) ;; → 1
(решта '(1 2 3)) ;; → (2 3)  [NB: "друге" фатально провокувало б очікування числа 2!]

;; 2. Canonical Dotted Pair:
(призначити p (сполучити 'кіт 42))
(перше p) ;; → кіт
(решта p) ;; → 42  [буквально: те, що лишилося після відокремлення першої координати]

;; 3. Improper List:
(решта '(1 2 . 3)) ;; → (2 . 3)
```

- **Core Primitives (Pair Foundation):** `сполучити`, `перше`, `решта`.
- **List Library Vocabulary (Derived APIs):** `голова`, `хвіст` MAY exist as high-level convenience aliases over proper lists (`(A B C)`), but `решта` is the primitive coordinate extractor $\pi_2$ interpreting $y$ as the residual element after $x$.

---

## 5. Audit of Current Rust Implementation / Аудит поточної Rust-реалізації

We do not disguise the current state of `crates/my-lisp` by asserting that everything outside the seven primitives is "already proven derived or merely an invisible builtin." Instead, we explicitly classify current visible features, introducing the status `? UNRESOLVED` (semantic debt requiring explicit derivation proof or formal admission):

| Feature / Surface Form | Current Rust Mechanism | Semantic Status in `my-lisp` | Note / Rationale |
| :--- | :--- | :--- | :--- |
| `quote` | special form (`eval/mod.rs`) | **L0 PRIMITIVE (PRIM_QUOTE)** | Historical lineage surface spelling |
| `atom` | builtin (`eval/builtins.rs`) | **L0 PRIMITIVE (PRIM_ATOM)** | Historical lineage surface spelling |
| `eq` | builtin (`eval/builtins.rs`) | **L0 PRIMITIVE (PRIM_EQ)** | Historical lineage surface spelling |
| `car` | builtin (`eval/builtins.rs`) | **L0 PRIMITIVE (PRIM_CAR)** | Historical lineage surface spelling |
| `cdr` | builtin (`eval/builtins.rs`) | **L0 PRIMITIVE (PRIM_CDR)** | Historical lineage surface spelling |
| `cons` | builtin (`eval/builtins.rs`) | **L0 PRIMITIVE (PRIM_CONS)** | Historical lineage surface spelling |
| `cond` | special form (`eval/mod.rs`) | **L0 PRIMITIVE (PRIM_COND)** | Historical lineage surface spelling |
| `symbols` | `Value::Symbol`, interning | **L1 ADMITTED DOMAIN** | Admitted atomic value |
| `pairs` | `Value::Pair` | **L1 ADMITTED DOMAIN** | Compound data domain |
| `exact integers` | `BigInt` (`bignum.rs`) | **L1 ADMITTED DOMAIN** | Admitted numeric domain |
| `exact rationals` | `Rational` (`bignum.rs`) | **L1 ADMITTED DOMAIN** | Admitted numeric domain |
| `+`, `-`, `*`, `/` | builtin / `arithmetic.rs` | **? UNRESOLVED** | Distinct domain capability vs primitive leak |
| `<`, `>`, `=` | builtin / `arithmetic.rs` | **? UNRESOLVED** | Predicates over numbers |
| `lambda` | special form (`closures.rs`)| **? UNRESOLVED** | Evaluator constructs closure directly; derivation unproven |
| `def` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Environment binding form |
| `defmacro` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Meta-programming mechanism |
| `eval` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Evaluator reflection |
| `print`, `princ` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Host I/O side effect |
| `read`, `read-all` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Host reader reflection |
| `strings` family | special forms & `Value::String` | **? UNRESOLVED** | Text domain vs pair encoding |
| `vectors` family | builtins (`eval/builtins.rs`) | **? UNRESOLVED** | Random-access array domain |
| `sha256-hex` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Host cryptographic utility |
| `json-parse` | special form (`eval/mod.rs`) | **? UNRESOLVED** | Host data interchange utility |
| `utc-now`, `ntp` | builtins (`eval/builtins.rs`) | **? UNRESOLVED** | Host capability / wall-clock service |

---

## 6. The Evidence Requirement for "Derived" / Вимога доказу для статусу «Derived»

**"Derived is a claim requiring evidence."**
An operation or syntactic form cannot be declared `L2 DERIVED` simply because it is desirable or conceptually elegant. A valid derivation requires an executable witness:
1. **Explicit Transformation / Definition:** The form must be expressed solely in terms of admitted lower layers (L0 primitives and L1 admitted domains).
2. **Behavioral & Semantic Parity:** An automated conformance test must prove that the derived expression satisfies all contract obligations identically to any reference engine.
3. **No Hidden Evaluator Intrinsics:** The evaluator must not rely on unadmitted internal hooks or bypasses to execute the form.

---

## 7. Consequences / Наслідки

1. **Freedom from Ontological Creep:** Future agents, implementers, and backends are prohibited from promoting convenience operations (such as `add` or `eval`) to primitive status.
2. **Honest Roadmap for Simplification:** The `? UNRESOLVED` column identifies the exact semantic debt of the Rust implementation. Subsequent milestones will systematically resolve each `?` into either an admitted value domain, a proven derived form, an external capability, or a cleanly sequestered host tool.
3. **Substrate Neutrality:** `my-lisp` remains an autonomous mathematical creation that presides above Rust, C, and FPGA silicon.

---

## 8. Closed: Canon Access Architecture (2026-09-06)
## 8. Закрито: Архітектура доступу до канону (2026-09-06)

> **Superseded for Canon 0+7 binding semantics by ADR-006 / Contract 6.0 (2026-09-08).** The text below is retained as historical evidence of the earlier Variant-A decision; it is no longer normative where it permits shadowing Canon spellings.
>
> **Замінено для семантики зв’язування Canon 0+7 рішенням ADR-006 / Contract 6.0 (2026-09-08).** Текст нижче збережено як історію попереднього Variant A; дозвіл затінювати канонічні написання більше не є нормативним.

The question of canonical access semantics (initiated during the canon-namespace-shadowing research cycle, `docs/research/canon-namespace-shadowing.md`) is **closed with the following decision:**

Питання семантики доступу до канону (досліджене в `docs/research/canon-namespace-shadowing.md`) **закрите з таким рішенням:**

**Chosen: Variant A — No privileged `canon:*` namespace. / Обрано: Варіант A — без привілейованого простору імен `canon:*`.**

The two requirements that were at risk of being conflated:

```text
Canon must be immutable
  ≠
User must always have a magic unshadowable path to Canon
```

**Resolution:** The Canon is an invariant of the specification and the conformance harness — **not** an invariant enforced in the runtime lexical environment. Any surface name (`atom`, `атом`, `canon:atom`) is an ordinary symbol that may be shadowed in a local scope. Shadowing a surface name does not alter, redefine, or pollute the canonical semantic identity it refers to. `PRIM_ATOM` remains what it is regardless of what the local scope says about the word `atom`.

**The closed formula:**

```text
CANON defines meaning.
Environment binds names.
Names may change.
Meaning does not.
```

**What this closes permanently:**

| Proposal | Status |
| :--- | :--- |
| Variant B: protected `canon:*` prefix | **REJECTED** — introduces privileged lexical class, increases ontology, complicates C/FPGA implementation (requires prefix-aware string inspection in binders) |
| Variant C: separate ROM dispatch map | **REJECTED** — reinvents `(core ...)` under namespace syntax |
| `(core ...)` special form | **REJECTED** — would create an 8th primitive via backdoor |
| Destructive normalization `атом → atom` at reader | **REJECTED** — destroys homoiconicity |
| `canon:*` as semantic-privileged namespace | **REJECTED** — `canon:*` may exist as library convention only |

**What remains open** (not affected by this decision):

- Ukrainian surface spellings for `PRIM_CAR`, `PRIM_CDR`, `PRIM_CONS`, `PRIM_COND`, `PRIM_EQ`, `PRIM_QUOTE` — deliberately `?` in §4.1 above.
- `lambda` genealogy — ADR-004 §5 status `? UNRESOLVED`, next research target after this closure.

