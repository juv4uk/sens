# Поточна бінарно-доменна архітектура SENS

**Статус:** CURRENT EXPLANATORY MAP · 2026-10-03

Цей документ **пояснює**, але не створює семантичну владу. Якщо проза
суперечить ратифікованому owner-рішенню, машинному контракту або executable
witness — перемагає сильніше джерело. Починати перевірку треба з
[`CURRENT.md`](../CURRENT.md).

## 1. Канонічне правило

Поточна онтологія Core і Core-Math:

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Коротше:

```text
bits + domain + law -> meaning
```

Звідси випливають жорсткі заборони:

- однакові біти **не** означають однакову семантику;
- однакова ширина **не** означає один домен;
- однакова машинна формула **не** означає один семантичний закон;
- вільна координата **не** є функцією;
- opcode, enum, hash, AST, JSON, cache, registry row або людська назва не є
  канонічною identity лише тому, що вони зручні реалізації.

Позитивний і негативний executable controls:

- **#2502**: Core і Core-Math незалежно сходяться на selector-law для поточних
  generated D4/D5 descendants — bounded convergence;
- **#2509**: selector-path і exact-Q group-factor можуть використовувати
  однаковий механізм `child = 2*parent + bit`, але cross-domain apply дає
  `DOMAIN-MISMATCH`.

Тому правильна формула не `bits = meaning`, а саме
`bits + domain + law = meaning`.

## 2. Domain, carrier і mechanism — різні речі

Не змішувати:

```text
semantic domain  = law-bearing context
carrier/width    = скільки/які біти фізично несуть об'єкт
mechanism        = де і як це обчислюється/передається
```

Приклади:

```text
D7.SoundCell [carrier=W7]       # semantic domain
D7.LocalOrdinal [carrier=W7]    # інший semantic role/domain context
W7 / 7-bit                      # лише carrier
FPGA / Rust / radio / WASM      # mechanism
```

Width допомагає ідентифікувати exact binary object, але width сам по собі не
пояснює його сенс.

## 3. Core

Core — реконструкція й продовження лінії **Lisp I -> Lisp 1.5 -> SENS**.

Поточна дисципліна Core є historical-first:

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

Це означає:

```text
historically present != fundamental in SENS
derivable in SENS     != absent from historical record
```

Спочатку фіксуємо, що реально було в ранньому Lisp. Потім шукаємо families,
generators, axes, symmetries, derivability і lower bounds. Лише після цього
виводимо native SENS roots/coordinates/laws.

### Поточні доменні орієнтири

- **D1** — ratified PredicateBit: exact 1 bit, `0=NO`, `1=YES`;
- **D2** — ratified structural `racanā2`;
- **D3/D4** — ratified current Core foundation;
- **D5/D6** — **ratified widths/ontology**, але historical occupancy і final
  SENS semantics ще не вважаються завершеними;
- **D6 PURE-UNKNOWN** — untouched coordinates залишаються UNKNOWN, доки закон
  не заробить resident; free-space search заборонений;
- **D7** — ratified Sound7 + local śloka/sūtra ordinals; це **не** general
  arithmetic Number;
- **D14** — research: Pāṇini grammar як graph domain, не просто flat 14-bit
  table;
- **D24/D48/...** — research напрям arithmetic Number / FPGA-oriented exact
  numeric domains.

Parentless semantic root не отримує width/coordinate автоматично. Поточні
дослідження #2662/#2667/#2669 прямо перевіряють, яким законом такий root може
заробити exact domain. `free slot`, chronology або host metadata не є
доказом.

## 4. Core-Math

Core-Math — окрема математична дослідницька лінія. Вона **не зобов'язана**
успадковувати Lisp vocabulary, Core placement або Core execution structure.

Мінімальна машинна ідея:

```text
binary input(s)
+ admitted mathematical law
-> binary output
```

#2491 дає перший bounded `bits + law -> bits` witness. #2500 показує
exact-Q family/role factorization:

```text
family root
  + role bit
  -> inverse / quotient coordinate
```

При цьому сам exact 0/1 polarity не оголошується математично примусовим, якщо
falsifier цього не доводить.

Попередні experiments із AST/hash/certificate/cache не викинуті. Їхня роль
тепер чітка:

- proof/certificate — evidence/addressing;
- AST/JSON — research/tooling representation;
- hash — deterministic projection/index, якщо потрібен;
- cache — mechanism acceleration;
- registry row — mechanism/catalogue;
- **semantic identity** усе одно має bottom out у binary object + domain + law.

## 5. Core ↔ Core-Math

Дозволені три результати:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

Convergence не є метою за будь-яку ціну. Вона заробляється лише коли незалежно
збігаються:

```text
same binary object
+ same exact domain
+ same semantic equation
+ same law
+ independent cross-proof
```

#2502 — bounded positive control для selector composition.
#2509 — standing negative control: той самий bit transform у різних доменах не
створює convergence.

## 6. Generated, root, residue, UNKNOWN

Координата не стає resident через красу або вільне місце.

```text
generated child:
  exact parent + proved delta/generator -> candidate child

derived behavior:
  reconstructible from basis -> new resident may be unnecessary

parentless root:
  must independently earn exact domain/width

UNKNOWN:
  valid epistemic state
```

`UNKNOWN` — не дефект таблиці й не заклик “заповнити слот”. Негативний
результат теж є корисним research evidence.

## 7. Research task grammar

Поточний governed task має явно назвати:

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

Canonical phase values:

```text
HISTORICAL-INGEST
STRUCTURAL-DISCOVERY
SENS-DERIVATION
```

Core/Core-Math schema ratchets перевіряють форму й epistemic honesty, але не
ратифікують семантику автоматично.

## 8. Mechanism boundaries

Rust, FPGA, C, WASM, GraalVM, radio transport, packed wire, CRC/FEC/ARQ та
інші substrates/mechanisms не стають semantic authority.

Правильна межа:

```text
semantic SENS
-> exact-width binary object / canonical wire
-> mechanism / transport / substrate
-> observation
```

Наприклад RF frequency є шляхом через фізичний світ, а не шляхом у SENS
semantic tree.

## 9. Людські surfaces

Українські, англійські, санскритські й symbolic names — projections/UI.
Історичні Lisp names — provenance і human explanation.

Назва `CAR`, `ADD`, `Sound`, `Number` або `TRANSFORMER` сама по собі
не є canonical machine identity.

Canonical source extension проєкту — **`.lisp`**. Розширення файлу теж не є
семантикою.

## 10. Що читати

1. [`CURRENT.md`](../CURRENT.md) — current truth entry point.
2. [`docs/semantic-authority-map.md`](semantic-authority-map.md) — authority.
3. [`docs/language-core.md`](language-core.md) — Core/Core-Math model.
4. [`docs/benchmarks.md`](benchmarks.md) — current evidence/benchmark policy.
5. `docs/research/**` — dated evidence; не автоматично current authority.
6. GitHub owner/ratified issues referenced above — current scoped decisions.

## English summary

SENS currently uses a binary-domain ontology:

```text
semantic object = binary number + exact domain + proved law
```

Core reconstructs early Lisp first, discovers structure second, and derives
native SENS semantics third. Core-Math independently studies mathematical laws
over binary objects. The two may diverge, complement each other, or converge
only when binary object, domain, semantics and law independently agree.

Width is not semantics. A shared machine transform is not a shared semantic
law. Mechanisms such as Rust, FPGA, wire protocols, hashes, caches and human
names remain non-authoritative unless a separate admitted law says otherwise.
