# #2011 — перший bounded результат для QUOTE-generator

Лише дослідження. Жодної зміни allocation/runtime/contract.

## Зафіксований закон

Історичний і поточний evaluator-law однаковий за суттю:

```text
QUOTE(form) -> operand-as-data
```

Тобто QUOTE повертає operand без оцінювання, а не будує новий quoted form.

## Кандидат 1 — глибина quotation як локальний generator

Executable witness:

```text
eval(QUOTE x)                 -> x
eval(QUOTE (QUOTE x))         -> (QUOTE x)
eval(QUOTE (QUOTE (QUOTE x))) -> (QUOTE (QUOTE x))
```

Наступний рівень quotation повертається як **побудовані дані**. Щоб отримати його з value, потрібна структура на кшталт `CONS(QUOTE, CONS(value, ()))`.

Отже repeated QUOTE не є локальною CAR/CDR-подібною дією: він потребує construction/ground.

## Кандидат 2 — quoted atom проти quoted list

QUOTE застосовує ту саму дію до обох payload-класів: повертає operand без оцінювання. Різниця належить payload-domain, а не новій дочірній операції QUOTE.

## Кандидат 3 — apostrophe

Reader apostrophe лише desugar-иться в той самий quote form, тому surface spelling не є семантичним descendant evidence.

## Висновок

Перші три очевидні QUOTE-family не доводять selector-strength binary family. `0010/0011` залишаються unallocated у межах цього експерименту.

Це bounded negative result, а не універсальна теорема про неможливість будь-якої майбутньої QUOTE-алгебри.

Артефакт: `scripts/research-2011-quote-generator.py`.
