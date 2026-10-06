# D10 forward/JTMS harvest v1

**Статус:** research / unratified  
**Issue:** #4028

Із 32 ще непокритих top-level definitions у `lib/forward.lisp` відібрано 26 самостійних semantic operations.

## Відібрано

```text
JTMS state algebra             3
JTMS condition matching       4
rule-condition recognizers    6
rule-condition matching      10
multi-result forward exec     3
-------------------------------
total                        26
```

## NO-SLOT у цьому tranche

```text
*working-memory*
*justified-memory*
*jtms-memory*
find-entry
map-apply-head
map-apply-head-jtms
```

Три перші — storage cells; решта — generic/local implementation helpers.

## Стан D10

```text
selected        330/1024
placed          256
unplaced         74
remaining       694
ratified          0
```

Усі 26 нових meanings лишаються `UNPLACED`. Старі 8-bit spellings у source-файлі не мають D10 placement authority.
