# D8: дешевий collapse-screen другої осі — #3669

Цей research-falsifier відкидає привабливі другі осі, які **не заробляють**
чотирикутний D8 product.

Він не займає жодної D8-координати й не використовує старий D8 donor.

## Перевірені осі

| D6 family | кандидат другої осі | результат |
|---|---|---|
| LENGTH / LENGTH-ONTO | reverse списку | AXIS-INVISIBLE |
| MIN-LIST / MAX-LIST | conjugation через NEG | AXIS-DEPENDENT |
| ADD1 / SUB1 | conjugation через NEG | AXIS-DEPENDENT |
| INTEGERP / RATIONALP | числовий NEG | AXIS-INVISIBLE |
| REMAINDER / GCD | перестановка аргументів | PARTIAL-COLLAPSE |

### LENGTH / LENGTH-ONTO

Для всіх двійкових списків довжини 0..5 та кількох accumulator values:

```text
LENGTH(reverse(xs)) = LENGTH(xs)
LENGTH-ONTO(reverse(xs), a) = LENGTH-ONTO(xs, a)
```

Отже вісь орієнтації невидима.

### MIN-LIST / MAX-LIST

На всіх непорожніх списках довжини 1..4 з елементами `[-2,2]`:

```text
NEG(MIN(NEG(xs))) = MAX(xs)
NEG(MAX(NEG(xs))) = MIN(xs)
```

NEG лише повторює вже наявне перемикання MIN/MAX. Друга вісь залежна від
першої.

### ADD1 / SUB1

Для `x ∈ [-32,32]`:

```text
NEG(ADD1(NEG(x))) = SUB1(x)
NEG(SUB1(NEG(x))) = ADD1(x)
```

Тут теж NEG — це та сама семантична вісь, а не незалежна друга.

### INTEGERP / RATIONALP

На 23 різних exact rationals:

```text
INTEGERP(-x) = INTEGERP(x)
RATIONALP(-x) = RATIONALP(x)
```

Вісь знаку невидима.

### REMAINDER / GCD

На 256 парах додатних цілих `1..16 × 1..16`:

- GCD симетричний на всіх парах;
- REMAINDER змінюється при swap у 240 випадках;
- чотири потенційні кути дають лише **3 різні truth tables**.

Отже квадрат частково схлопується.

## Підсумок

```text
перевірено families    5
surviving axes         0
axis-invisible         2
axis-dependent         2
partial-collapse       1
```

Ми відкидаємо лише конкретну перевірену вісь, а не саме D6-сімейство.

Практичний наслідок: іншим агентам не треба повторно відкривати ці п'ять
гіпотез як D8 product candidates.
