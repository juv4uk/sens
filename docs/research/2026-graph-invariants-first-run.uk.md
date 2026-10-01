# #2026 — name-erased typed graph invariants, перший прогін

Статус: лише дослідження на корпусі Lisp I / Lisp 1.5 із #1962.

## Вхід

- 34 semantic/research nodes;
- 129 typed directed edges;
- поточні relation types: `composition`, `structure`, `derivable`, `recursion`, `calls`.

Primary refinement навмисно не використовує:
- людські назви вузлів як color input;
- seed3/prefix binary codes;
- historical slot numbers.

Додаткові режими додають лише non-name research metadata (`kind`, `era`, `prefix_evidence`).

## Перший результат

```text
mode                    classes  unique  collision cells
topology                   32       30       2
kind                       32       30       2
kind+era                   32       30       2
kind+era+evidence          32       30       2
```

У всіх name-erased режимах виживають ті самі дві collision cells:

```text
{lambda, label}
{caddr, cdar}
```

Обидві пари також є exact swap automorphisms поточного typed graph.

Call/recursion subgraph відтворює очікувані non-trivial SCC:

```text
{eval_lisp1, evcon_lisp1, evlis_lisp1}
{apply_lisp15, eval_lisp15, evcon_lisp15, evlis_lisp15}
```

## Сильний falsifier 1 — втрачено порядок композиції

`CADDR` і `CDAR` — семантично різні selector compositions.

Поточний graph записує їх generic `composition` relations до CAR/CDR, але не зберігає достатньо order/multiplicity information, щоб розрізнити:

```text
CADDR = CAR ∘ CDR ∘ CDR
CDAR  = CDR ∘ CAR
```

Отже:

> unordered typed dependency graph недостатній як self-description proof substrate для selectors.

Це не аргумент додати names або bit codes. Це аргумент, що relation kernel потребує **ordered proof/generator relation** або еквівалентного certificate там, де порядок є семантикою.

Тобто:

```text
dependency graph
!=
canonical semantic proof path
```

## Сильний falsifier 2 — binding semantics описані недостатньо

`LAMBDA` і `LABEL` залишаються exact structural swap automorphisms навіть із `kind/era/prefix_evidence` metadata.

Поточний graph не містить факту, який пояснює різницю між:
- ordinary binding/function abstraction;
- recursive naming/binding.

Правильна реакція — не tie-break через name.

#2023 має вивести мінімальний relation/evidence, який представляє цю реальну semantic distinction, а не просто призначити код англійській назві relation.

## Важливий позитивний результат

30 із 34 corpus nodes стають структурно унікальними через typed refinement без names і binary codes.

Отже поточні typed relations уже несуть значну частину semantic information.

Але structural uniqueness — це лише distinguishability evidence, не доказ semantic identity, necessity або canonicality.

## Automorphism result

У stable WL cells bounded search знаходить рівно чотири automorphisms:

```text
identity
swap(lambda,label)
swap(caddr,cdar)
swap both pairs
```

Тому ці collision — не просто слабкість конкретного WL algorithm. Це справжні symmetry поточного typed graph.

## Наслідок для self-description

Self-describing SENS graph зараз бракує щонайменше:

1. ordered/multiplicity-sensitive construction evidence для selector composition;
2. реальної semantic distinction між recursive і non-recursive binding forms.

Generic `depends-on` relation для цього недостатньо.

## Наслідок для #2034 automaton countermodel

Execution-state minimization може зливати control states при різних semantic identities.

Graph self-description — ні.

Тому automaton-state equivalence та semantic-graph equivalence мають залишатися різними поняттями.

## Принцип

**Якщо два значення є exact automorphisms name-erased graph, graph ще не містить факту, який їх розрізняє.**
