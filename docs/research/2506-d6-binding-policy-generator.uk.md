# #2506 — D6 binding-policy generator witness

Статус: лише research.

## Domain record

```text
DOMAIN        Core D6 candidate family
BINARY OBJECT 0011 + два policy-refinement bits
LAW           незалежні комутативні binding-policy refinements
WITNESS       executable four-corner policy square
FALSIFIER     залежність / некомутативність / parent mismatch / collision
STATUS        hypothesis with executable witness
RELATION      Core-only
```

## Вхід із #2492

D4 `0011 DEFINE` і shared-location core відрізняються двома незалежно
спостережуваними policy:

```text
search scope:
  current
  nearest-existing

missing-binding policy:
  create
  fail
```

Тому one-bit D5 child уже відхилений.

## Candidate two-bit family

Executable square:

```text
00  current/create   = D4 DEFINE behavior
01  current/fail
10  nearest/create
11  nearest/fail     = shared-location core
```

Refinements:

```text
S: current -> nearest-existing
M: create  -> fail
```

Witness доводить:

```text
M(S(DEFINE)) = S(M(DEFINE)) = shared-location core
```

Обидві трансформації idempotent і commute.

Отже маємо чисту форму двобітного product-generator.

## Exact-width projection

Попередня D6-проекція:

```text
001100  00/base corner
001101  one-axis corner
001110  one-axis corner
001111  both-axis corner
```

Але semantic generation і residency — різні речі.

### 001100

Observationally identical до exact-width parent `0011 DEFINE`, тому не
заробляє новий resident лише через zero-padding.

### 001101 / 001110

Це добре визначені one-axis policies. Чи потрібні вони як first-class public
identities — окреме admission-питання.

При перестановці порядку осей їхні labels міняються місцями.

### 001111

Both-refinements corner не змінюється при перестановці осей і точно відповідає
доведеній shared-location capability.

Тому це найсильніший D6 coordinate **candidate**, але не ratified resident.

## Collision

D6 selector-law уже генерує:

```text
101000..101111
110000..110111
```

Усі `0011xx` candidate paths не перетинаються з цими 16 selector descendants.

## Межа

Witness не доводить:
- що кожен generated corner має бути public identity;
- що порядок axis є канонічним;
- що `001111` ратифікований;
- що Core-Math мусить повторювати цей family.

## Принцип

**Ширший word виправданий незалежними semantic dimensions лише коли їхні
transformations чисто композиційні; occupancy — окреме рішення.**
