# D8: collapse-screen другої осі — #3669

Цей witness відхиляє привабливі, але не незалежні другі осі до того, як вони
стануть заявами про D8-координати.

Перевірено:
- LENGTH/LENGTH-ONTO × reversal -> AXIS-INVISIBLE
- MIN-LIST/MAX-LIST × NEG-conjugation -> AXIS-DEPENDENT
- ADD1/SUB1 × NEG-conjugation -> AXIS-DEPENDENT
- INTEGERP/RATIONALP × NEG -> AXIS-INVISIBLE
- REMAINDER/GCD × swap аргументів -> PARTIAL-COLLAPSE

Точні bounded результати:
- LENGTH reversal: 63/63
- LENGTH-ONTO reversal: 315/315
- MIN/MAX NEG-conjugation: 780/780 в обох напрямках
- ADD1/SUB1 NEG-conjugation: 65/65
- exact numeric predicates invariant на 23 раціональних значеннях
- GCD symmetric 256/256, REMAINDER змінюється 240/256, тому маємо лише 3 унікальні кути

Підсумок: **0/5 запропонованих осей вижили**.

Це відкидає осі, а не назавжди самі D6-сімейства.

```sh
python3 benchmarks/d8-collapse-screen/run.py --out /tmp/d8-collapse-screen
```
