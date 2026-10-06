# D9 fill v1 — перший щільний seed

**Статус:** RESEARCH / UNRATIFIED  
**Authority task:** #3964  
**Foundation:** Contract 11.7 / #3960

D9 продовжує щільний Core-domain метод після ратифікованого D8 256/256.

## Мета

```text
width    9
capacity 512
target   512 distinct meanings
```

Ширина дає місткість, а не значення. D9 не отримує семантику автоматично лише тому, що має 9 бітів.

## Перші 128 кандидатів

Ратифікований D8 має 64 selector residents із law-forced координатами.

Для кожного D8 selector `p`:

```text
p0 -> додати A перед R
p1 -> додати D перед R
```

Наприклад:

```text
D8 01100000 CDAAAAAR
D9 011000000 CDAAAAAAR
D9 011000001 CDAAAAADR
```

Отже:

```text
128 selector-law candidates
384 semantics remaining
0 ratified D9 residents
```

Machine-readable source: `knowledge/d9-selector-seed.json`.

## Що не робимо

- не копіюємо D8 residents як D9;
- не використовуємо Sens8/Sid8/Function8 координати;
- не допускаємо D8 overflow автоматично;
- не вважаємо `p -> p0/p1` семантичним законом для всіх D8 residents;
- не ратифікуємо D9 до окремого owner decision.

## Наступний крок

Зібрати решту 384 distinct meanings. Спочатку re-review 34 D8 overflow rows і всі збережені позитивні/негативні D8 witnesses, потім додавати чисті algebra/product/generator families і лише після цього historical/useful residue.
