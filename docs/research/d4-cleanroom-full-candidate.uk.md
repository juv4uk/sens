> **ЗАМІНЕНО OWNER-RATIFICATION #3272.** Цей файл зберігає доретифікаційний кандидат 14+2 лише як дослідницьке свідчення. Чинний D4 визначають Contract 11.2 та `contracts/d4-bootstrap-ratification.lisp`.

# Мінімальний історичний bootstrap-кандидат D4 — #3225

Історія може пропонувати capabilities, але старі координати не мають жодної влади.

Фільтр: залишаємо лише можливості, потрібні історичному/self-host bootstrap, та стабільні похідні residents; історичні механізми й зайві зручності окремих identities не отримують.

```text
0000 APPLY
0001 EVAL
0010 LAMBDA
0011 DEFINE
0100 NOT
0101 UNALLOCATED
0110 CDAR
0111 CDDR
1000 CAAR
1001 CADR
1010 LOOKUP
1011 BIND
1100 EVCON
1101 EVLIS
1110 LIST
1111 UNALLOCATED
```

Чому саме такі волокна нового ратифікованого D3:
- EMPTY -> APPLY/EVAL: виконання вже вирішеного callable проти контекстної інтерпретації;
- QUOTE -> LAMBDA/DEFINE: executable abstraction проти стійкого іменованого binding;
- ATOM -> NOT + порожнє місце: похідний предикат; другої необхідної capability немає;
- CDR/CAR -> доведений закон композиції селекторів;
- EQ -> LOOKUP/BIND: читання/запис середовища за exact identity;
- COND -> EVCON/EVLIS: helpers умовного та спискового evaluator;
- CONS -> LIST + порожнє місце: повторне конструювання; другої необхідної capability немає.

Новими irreducible bootstrap capabilities вважаємо лише LAMBDA і DEFINE. Решта — generated/derived residents. Дві дірки навмисні.

LABEL, FUNCTION/FUNARG, EVALQUOTE, PAIRLIS, ASSOC, APPEND та інші не отримують D4 identities, бо наші дослідження класифікували їх як derived або mechanism-only.
