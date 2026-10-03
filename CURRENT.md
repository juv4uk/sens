# CURRENT — where the truth actually lives

**Оновлено:** 2026-10-03

Це точка входу для питання **«що зараз чинне?»**. Якщо інший документ,
старий план, historical report або archived PoC суперечить джерелам нижче,
чинніші джерела перемагають.

Коротка карта нової архітектури:
[`docs/current-binary-domain-architecture.md`](docs/current-binary-domain-architecture.md).

## 1. Поточна онтологія

Owner paradigm #2490:

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Тобто:

```text
bits + domain + law -> meaning
```

Наслідки:

- однакові біти не гарантують однакової семантики;
- однакова width не є semantic domain;
- однакова machine transform не є автоматично одним semantic law;
- free coordinate не є function/resident;
- людська назва, opcode, registry row, AST, JSON, hash або cache не стають
  canonical identity лише через реалізацію.

Standing negative control: #2508/#2509.
Bounded positive convergence control: #2495/#2502.

## 2. Authority order

Не всі типи тверджень мають одного власника. Поточна практична ієрархія:

1. **Owner-ratified/current decisions для відповідного scope**
   - #2490 — binary-domain ontology;
   - #2533 — historical-first phase order;
   - #2414 — D5/D6 width/domain ratification;
   - #2415 — D7 role/domain ratification;
   - інші явно ratified/owner decisions у відповідному домені.
2. **Machine-readable language/runtime authority**
   - [`language-contract.lisp`](language-contract.lisp) — current observable
     runtime/language contract для охопленого ним scope;
   - ratified machine-readable laws/guards;
   - admitted executable conformance fixtures.
3. **Executable witnesses and falsifiers**
   - focused research harnesses;
   - CI gates;
   - cross-implementation parity;
   - counterexamples.
4. **Reference mechanisms**
   - [`crates/sens`](crates/sens);
   - independent Rust/C/WASM/FPGA/other implementations.
5. **Generated reference and explanatory docs**
   - generated maps/tables;
   - README, CURRENT, architecture docs.
6. **Historical/process material**
   - `docs/archive/**`;
   - dated research records;
   - superseded plans/notes.

Якщо owner decision ще не перенесений у machine-readable contract, це не
означає, що старіша проза має право його скасувати. Це означає, що є
**migration debt**, яку треба назвати явно.

## 3. Core зараз

Core — реконструкція/продовження лінії:

```text
Lisp I -> Lisp 1.5 -> SENS
```

Поточний порядок дослідження (#2533):

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

Тому:

```text
historically present != fundamental in SENS
derivable in SENS     != absent from history
```

### Ratified domain status

- **D1** — ratified PredicateBit.
- **D2** — ratified `racanā2` structure.
- **D3/D4** — ratified current Core foundation.
- **D5/D6** — ratified **domain widths/ontology**, але historical occupancy і
  final SENS maps ще не вважаються завершеними.
- **D7** — ratified Sound7 + local śloka/sūtra ordinals; не general Number.
- **D14** — research: full Pāṇini grammar graph.
- **D24/D48/...** — research: exact Number / FPGA-oriented numeric domains.

D6 PURE-UNKNOWN coordinates лишаються UNKNOWN, поки independent law не
заробить placement. Вільний слот, chronology або numeric proximity не є
доказом.

Parentless semantic root теж не отримує width автоматично. #2662/#2667/#2669
досліджують exact domain admission для residue/root cases.

## 4. Core-Math зараз

Core-Math — окрема mathematical language/research line.

Мінімальна модель:

```text
binary input(s)
+ admitted mathematical law
-> binary output
```

#2485/#2491 — bounded minimal binary executor.
#2494/#2500 — exact-Q group factor law.
#2460 та наступні experiments — evidence про law-generated operations.

Core-Math не успадковує Core placement, Lisp vocabulary або Core domain
membership автоматично.

## 5. Core ↔ Core-Math

Три допустимі результати:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

Convergence вимагає незалежного збігу:

```text
same binary object
+ same exact domain
+ same semantics
+ same law
+ cross-proof
```

#2502 — bounded selector convergence.
#2509 — negative control: same `2*x+b` mechanism у selector і Q-group domains
не зливає semantic laws.

## 6. Domain != carrier != mechanism

#2540:

```text
domain     = law-bearing semantic context
carrier    = exact bit/width representation
mechanism  = execution/transport substrate
```

Приклади:

```text
D7.SoundCell [carrier=W7]       # semantic domain
D7.LocalOrdinal [carrier=W7]    # distinct semantic context
W7                              # carrier only
FPGA / Rust / radio             # mechanism only
```

## 7. Research task grammar

Для governed Core/Core-Math research:

```text
PHASE
DOMAIN
BINARY OBJECT
LAW
WITNESS
FALSIFIER
STATUS
RELATION
```

Allowed phase values:

```text
HISTORICAL-INGEST
STRUCTURAL-DISCOVERY
SENS-DERIVATION
```

Explicit UNKNOWN/UNRESOLVED є валідним станом. Decorative completeness — ні.

## 8. What is explicitly NOT authoritative

- `docs/archive/**`;
- human names as machine identity;
- free-space placement;
- benchmark speed as semantic proof;
- host/runtime implementation detail;
- hash/AST/JSON/cache/registry merely because tooling uses them;
- RF frequency/modulation as semantic identity;
- a peer-agent statement without reproducible evidence.

## 9. For a new agent starting cold

1. Read [`AGENTS.md`](AGENTS.md).
2. Read this file.
3. Read
   [`docs/current-binary-domain-architecture.md`](docs/current-binary-domain-architecture.md).
4. Read [`docs/semantic-authority-map.md`](docs/semantic-authority-map.md).
5. For Core work, identify PHASE first.
6. For every semantic claim, name DOMAIN + BINARY OBJECT + LAW.
7. Find the strongest WITNESS and FALSIFIER before changing placement.
8. Treat UNKNOWN as a legitimate result.
9. Run the focused CI gate before claiming a result.

## 10. Historical note

Earlier repository states used flat SID8/Function8 and multiple Core profiles.
Those records remain useful provenance and compatibility evidence, but they are
not the current ontology.

The canonical source extension remains **`.lisp`**. File extension is not
semantic identity.
