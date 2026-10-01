# #2019 — перша діагностика pressure для bīja3

Лише дослідження. Це навмисно слабше за доказ мінімальності.

## Питання

Якщо вилучити одне успадковане bīja3-seed з поточного declared Lisp I / Lisp 1.5 dependency corpus, скільки derived material зараз від нього залежить?

Це corpus-coverage питання, а не доказ:
- логічної необхідності;
- незалежності;
- невивідності іншим законом;
- унікальності bīja3.

## Метрики

Для кожного seed та історичної ери рахуємо:
- кількість derived nodes із цим seed у transitive support;
- кількість exclusive dependents;
- кількість co-seeds;
- чи є у declared graph шлях, який вже виводить seed через інший seed.

Останнє — лише graph diagnostic. Відсутність такого шляху не доводить незалежність у принципі.

## Поточний сигнал

CAR/CDR мають найбільший pressure у bounded corpus і по одному exclusive selector-descendant. QUOTE має найменший pressure і змінюється між Lisp I та Lisp 1.5.

Ці числа не означають:
```text
high pressure = necessary
low pressure  = removable
```

Вони лише показують, де alternative basis має дати сильніший reconstruction proof.

## Наступний крок

Використовувати pressure-map для пріоритизації справжньої роботи #2019:
1. capability loss при вилученні;
2. derivability з альтернативних roots;
3. alternative bases;
4. blind WSM comparison після freeze.

Артефакт: `scripts/research-2019-bija3-pressure.py`.
