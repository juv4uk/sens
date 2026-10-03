# Ядро мови SENS — бінарні домени, закони й докази

**Статус:** CURRENT EXPLANATORY DOCUMENT · 2026-10-03

Попередній SID8-only документ збережено в
[`docs/archive/language-core-sid8-only-superseded-2026-10-03.md`](archive/language-core-sid8-only-superseded-2026-10-03.md).

Цей документ пояснює поточну модель, але сам не створює semantic authority.
Див. [`../CURRENT.md`](../CURRENT.md) і referenced ratified/executable evidence.

## 1. Semantic object

Поточна owner-парадигма (#2490):

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Біти самі по собі не несуть значення.

Один і той самий bit string може легально існувати у двох доменах і означати
два різні semantic objects.

## 2. Domain, carrier і mechanism

Три шари треба тримати окремо:

```text
domain     = law-bearing semantic context
carrier    = concrete width/bit representation
mechanism  = executor/transport/substrate
```

Приклади:

```text
D7.SoundCell [carrier=W7]       semantic domain
D7.LocalOrdinal [carrier=W7]    інший semantic context
W7                              лише carrier
Rust / FPGA / RF                mechanism
```

Bare width недостатній для встановлення semantic domain.

## 3. Core

Core реконструює історичну Lisp-лінію перед native SENS derivation:

```text
Lisp I -> Lisp 1.5 -> later early-Lisp evidence
```

Порядок дослідження (#2533):

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

Historical inventory не можна стирати, навіть якщо SENS пізніше виводить або
стискає операцію.

### Поточний status доменів

| Domain | Поточний status |
|---|---|
| D1 | ratified PredicateBit |
| D2 | ratified structural racanā2 |
| D3 | ratified Core foundation |
| D4 | ratified Core foundation |
| D5 | ratified width/domain ontology; occupancy ще досліджується |
| D6 | ratified width/domain ontology; багато coordinates лишаються UNKNOWN |
| D7 | ratified Sound7 + local śloka/sūtra ordinals; не arithmetic Number |
| D14 | research candidate: Pāṇini grammar graph |
| D24/D48/... | research candidates: exact Number / FPGA-friendly numeric domains |

Ratified width не означає blanket occupancy.

## 4. Generated descendants

Generated child може заробити candidate identity через exact parent + admitted
local generator:

```text
parent
+ delta / generator
-> generated child
```

Selector composition — найсильніший current positive control.

Для selector-path coordinate додавання semantic projection choice може
узгоджуватись із binary relation:

```text
E(extend(s,b)) = 2*E(s) + b
```

Але arithmetic formula сама по собі не є semantic law. Semantic law тут —
selector composition. #2502 незалежно cross-proves current generated D4/D5
selector descendants через Core-Math executor.

## 5. Parentless roots і residue

Semantic root **не** заробляє width через free space.

Розділяємо:

```text
roothood
width/domain membership
coordinate placement
```

Це три різні claims.

Для parentless root:

- roothood може бути proved;
- exact width може лишитися UNKNOWN;
- coordinate може лишитися UNPLACED.

#2662/#2667/#2669 досліджують, як parentless root чесно заробляє exact domain.

## 6. D6 PURE-UNKNOWN discipline

Unknown coordinates — не дефект inventory.

PURE-UNKNOWN D6 coordinate може покинути цей клас лише після same-base semantic
law, lower-bound theorem або іншого admitted placement evidence.

Заборонені placement arguments:

- free capacity;
- numeric adjacency;
- attractive bit pattern;
- chronology alone;
- Core-Math authority без bridge/domain proof;
- mechanism-local metadata.

Успішний research result може бути **NO-CANDIDATE**.

## 7. Core-Math

Core-Math досліджує математичні закони над binary objects незалежно від Core.

Мінімальна execution-ідея:

```text
binary input(s)
+ admitted mathematical law
-> binary output
```

Ключове evidence:

- #2491 — перший bounded `bits + law -> bits` executor;
- #2500 — exact-Q family/role factorization;
- #2509 — same machine transform у різних domains не зливає semantics.

Core-Math може diverge від Core і не успадковує Core placement автоматично.

## 8. Core / Core-Math relation

Допустимі результати:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

Convergence вимагає незалежного збігу:

```text
binary object
+ exact domain
+ semantic equation
+ law
+ cross-proof
```

Matching syntax, human names, hashes, ASTs, storage layouts або machine formula
недостатньо.

## 9. Human surfaces

Human names — source/UI projections.

До них належать:

- українські;
- English;
- Sanskrit;
- symbolic spellings;
- historical Lisp names.

Назва допомагає людині обговорювати об'єкт, але не замінює binary-domain
identity.

Canonical source extension лишається **`.lisp`**. File suffix не є semantic
identity.

### Source/implementation compatibility

- Канонічне розширення вихідного коду — **`.lisp`**.
- `.wsm` і `.my` — **legacy aliases** для compatibility/history; вони не створюють окремої semantic identity.
- Rust — **референсна реалізація** поточного runtime/mechanism layer, а не власник semantics.

## 10. Execution substrates

Rust — current reference mechanism, не semantic authority.

Те саме стосується:

- C;
- Common Lisp;
- WASM;
- GraalVM;
- FPGA;
- GPU;
- Prolog / Datalog / CLIPS;
- radio/wire transports.

Mechanism може виконувати або переносити admitted object. Він не має права
непомітно mint-ити нове language meaning.

## 11. Wire і packed representation

Packed/wire representation зберігає exact payload і boundaries. Воно не
створює semantic domain.

Conceptual layering:

```text
semantic object
-> canonical SENS wire/container
-> transport framing
-> physical channel
```

CRC, FEC, ARQ, frequency, modulation і RF profile — transport mechanisms.

## 12. Governed research record

Поточна task grammar:

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

Allowed PHASE:

```text
HISTORICAL-INGEST
STRUCTURAL-DISCOVERY
SENS-DERIVATION
```

Schema робить uncertainty явною, але не auto-ratify-ить semantics.

## 13. Historical SID8

Попередня flat 256-slot SID8/Function8 модель лишається:

- historical provenance;
- compatibility evidence;
- migration donor;
- falsifier проти випадкового повернення до flat identity.

Вона **не** є current ontology.

## 14. Межа проєкту

SENS володіє admitted semantic meaning.

Reference implementations, generated files, benchmarks, surfaces, proof-address
formats і caches лишаються evidence/mechanism нижчого рівня, якщо окремий law
не встановив інше.

Authority precedence:
[`semantic-authority-map.md`](semantic-authority-map.md).

## English · auxiliary

The current SENS model is:

```text
semantic object = binary number + exact semantic domain + admitted law
```

Core reconstructs historical Lisp first, discovers structure second, and
derives native SENS semantics third. Core-Math independently studies
mathematical laws over binary objects. Domain, carrier and mechanism are
separate; free coordinates remain unassigned until a law earns placement.
