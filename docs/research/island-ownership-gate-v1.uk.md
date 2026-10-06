# D9/D10 та execution islands — ownership gate

**Authority:** #4033  
**Статус:** P0 reconciliation

SENS уже має чотири автономні execution islands:

```text
Common Lisp
Prolog
CLIPS
Datalog
```

Головна межа:

```text
SENS owns the language + explicit border
islands own their native reasoning/execution semantics
```

## Що виявив аудит

D9 вже ратифікований (#4008 / Contract 11.8), тому його не можна тихо переписати.

У чинній 512/512 карті:

```text
definite island/package-owned  136
experiment-needed               70
```

До definite входять:
- Prolog: reason + unification;
- CLIPS: forward/JTMS + CLIPS import tooling;
- Datalog/package: knowledge journal;
- packages: world, persistent map, persistent vector.

D10 поки research, але вже має:

```text
definite ownership conflicts    55
experiment-needed               15
```

Тому D10 отримує ratification blocker.

## Що Core може мати

Core може володіти:
- island selector;
- raw/opaque invoke;
- explicit partial projection;
- opaque result/reference;
- provenance;
- failure/result-cardinality protocol.

Це **bridge semantics**.

Core не повинен дублювати:
- Prolog resolution/unification;
- CLIPS rule engine / JTMS;
- Datalog fixpoint/relational storage;
- Common Lisp library algorithm лише тому, що runtime доступний.

## Що робимо з уже напрацьованим

Нічого не видаляємо.

Для кожного row зберігаємо:
- stable id;
- current coordinate (для D9);
- law/witness;
- source file;
- target island/package;
- ownership classification.

Міняється не історія роботи, а її **власник**.

## D9

D9 уже ратифікований. Цей аудит не змінює жодної координати.

Наступний крок для D9 — owner-amendment plan:
1. визначити, які 136 definite rows мають стати island/package capability evidence;
2. знайти справжні Core bridge semantics або інші Core meanings для заміни;
3. окремо вирішити 70 experiment-needed rows;
4. тільки після явного owner-рішення змінювати Contract 11.8 / карту.

## D10

D10 ще не ратифікований, тому gate діє одразу:
- нові rows з definite non-Core sources заборонені;
- існуючий борг може тільки зменшуватися;
- unknown/experiment-needed потребує ownership witness;
- D10 ratification заблокована, поки definite conflicts > 0.

Machine-readable audit: `knowledge/island-ownership-gate-v1.json`.
