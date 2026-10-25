# Yukti (युक्ति) · Д5:11100 ASSOC / saṃbandha · 25.10.2026

## Перевірена першопричина
Історичний SENS `знайти-за-ключем` повертав першу збіжну пару до перевірки кінця D3-списку; неправильний пізній хвіст або запис ставав невидимим. Це така сама помилка впевненої відповіді за пошкоджених передумов, як виправлена в Д5:11101 MEMBER (`5117d756581d67e2f9c29ce24de7f4495d84ad60`).

## SENS-виправлення
Розширено `lib/core4-parts/core4-d6.lisp` і синхронний `lib/core4.lisp`. Додано одну похідну функцію `знайти-за-ключем-ядро`; ратифікований виклик Д5:11100 `знайти-за-ключем` лишається незмінним за інтерфейсом і повертає першу пару, або структурний `()` за відсутності. Після першого збігу зберігає D1-прапорець, не порівнює ключі повторно, але перевіряє решту хребта й кожен запис. Зіпсований список/запис дає справжній D3 `перше` Type, не відсутність. Без нового opcode або host-оракула.

`scripts/prove-lisp-semantic-t5m.sh`: чотири точні випадки (`d5-assoc-total-list-positive`, `d5-assoc-total-list-mutant`, `d5-assoc-hidden-tail`, `d5-assoc-late-record`); оновлено мінімальний витяг визначень для епістемічних свідків: ядра Д5 MEMBER і ASSOC перед їхніми публічними викликами. Фізичні позитив/мутант/Type маршрути SENS→Zig/T5M→paired→standalone Core4.

## Невизначене
Статичний баланс S-виразів не підтверджує фізичне виконання. Обидва нові D5 source commits потребують canonical remint Core4. Раніше 4/4 D11 two-witness були нативно PASS на SHA `d19a193b`, але F6 producer→consumer і дрейф фізичних носіїв лишалися RED. Жодного релізного GO.

## Техзавдання наступному Swarm-агенту
1. Перевірити точні SHA нового коміту та всі 8 D5 MEMBER/ASSOC witness ID на direct/paired/standalone. Якщо red, зберегти source/physical/view SHA, actual vs expected.
2. Перевипустити `lib/core4.sens` строго чинним SENS/Zig mint. Не створювати фізичні слова/байти вручну; після remint підтвердити semantic law.
3. Перевірити регресійні D6 UNION/INTERSECTION та D9 MAP-CONTAINS/MAP-GET, бо вони композиційно викликають Д5.
4. Незалежно усунути F6 producer→consumer rejected invalid-format за source/physical правдою, не додавати compat SID8, не перетворювати Type на ().
5. Далі D7–D11 резидентна виконавча карта, D12→D24 signed overflow. Повне завершення/реліз NO-GO до owner GO.

`D5_ASSOC=SOURCE_COMPLETE_NATIVE_PENDING`
`RELEASE=NO-GO`

**Deutsch:** D5 ASSOC überprüft jetzt auch den gesamten Listenrest und alle Records.
**English:** D5 ASSOC validates the entire alist before confirming its first match.
