# D5 v2 generator shadow — #3284

Дослідницький кандидат після owner reset #3278.

Старий D5 resident APPEND прибрано, бо єдину чинну identity APPEND тепер має D4:1111 (#3287/#3291).

Звільнене місце не заповнюємо випадковою історичною зручністю. Беремо вже наявний у SENS генератор:

```text
10100  REVERSE
10101  REVERSE-ONTO
```

Локальний закон:

```text
REVERSE(x) = REVERSE-ONTO(x, ())
REVERSE-ONTO(x,y) = APPEND(REVERSE(x), y)
APPEND(x,y) = REVERSE-ONTO(REVERSE(x), y)
```

Це executable evidence #3293/#3294.

Чому це сильніше за NCONC/NREVERSE/LENGTH/NTH:
- NCONC/NREVERSE потребують деструктивної мутації pair, якої SENS свідомо не має;
- LENGTH/NTH корисні, але не пояснюють уже наявну структуру REVERSE/APPEND;
- REVERSE-ONTO вже є реальною stack-safe основою й стискає одразу дві інші семантики.

Кандидат лишається 32/32, не дублює D4 APPEND, відновлює selector geometry і перетворює одну стару LOCAL-ALGEBRA пару на SEMANTIC-GENERATOR.

Глобального значення п'ятого біта не заявляємо.
