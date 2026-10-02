# #2344 — історичний ledger можливостей Lisp I -> Lisp 1.5

Статус: ledger дослідницьких доказів, не семантична влада мови.

Питання строго хронологічне:

> після вилучення всього, що вже представлено або виводиться з D1-D4,
> яка перша нова спостережувана можливість лишається?

Машинне джерело:

```text
docs/research/2344-post-d4-historical-ledger.json
```

Валідатор:

```text
scripts/research-2344-historical-ledger.py
```

## Поточні завершені рядки

```text
LABEL       DERIVED-D1-D4
FUNCTION    HISTORICAL-MECHANISM
FUNARG      HISTORICAL-MECHANISM
EVALQUOTE   DERIVED-D1-D4
PAIRLIS     DERIVED-D1-D4
```

Важливий негативний результат:

```text
PAIRLIS != current BIND
```

Історичний PAIRLIS зберігає порядок пакета параметрів/значень, а поточний
C1-BIND цей пакет розвертає. Водночас PAIRLIS повністю є структурною
рекурсією, тому схожість ролі не дала BIND батьківства і не породила нового
ідентифікатора.

## Навмисно нерозв'язані

Ledger не приховує прогалини:

```text
APPEND
PAIR
ASSOC
SUBST
SUBLIS
MAPLIST
SET / SETQ
PROG / GO / RETURN
FEXPR / FSUBR
TRANSFORMER
```

PAIR навмисно лишено UNRESOLVED, хоча він здається очевидним: #2286 довів
PAIRLIS, але не окремий executable witness для PAIR. Ledger має показувати цю
різницю, а не перетворювати інтуїцію на доказ.

## Механічні правила

Завершений рядок мусить:
- мати класифікацію, відмінну від UNRESOLVED;
- містити повний 40-символьний git commit;
- посилатися на commit, що реально існує в історії репозиторію;
- явно відповісти про hidden state, caller environment та one-new-delta.

Нерозв'язаний рядок:
- не може приписувати собі merged evidence SHA;
- не може отримати адресу.

Ця версія ledger **не виділяє жодної post-D4 адреси**.

## Closeout

Валідатор сам обчислює:

```text
first-new-observable-capability
earliest-unresolved
placement-search-may-start
```

Пошук розміщення дозволяється лише після того, як знайдена перша справді нова
можливість і всі історично попередні рядки закриті.

## Принцип

**Історія вибирає наступне питання. Виконуваний derivation вирішує, чи
виживає назва. Розміщення — останнє.**
