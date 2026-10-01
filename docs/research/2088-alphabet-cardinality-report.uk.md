# #2088 — cardinality алфавіту під binary-word law

Лише дослідження.

## Розділення тверджень

Формула `word ∈ {0,1}+` склеює три різні речі:
1. identity має алфавіт;
2. алфавіт мусить мати щонайменше два символи;
3. ці символи мусять бути саме `0` та `1`.

## Exact identity не вимагає binary

Unary-алфавіт теж дає різні exact words через довжину:
```text
•
••
•••
...
```

Тому exact width + exact symbol sequence самі по собі не виводять `|Σ|=2`.

## Два immediate refinements вже дають нижню межу

Якщо закон вимагає двох різних one-step дітей одного parent:
```text
p -> p+a
p -> p+b
p+a != p+b
```
то алфавіт має мати щонайменше два різні символи.

Це придатний lower bound для CAR/CDR-подібної генерації, але він залежить від сімейного branching-law.

## `0/1` — представники

Executable witness показує ізоморфізм:
```text
0 <-> α
1 <-> β
```
що зберігає equality, width, prefix, parent, append і two-branch path structure.

Отже математична структура виводить «дві розрізнювані альтернативи», а не конкретні glyph-и `0` та `1`.

Артефакт: `scripts/research-2088-alphabet-cardinality.py`.
