# Карта семантичної влади SENS

**Статус:** CURRENT ARCHITECTURE MAP · 2026-10-03

Головне правило:

> **Значення допускається через domain + law + evidence. Реалізація, назва, storage або transport не мають права тихо стати сильнішими за це.**

Детальна англійська/current карта:
[`semantic-authority-map.md`](semantic-authority-map.md).

## Поточна identity

Owner paradigm #2490:

```text
semantic object
=
binary number
+ exact semantic domain
+ proved/admitted law
```

Тому:

```text
bits alone          != meaning
width alone         != semantic domain
machine transform   != semantic law
human name          != canonical identity
free coordinate     != resident
hash/cache/registry != semantic authority
```

## Порядок сили тверджень

Для відповідного scope:

1. explicit owner/ratified decisions;
2. machine-readable contract / admitted laws / conformance;
3. executable witnesses і falsifiers;
4. reference/independent implementations;
5. generated projections і current documentation;
6. dated research/history/archive.

Старіший machine-readable artifact, який ще не мігрований під новішу explicit
ratification, є migration debt, а не правом скасувати owner decision.

## Domain, carrier, mechanism

#2540:

```text
domain     = law-bearing semantic context
carrier    = bits/width representation
mechanism  = execution/storage/transport
```

Наприклад:

```text
D7.SoundCell [carrier=W7]
D7.LocalOrdinal [carrier=W7]
```

Однакова W7 не робить ці об'єкти одним semantic domain.

## Core

Core працює historical-first:

```text
HISTORICAL-INGEST
        ↓
STRUCTURAL-DISCOVERY
        ↓
SENS-DERIVATION
```

History дає observations. Structure дає laws. SENS виводиться після цього.

## Placement

Координата заробляється законом.

Допустимі джерела:

- exact parent + generator;
- lower-bound theorem;
- independent root/domain law;
- explicit ratification із evidence.

Недопустимі заміни:

- free slot;
- numeric proximity;
- красивий bit pattern;
- chronology alone;
- host metadata;
- foreign-domain transform.

## Parentless roots

```text
PROVEN-ROOT
!=
PROVEN-WIDTH
!=
PROVEN-COORDINATE
```

Root може лишатися `domain=UNKNOWN`, `coordinate=UNPLACED`.

## Core-Math

Core-Math має власну mathematical authority:

```text
binary input(s)
+ admitted mathematical law
-> binary output
```

Він не успадковує Core placement автоматично.

## Cross-domain firewall

#2508/#2509:

Два domains можуть використовувати той самий mechanism:

```text
child = 2*parent + bit
```

і все одно мати різні semantic laws.

Cross-domain apply має fail closed.

## Convergence

#2495 допускає:

```text
DIVERGENT
COMPLEMENTARY
CONVERGENT
```

Convergence потребує:

```text
same binary object
+ same exact domain
+ same semantic equation
+ same law
+ independent cross-proof
```

#2502 — bounded selector positive control.

## Mechanisms

Rust, FPGA, C, WASM, GPU, caches, ASTs, hashes, wire, radio, CRC/FEC/ARQ —
mechanisms/evidence, не semantic authority.

## Human surfaces

Українські, English, Sanskrit, symbols і historical Lisp names — projections.
Вони допомагають людині, але не визначають machine identity.

## Документаційне правило

Current prose мусить відрізняти:

- ratified;
- bounded witness;
- hypothesis;
- falsified;
- UNKNOWN/UNRESOLVED;
- historical.

Старі research документи не переписуються заднім числом. Вони архівуються або
чітко маркуються, а current layer оновлюється окремо.

Див. також:

- [`../CURRENT.md`](../CURRENT.md)
- [`current-binary-domain-architecture.md`](current-binary-domain-architecture.md)
- [`language-core.md`](language-core.md)
