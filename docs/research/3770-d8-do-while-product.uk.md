# D8 DO/WHILE × condition/projection — #3770

**Статус:** research-only, `PRODUCT-CANDIDATE`.  
**НЕ semantic authority. НЕ D8 admission.**

## Питання

Чи дає чинна D6-сім'я `DO | WHILE` дві незалежні бінарні семантичні осі, які утворюють справжній D8 product candidate?

Перевіряються дві осі:

```text
A: condition sense
   0 = continue while predicate is true
   1 = stop when predicate is true

B: terminal projection
   0 = return terminal state
   1 = apply result function at termination
```

Чотири кути:

```text
00  continue-while-true + return-state   (WHILE-shaped)
01  continue-while-true + apply-result   (novel candidate)
10  stop-when-true      + return-state   (novel candidate)
11  stop-when-true      + apply-result   (DO-shaped)
```

У coordinate/gauge аналізі використовується еквівалентний базис:

```text
role = condition-toggle XOR terminal-projection-toggle
projection = terminal-projection-toggle
```

Це дозволяє прив'язати current D6 `WHILE=110011` і `DO=110010` до одного product square без проголошення нових D8 residents.

## Вичерпний bounded witness

Carrier станів:

```text
S = {0,1,2}
```

Перебираються:

```text
27  total step functions S -> S
8   predicates S -> PredicateBit
27  result functions S -> S

27 × 8 × 27 = 5832 schemas
```

Для кожної схеми перевіряються всі три початкові стани і всі чотири semantic corners. Цикли виявляються явно; схема входить до positive observation set лише якщо всі чотири кути завершуються для кожного початкового стану.

## Результат

```text
finite schemas                              5832
all four corners terminate                  972
all four global semantic tables distinct    432
axis-transform commutativity                 4/4
```

Отже:

- condition-sense є спостережуваною віссю;
- terminal-projection є спостережуваною віссю;
- дві осі комутують як незалежні transforms;
- існують non-degenerate випадки, де всі чотири семантичні кути попарно різні.

Класифікація:

```text
PRODUCT-CANDIDATE
```

## Coordinate/gauge result

Current D6 authority:

```text
WHILE = 110011
DO    = 110010
```

Research footprint:

```text
11001100 .. 11001111
```

За product-gauge:

```text
11001100  WHILE / lower-domain duplicate
11001101
11001110  middle gauge orbit:
          DO duplicate
          + continue-while-true/apply-result novel semantic
11001111  stop-when-true/return-state generated fixed candidate
```

Перестановка порядку осей міняє лише `01/10`. Кут `11` є інваріантним.

Footprint не перетинається з 64 selector-candidate coordinates.

## Межі висновку

Цей witness **не** стверджує:

- що D8 ратифікований;
- що будь-яка з чотирьох координат є current D8 resident;
- що lower-domain duplicate повинен дублюватися в D8;
- що novel middle semantic має вже визначену абсолютну координату;
- що існування D6 resident автоматично дає runtime mechanism;
- що D7 бере участь в ancestry.

Кількість admitted D8 coordinates:

```text
0
```

## Відтворення

```sh
python3 benchmarks/d8-do-while-product/run.py \
  --out /tmp/d8-do-while-product
```

Очікуваний witness повторюється детерміновано; workflow запускає два прогони й порівнює `witness.json`.

## Принцип

**Дві додаткові координатні біти мають бути зароблені двома незалежно спостережуваними законами; чотири назви самі по собі product square не створюють.**
