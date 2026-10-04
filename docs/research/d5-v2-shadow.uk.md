# D5 v2 shadow — #3284

Дослідницький rebase повного Core.D5 після owner-ratified D4 #3272.

## Фаза A

Зберігаємо всі 32 D5 residents, усі 16 двоелементних блоків та всі класи OD-D5-LAW-001. Пересуваємо тільки вісім блоків, потрібних для відновлення selector-generator під новими D4 selector prefixes.

```text
0110 CDAR -> 01100 CDAAR / 01101 CDADR
0111 CDDR -> 01110 CDDAR / 01111 CDDDR
1000 CAAR -> 10000 CAAAR / 10001 CAADR
1001 CADR -> 10010 CADAR / 10011 CADDR
```

Зворотне витіснення:

```text
1010 -> APPEND / REVERSE
1011 -> TIMES / QUOTIENT
1100 -> GO / RETURN
1101 -> LESSP / GREATERP
```

Механічно очікуємо:

- occupancy 32/32;
- 16 moved, 16 unchanged;
- усі 16 D5 pair memberships збережені;
- selector generation 8/8 відновлено;
- класи локальних законів незмінні;
- універсального D4-parent theorem немає;
- універсального значення п'ятого біта немає.

## Фаза B

D4 #3272 уже містить `APPEND` на 4 бітах. Старий D5 resident `APPEND` тому явно позначено для semantic de-duplication. Фаза A не підмінює його нишком.

Resident-set D5 змінюється лише окремим owner-рішенням.
