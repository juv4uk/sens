# #2703 — Семантичне розміщення 19 історичних рядків після D4

Фаза: **SENS-DERIVATION**

Цей звіт розміщує всі 19 завершених історичних рядків у semantic owner graph.
Нових binary residents він **не** створює.

## Уже зведені derived/mechanism рядки

| Історичний рядок | Семантичне місце | Binary residency |
|---|---|---|
| LABEL | D4 LAMBDA, closure/fixed-point recursion | немає |
| FUNCTION | D4 LAMBDA, closure representation | немає |
| FUNARG | D4 LAMBDA + APPLY, closure application | немає |
| EVALQUOTE | композиція D4 EVAL + APPLY | немає |
| APPEND | D3 structural recursion | немає |
| PAIR | D3 structural recursion | немає |
| PAIRLIS | D3 structural recursion над явним environment tail | немає |
| ASSOC | D3 structural search/equality recursion | немає |
| SUBST | D3 tree recursion | немає |
| SUBLIS | D3 tree recursion + derived ASSOC | немає |
| MAPLIST | D4 higher-order application + D3 list traversal | немає |
| GO | D1-D4 finite-state dispatch + tail recursion | немає |

Важливі негативні розміщення:
- PAIRLIS **не** є child від BIND;
- ASSOC **не** є child від LOOKUP;
- історичні назви зберігаються як provenance, а не як нові residents.

## Семантичні області, що вижили після D4

| Історичний рядок | Семантична область | Поточне розміщення |
|---|---|---|
| SET | shared-location carrier | UNPLACED |
| SETQ | shared-location carrier + quoted-target policy | **РАТИФІКОВАНИЙ Core D6 001111** за #2538 OD-001 / #2723 |
| PROG | composite з derived GO + non-local RETURN | окремий resident не потрібний |
| RETURN | доведений non-local-exit root | width UNKNOWN, UNPLACED |
| FEXPR | raw-form + caller-env + invocation carrier family | UNPLACED |
| FSUBR | raw-form + caller-env + invocation carrier family | UNPLACED |
| TRANSFORMER | raw-form carrier + returned-form/timing policy | UNPLACED |

## Наслідок для D5

Завершений D5 closeout лишається незмінним:

```text
selector-generated = 8
UNKNOWN/free       = 24
manual non-selector residents = 0
new non-selector D5 candidates = 0
```

Отже semantic placement означає **помістити історичний рядок під механізм або
сімейство, яке його пояснює**, а не витратити вільний код.

## Наслідок factor/root minimization

Сім post-D4 structural facts зведені до:

```text
PROVEN-ROOT:
  non-local-exit

CARRIER-PREMISE:
  shared-location-update
  raw-form-input
  explicit-caller-env
  invocation-packaging

POLICY-OVER-ROOT/CARRIER:
  returned-form-protocol
  expansion-timing
```

Roothood усе ще не визначає exact width.

## Відтворення

```sh
python3 benchmarks/post-d4-semantic-placement/run.py --out /tmp/post-d4-placement
```

Очікувано:

```text
POST-D4-SEMANTIC-PLACEMENT=PASS
HISTORICAL-ROWS=19
NEW-D5-RESIDENTS=0
D5=8-generated+24-UNKNOWN
RETURN=PROVEN-ROOT-UNPLACED
SETQ-D6-001111=RATIFIED-RESIDENT
```

## Принцип

**Історична операція може мати точне місце в semantic graph і водночас не
потребувати власного binary resident.**
