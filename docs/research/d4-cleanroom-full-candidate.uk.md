# Повний clean-room кандидат D4 — #3225

Повний дослідницький кандидат 16/16, виведений лише з ратифікованих D1–D3 та локальних законів D4-волокон.

**Не ратифіковано.** Історичні таблиці D4/SID8/Sens8 заборонені як premises.

```text
0000  GROUND?
0001  COALESCE
0010  ABSTRACT
0011  ENTER
0100  COMPOSITE?
0101  EXECUTABLE?
0110  CDAR
0111  CDDR
1000  CAAR
1001  CADR
1010  ASSOC-READ
1011  ASSOC-WRITE
1100  DISPATCH
1101  REENTER
1110  COLLECT
1111  MAP-BUILD
```

Локальні закони волокон:
- EMPTY -> спостереження ground / fallback-відновлення;
- QUOTE -> побудова відкладеної виконуваної поведінки / входження в представлену семантику;
- ATOM -> завершення поточного поділу видів / спостереження нового executable-carrier;
- CDR/CAR -> композиція селекторів;
- EQ -> читання/запис асоціації за точною identity-key;
- COND -> скінченний dispatch / необмежений re-entry;
- CONS -> скінченне збирання / рекурсивне transform-and-build.

Дисципліна статусів:
- селектори вже породжені законом;
- REENTER має clean-room lower-bound witness (#3230/#3233);
- ABSTRACT проходить незалежну clean-room перевірку (#3229);
- усі інші нові рядки лишаються кандидатами, доки їхній fibre-witness не пройде;
- жоден posterior historical match не створює semantic authority.
