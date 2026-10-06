# D9 registry harvest v2 — 82 відновлені semantics

**Статус:** research / unratified  
**Issue:** #3979  
**Foundation:** #3960 / Contract 11.7

Джерело: ширший `lib/surface/semantic-registry.lisp`, але його старі 8-бітні координати повністю стерті з нового artifact.

## 132 рядки поза public-signature catalog

```text
SELECT-D9-CANDIDATE                  82
LOWER-DOMAIN-OR-CURRENT-PROJECTION   44
INTERNAL-NO-SLOT                      4
HOLD-SEMANTIC-REVIEW                  2
---------------------------------------
TOTAL                               132
```

Після цього D9:

```text
selected semantics          250/512
law-forced coordinates      128
unplaced selected           122
remaining                   262
ratified D9 residents         0
```

## Відновлені сімʼї

```text
GENERIC-DERIVED               8
SEQUENCE-ORDINAL              4
TIME-CALENDAR-DEADLINE       14
PERSISTENT-MAP                5
PERSISTENT-VECTOR             6
KNOWLEDGE-REASONING          16
UNIFICATION                   6
EPISTEMIC                    11
HOST-POLICY-WRAPPER           6
ANSWER-ALGEBRA                6
--------------------------------
TOTAL                        82
```

### Особливо важливе відновлення

`SECOND/THIRD/FOURTH/FIFTH` не зливаються з `CADR/...`.

Pair selector відповідає на питання про структуру cons-пари. Ordinal accessor відповідає на питання про позицію у лінійній послідовності. Архітектурний аудит прямо забороняє колапс `SECOND = CADR`.

Це хороший приклад правила D9: верхній домен відновлює semantic distinction, яку нижчий компактний домен міг не мати місця висловити окремо.

## Time boundary

Raw `mono-ns`, `unix-time-now`, `ntp-query-raw`, `timezone-declarations-raw` були залишені HOLD у #3977.

Натомість Lisp-owned policies з `lib/time.lisp` входять як D9 candidates:
- чисті calendar/deadline перетворення;
- language-level interpretation raw observations;
- public UTC/internet-time/timezone meaning.

Тобто:

```text
host observation mechanism != language time policy
```

## Host-backed public policy

`process-run`, TCP та file operations теж допускаються лише як **Lisp-owned public policy**. Raw host execution/bytes/socket/filesystem capability не стає D9 meaning.

## Не допускаються

44 rows — уже чинні lower/current meanings або projections.

4 internal helpers:
- largest-chunk
- nondecreasing-from?
- nonincreasing-from?
- digit->string

2 HOLD:
- invoke — post-semantics mechanism selection;
- binary — недостатньо визначений semantic law.

## Геометрія

Усі 82 нові meanings залишаються **UNPLACED**.

```text
semantic recovery != coordinate assignment
```

Жоден старий registry SID не переноситься в D9.
