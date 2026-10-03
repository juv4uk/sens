# SENS vision — from historical Lisp to law-governed binary domains

**Status:** CURRENT VISION · 2026-10-03

The previous Advice-Taker/NLP-centered vision is preserved at
[`docs/archive/vision-advice-taker-superseded-2026-10-03.md`](archive/vision-advice-taker-superseded-2026-10-03.md).

## Українська

### 1. Мета

SENS досліджує мову, де машинний semantic object не залежить від людської
назви, opcode або таблиці слотів.

Поточна цільова формула:

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Ми шукаємо не “гарну нумерацію функцій”, а закони, які **змушують** структуру
домену.

### 2. Core: від історії до теорії

Core не починає з чистого аркуша. Він реконструює ранній Lisp як емпіричний
матеріал:

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

Ідея проста:

- історія дає observations;
- структура знаходить families/generators/independent axes;
- SENS виводить мінімальні roots/laws/domains після цього.

Тому історична функція може лишатися в historical ledger навіть якщо SENS
пізніше доведе, що вона generated або derived.

### 3. Core-Math: математика над binary objects

Core-Math іде іншим шляхом. Він питає:

> які binary objects і operations математично примушені законами, незалежно від Lisp vocabulary?

Мінімальна машина:

```text
bits + domain + law -> bits
```

Core-Math може генерувати нові binary objects із законів, але не зобов'язаний
мати ті самі domains або coordinates, що Core.

### 4. Де Core і Core-Math зустрічаються

Ми не форсуємо єдність.

Допустимі результати:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

Зустріч вважається справжньою лише коли незалежно збігаються:

```text
binary object
domain
semantic equation
law
cross-proof
```

Selector composition уже має bounded positive convergence witness.
Same-transform/different-domain має bounded negative witness.

### 5. Exact domains замість “вільних слотів”

Координата не отримує значення, бо вона порожня.

Ми хочемо, щоб resident заробляв місце через:

- generator;
- lower bound;
- independent root/domain law;
- ratified exact evidence.

Якщо доказу немає, **UNKNOWN/UNPLACED** є правильною відповіддю.

### 6. Доменна карта

Поточний напрям:

```text
D1        PredicateBit
D2        structural racanā2
D3/D4     ratified Core foundation
D5/D6     ratified widths; historical/structural filling continues
D7        Sound7 + local textual ordinals
D14       Pāṇini grammar graph research
D24/D48…  exact Number / FPGA-oriented research
```

Це не означає, що кожна координата всередині width уже має сенс.

### 7. Hardware і transport

FPGA/GPU/Rust/C/WASM/radio — важливі, але вони механізми.

Мета:

```text
same semantic object/law
        ↓
multiple execution substrates
```

а не:

```text
hardware opcode -> language meaning
```

Exact-width binary domains природно цікаві для FPGA, але hardware convenience
не може бути доказом semantic placement.

### 8. Самоопис і proof

Proofs/certificates важливі як evidence й addressing. Але proof format, hash,
AST або JSON не стають semantic identity автоматично.

Для parentless roots зараз окремо перевіряється, чи proof-address може бути
semantic domain, чи лишається certificate-only. Відповідь не передбачається.

### 9. Наука замість догми

Сильний SENS task повинен мати:

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

Проєкт вважає успіхом не лише підтвердження, а й:

- falsification;
- NO-CANDIDATE;
- UNKNOWN;
- divergence;
- доказ того, що красивий bit pattern є лише механізмом.

### 10. Довга перспектива

Якщо підхід працює, SENS має стати мовою, де:

- значення не прив'язане до однієї людської поверхні;
- функції/операції виникають із domain laws, а не з ручної таблиці;
- machine representation є компактною й exact;
- execution переноситься між CPU/FPGA/іншими substrates без зміни semantic law;
- історичні мови, математика й hardware можуть незалежно давати докази одній структурі.

Але convergence має бути **заробленою**, не запроєктованою наперед.

## English summary

SENS is moving from a flat function-table mindset toward a law-governed
binary-domain language model:

```text
semantic object = binary number + exact domain + admitted law
```

Core reconstructs early Lisp first, discovers structure second, and derives
native SENS semantics third. Core-Math independently studies mathematical laws
over binary objects. They may diverge, complement each other, or converge only
where independent evidence forces the same object/domain/semantics/law.

Unknown coordinates remain unknown. Mechanisms such as Rust, FPGA, hashes,
caches, ASTs, wire formats and RF profiles remain non-authoritative.

The long-term vision is not a larger table of opcodes. It is a language whose
binary structure is explained by reusable laws.
