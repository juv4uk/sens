# #1962 — LISP I → LISP 1.5: від плоскої таблиці до prefix-графа

**Статус:** research-only, не semantic authority, без production migration.
**Branch:** `research/1962-lisp1-15-domain-graph`.

## Поточна модель після owner pivot 2026-10-01

Початкова гіпотеза цього PR була:

```text
D3 = QUOTE / COND / LAMBDA / LABEL
mūla4 = ATOM / EQ / CAR / CDR / CONS
```

Вона **більше не є current hypothesis**. Важливе виправлення цього звіту:
пізніше тут помилково повторили стару перестановку імен. Поточне канонічне
джерело — `lib/domains/d3.lisp`; його ратифікована карта:

```text
000  ()
001  QUOTE
010  ATOM
011  CDR
100  CAR
101  EQ
110  COND
111  CONS
```

Це рівно один ground-value і сім конститутивних операцій:

```text
1 ground + 7 constitutive operations = 8 = 2^3
```

Раніше наведена в цьому звіті перестановка
`011 EQ / 100 CONS / 101 CAR / 110 CDR / 111 COND` є
**застарілим дослідницьким артефактом, не D3-авторитетом**. Жодна
канонічна таблиця не змінюється заради узгодження старого документа.

Старі перші вісім 8-бітних записів
`00000000..00000111` у цьому research трактуються лише як
zero-padded projection історичного зерна, а не як доказ плоскої
256-функціональної ontology.

## Гіпотеза prefix-графа

Для слова довжини більше 3:

```text
parent(code) = code без останнього біта
children(p)  = p0, p1
```

Але дуже важлива межа:

> prefix-parent ще НЕ дорівнює semantic derivation.

Він може означати:
- композиційного предка;
- семантичну сім'ю;
- allocation ancestry;
- іншу typed relation.

Це має визначатися evidence окремо для кожного піддерева.

## Знахідка 1 — CAR/CDR дають точне бінарне дерево без ручної таблиці

Це перший сильний позитивний witness.

Ортогональна до dependency-схеми selector-гілка спирається на
два **поточні D3 residents**, не на старі номери:

```text
100 -> CAR
011 -> CDR
```

У чинних D4/D5 таблицях продовження selector-сім'ї узгоджується з цими батьками:

```text
1000   CAAR
1001   CADR
0110   CDAR
0111   CDDR

10000  CAAAR
10001  CAADR
10010  CADAR
10011  CADDR

01100  CDAAR
01101  CDADR
01110  CDDAR
01111  CDDDR
```

Тут кожен доданий біт вибирає A- або D-проєкцію всередині попереднього
selector. Це compositional meaning, а не дозвіл переприсвоювати координати:
перевіряти його треба проти канонічних `lib/domains/d3.lisp`,
`lib/domains/d4.lisp` і `lib/domains/d5.lisp`.

Для selector subtree на ширині `n >= 3`:

```text
count(n) = 2^(n-2)
```

і всі імена унікальні.

`scripts/research-1962-prefix-tree.py` це перевіряє executable.

### Чому це важливо

Ми отримали перший приклад, де:

```text
довший binary word
=
точно один додатковий semantic/compositional step
```

Це саме та властивість, яку шукали в теорії графів/зв'язків.

## Знахідка 2 — primary і derived справді можуть жити на одній ширині

Ширина більше не кодує жорсткий клас
`primitive -> primary -> derived`.

Наприклад, на 4 бітах:
- `CAAR/CADR/CDAR/CDDR` уже є **derived**;
- водночас `LAMBDA/LABEL` можуть виявитися **primary** вузлами іншої
  4-бітної сім'ї.

Отже:

```text
bit width = depth/address in prefix graph
semantic role = independent node property
```

Це сильніше й простіше за попередню role-per-width модель.

## Знахідка 3 — evaluator SCC не визначає бітність

Dependency corpus лишається корисним як другий тип графа.

LISP I:

```text
{eval, evcon, evlis}
```

утворюють multi-node SCC, а `apply` стоїть над ним.

LISP 1.5:

```text
{apply, eval, evcon, evlis}
```

вже є одним SCC.

Отже recursive topology evaluator-а змінюється між двома історичними
реалізаціями. SCC потрібні для аналізу, але вони не є кодовим доменом
самі по собі.

## Знахідка 4 — reachability і named depth недостатні

Старі Model A/B лишаються як falsification evidence:

- named dependency depth змінюється від helper refactoring;
- transitive derivability сплющує майже все до того самого seed basis.

Тому prefix allocation не можна виводити лише з call graph.

Потрібні **два ортогональні графи**:

```text
A. dependency / derivability graph
B. prefix / family graph
```

а потім доказаний міст між ними:

```text
prefix edge --[typed evidence]--> semantic relation
```

## Перші кандидати для інших seed families

Це НЕ allocations; лише напрям перевірки.

```text
000 ()     -> NULL?                         medium; multi-root dependency
001 QUOTE  -> LAMBDA / LABEL?               medium; representation/binding family
010 ATOM   -> type predicates?              open
011 CDR    -> CDAR / CDDR                   PROVEN selector composition
100 CAR    -> CAAR / CADR                   PROVEN selector composition
101 EQ     -> EQUAL / MEMBER?               medium; equality/search family
110 COND   -> AND / OR / NOT / implication  historical derivability; binary placement open
111 CONS   -> LIST / APPEND?                medium-to-strong construction family
```

Головне правило: **не заповнювати порожній child лише заради симетрії**.

## Первинні джерела

- *LISP I Programmer's Manual*, MIT, March 1960:
  Chapters 2 and 4; manual explicitly says the central core is built
  from five elementary functions/predicates by composition,
  conditional expressions, and recursive definitions.
- *LISP 1.5 Programmer's Manual*, MIT, 1962:
  §1.2 elementary functions; §1.6 universal `evalquote`;
  pp. 18–21 derived list helpers and evaluator.
- J. McCarthy, *Recursive Functions of Symbolic Expressions and Their
  Computation by Machine, Part I*, CACM 1960.

Внутрішні донори:
`ecosystem/docs/correspondence/mccarthy-1960-eval-apply-*`,
`ecosystem/docs/correspondence/manus-ai-mylisp-vs-lisp15-*`,
`ecosystem/memory/mccarthy-eval-x86-64-prototype.md`.

## Артефакти

- `1962-lisp1-15-nodes.tsv` — seed/prefix/node roles;
- `1962-lisp1-15-edges.tsv` — typed dependency evidence;
- `scripts/research-domain-graph-1962.py` — SCC + dependency diagnostics;
- `1962-lisp1-15-prefix-tree.txt` — prefix research corpus;
- `scripts/research-1962-prefix-tree.py` — executable selector theorem;
- `1962-lisp1-15-first-run.txt` — generated diagnostic snapshot.

## Наступний крок

1. Зберегти `bīja3` незмінним як research premise.
2. Для кожного з шести ще не доведених seed families шукати **локальний
   закон породження**, а не красиву пару назв.
3. Приймати 4-бітне призначення лише якщо prefix-parent має stable
   typed meaning на Lisp I і Lisp 1.5.
4. Перевірити, чи 5-бітні descendants продовжують той самий закон.
5. Якщо family не має природної binary expansion — лишити child
   unallocated, а не ламати модель.

## Принцип

**Код має не просто називати вузол. Там, де це можливо, доданий біт має
нести ще один доведений зв'язок.**
