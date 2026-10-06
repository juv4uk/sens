# D9 semantic inventory — 148/512

**Статус:** research / unratified  
**Parent:** #3964  
**Inventory task:** #3965  
**Foundation:** #3960 / Contract 11.7

Перші D9 кандидати тепер зібрані в одну machine-readable таблицю:

`knowledge/d9-v1-semantic-inventory.json`

## Поточний стан

```text
selected semantics          148/512
law-forced coordinates      128
unplaced selected            20
remaining                   364
ratified D9 residents         0
```

128 selector descendants мають law-forced 9-bit coordinates. 20 нових semantics із D8 overflow уже відібрані як meaning, але навмисно залишені без coordinates.

Це розділяє два питання:

```text
що означає resident candidate?
!=
де саме він стоїть у D9?
```

Наступний етап — добрати ще 364 distinct meanings і паралельно шукати локальні закони (#3970), але не gauge-fixити простір завчасно.
