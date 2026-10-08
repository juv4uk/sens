# Archipelago v1 — карта семантичної власності

**Статус:** current architecture  
**Authority:** #4140  
**Foundation:** D1–D9 owner-ratified #4008 / Contract 11.8  
**D10:** research / unratified

## Головна ідея

SENS не повинен поглинати кожний алгоритм, який існує в авторських репозиторіях.

```text
SENS Core
  = semantic identity + laws + explicit border

islands / packages / substrates
  = native execution, reasoning, domain algorithms, mechanisms
```

Core володіє мостом. Острів володіє своїм світом.

## Core border

У D10 зараз факторизовано рівно шість універсальних bridge meanings:

```text
ISLAND-CALL
EXECUTION-WITNESS
NATIVE-OBSERVATION
RESULT-COUNT
BRIDGE
MISSING-CAPABILITY
```

Вони не визначають Prolog, CLIPS, Datalog або Common Lisp. Вони визначають лише чесну межу між SENS і автономним producer.

## Чотири execution islands

### Common Lisp

Володіє native Lisp execution/runtime result model. Core не отримує semantic identity лише тому, що SBCL може щось виконати.

### Prolog

Володіє unification, search, backtracking, substitution streams і 0..N answers. SENS не перетворює 0 substitutions на універсальне FALSE.

### Datalog

Володіє relations, tuple sets, fixpoint / closure. Порожнє relation не є автоматично Canon 0 або FALSE.

### CLIPS

Володіє facts, working memory, agenda, production rules і native rule-engine/JTMS observations. Core не дублює цей engine під іншими іменами.

## Package/domain islands

D10 cleanup уже виніс за Core:
- knowledge/Datalog package;
- world simulation;
- linguistic/translation;
- science/core-math dimensions.

Це не видалення роботи. Семантика, witnesses і provenance зберігаються, але власник змінюється.

## Backend/substrate islands

Компіляторні й апаратні репо на кшталт cml, fpga-lisp, sens-futhark, wsm-cuda, wsm-graalvm, wsm-os та wsm-target-contract володіють mechanism/substrate semantics.

Opcode, register, ABI, CUDA driver, FPGA wire або Graal implementation detail не стає Core resident. Вони можуть дати Core лише універсальний seam law, якщо він доведений незалежно від конкретного backend.

## Усі авторські репо

`knowledge/d10-owner-repo-donor-matrix-v2.json` містить 87 доступних `juv4uk/*` репо.

Archipelago v1 розкладає їх точно по одній зоні:

```text
CORE-DONOR          1
HISTORICAL-DONOR    9
PACKAGE-ISLAND     33
SUBSTRATE-ISLAND   11
REFERENCE-WATERS   33
---------------------
TOTAL              87
```

`REVIEW-REQUIRED` у зеленому стані не допускається.

## D10 ownership gate

Поточний стан:

```text
D10 selected              625/1024
law-forced                256
unplaced                  369
remaining                 399
ratified                    0

definite non-Core selected  0
review-required selected    0
Core bridge meanings        6
```

Отже D10 зараз ownership-clean.

## Правило наступного заповнення D10

Кандидат із острова, package або backend не потрапляє в Core напряму.

```text
native/package/backend behavior
        ↓
ownership review
        ↓
чи існує substrate-independent universal border law?
        ├─ ні  -> лишається острову/package/backend
        └─ так -> окремий Core candidate
```

## Принцип

```text
Core не є материком, який поглинає острови.

Core — це карта, закони кордонів і мости.
Острови зберігають власну семантику та native result model.
```

Machine-readable authority: `knowledge/archipelago-map-v1.json`.
