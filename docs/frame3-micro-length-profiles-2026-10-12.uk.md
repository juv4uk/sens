# Frame3-Micro: профіль визначає фізична довжина

Дата: 12.10.2026.

Рішення власника: **F3M не витрачає внутрішні байти на magic/version selector.**
Сімейство визначається зовнішнім маршрутом (`.f3m`, явний decoder/manifest),
а конкретний micro-profile визначається **лише точною фізичною довжиною payload**.

## Закон вибору

| Фізична довжина | Профіль | Бітовий простір |
|---:|---|---:|
| 1 байт | **F3M-1** | 8 біт / 256 кодів |
| 2 байти | **F3M-2** | 16 біт / 65 536 кодів |
| 3 байти | **F3M-3** | 24 біти / 16 777 216 кодів |
| 4 байти | **F3M-4** | 32 біти / 4 294 967 296 кодів |

Нуль байтів і 5+ байти зараз **відхиляються fail-closed**. Нову довжину не можна
вводити неявно: F3M-5 тощо потребує окремого рішення, таблиці ранжування,
негативних тестів і доказу roundtrip/evaluator parity.

## Заборона sniffing

Вміст payload не може визначати профіль. Байти `0xF3`, `0xF4` або будь-які
інші значення не є magic selector для F3M. Це означає:

- 1 байт завжди маршрутизується як F3M-1;
- 2 байти — як F3M-2;
- 3 байти — як F3M-3;
- 4 байти — як F3M-4;
- помилка декодування вибраного профілю є помилкою; fallback у T5/F3C немає.

Зовнішній маршрут визначає лише сімейство F3M; **довжина визначає профіль**.
Таким чином усі 8/16/24/32 фізичні біти лишаються доступними рангу програми.

## Стан доказів

**F3M-1:** чинний dense enumerator використовує **всі 256/256** однобайтових
значень як унікальні замкнені програми. Для кожного коду перевіряються exact
SENS words, canonical parse, реальний evaluator, T5 parity і reverse rank.
Приклад: `0x3E` → `CAR(CONS(1,NIL))`.

Попередній sparse witness `0x45` / 45 із 256 кодів лишається історичним
артефактом 11.10.2026 і не є чинною F3M-1 таблицею.

**F3M-2 і F3M-3:** dense enumerator уже виділяє їм неперетинні глобальні
rank-вікна: наступні **65 536** і **16 777 216** програм відповідно.
F3M-2 має exhaustive byte-roundtrip тест усіх 65 536 payloads; F3M-3 має
boundary/sample roundtrip і реальний трьохбайтовий COND witness. Повний
exhaustive evaluator sweep усіх 16 777 216 F3M-3 програм ще не заявляється
завершеним.

**F3M-4:** наступне неперетинне вікно має **4 294 967 296** локальних рангів.
Поточна microgrammar гарантовано містить достатньо програм: cumulative count
до 11 micro-nodes = **3 149 929 038**, а сам 12-node layer має
**27 233 592 018** програм, тож F3M-4 повністю заповнюється всередині
9–12-node області. Перевірено boundary values і **65 536 stratified samples**
по всьому 32-бітному простору; повний 2^32 exhaustive sweep не заявляється.

### Трьохбайтовий виконуваний свідок

Фізичний payload **`2F 18 59`** (рівно 3 байти, без мітки) у чинному
dense F3M-3 декодується в:

`IF-ATOM(QUOTE(0), CAR(CONS(QUOTE(1),1)), CDR(CONS(QUOTE(NIL),QUOTE(0))))`

Він відновлює точні SENS-слова, проходить canonical parser і реальний
evaluator та дає результат **`1`**. Це не вручну призначений opcode:
`2F 18 59` є локальним 24-бітовим рангом усередині неперетинного
F3M-3 global-rank window.

[GitHub Actions run 38194615315](https://github.com/juv4uk/sens/actions/runs/38194615315)
— **SUCCESS**: dense rank-window tests PASS, усі **65 536/65 536** F3M-2
payloads пройшли exhaustive encode/decode roundtrip, F3M-3 boundary/sample
roundtrip PASS, трьохбайтовий COND witness PASS, F3M-1 256/256 evaluator/T5
proof PASS.



### Чотирьохбайтовий виконуваний свідок

Payload **`DE AD BE EF`** (рівно 4 байти) декодується чинним F3M-4
enumerator у 12-вузлову програму:

`ATOM(CONS(ATOM(CDR(CONS(QUOTE(0),CAR(CONS(NIL,QUOTE(0)))))),ATOM(ATOM(ATOM(QUOTE(NIL))))))`

Вона проходить canonical parser, реальний SENS evaluator, повертає **`0`**
і roundtrip-иться назад точно в `DE AD BE EF`. Код обраний не як opcode:
це звичайний 32-бітний локальний rank усередині F3M-4 window.


### Пошук максимально виразного коду біля верхньої межі F3M-3

Для поточної microgrammar визначено 6 capability-класів: **QUOTE, ATOM,
CONS, CAR, CDR, COND**. DP по всіх 64 capability-mask'ах довів, що
найраніший глобальний ранг, який уже містить усі шість класів, дорівнює
`1 523 043`, тобто локальний F3M-3 payload **`16 3C 63`**.

Окремий exhaustive-пошук перевіряє **всі останні 65 536** трьохбайтових
payloads, від `FF 00 00` до `FF FF FF`. Прозорий lexicographic score:
кількість capability-класів → кількість COND → кількість encoded-операцій →
глибина → exact-word count → node count → пізніший rank.

Переможець цієї останньої 64K-сторінки — **`FF FB 37`**, лише на
**1 224 ранги** раніше за фізичну межу `FF FF FF`:

`CAR(CONS(CDR(CONS(1,QUOTE(1))),ATOM(IF-ATOM(QUOTE(NIL),QUOTE(NIL),QUOTE(NIL)))))`

Властивості witness: **6/6 capability-класів, 1 COND, 11 encoded-операцій,
глибина 4, 43 exact words, 9 micro-nodes**. Канонічний reader приймає
відновлені слова, реальний evaluator виконує програму і повертає exact
**D1:1**; encode/decode повертає ті самі три байти `FF FB 37`.

Сам крайній `FF FF FF` не є «найпотужнішим»: у ньому лише 4/6
capability-класів і немає COND. Тобто порядок rank є канонічним порядком
enumerator'а, а не шкалою обчислювальної сили.

[GitHub Actions run 38195272188](https://github.com/juv4uk/sens/actions/runs/38195272188)
— **SUCCESS**: DP-minimum, exhaustive final-64K search, реальне виконання,
F3M-1 256/256 regression і original-F3 corpus усі PASS. F3M-4 окремо має
algebraic capacity proof, 65 536 stratified roundtrip samples і executable
`DE AD BE EF` witness.

Старі дослідження canonical capacity можуть бути донорами для побудови
F3M-2/F3M-3, але їхні числа не стають автоматично чинною ємністю нового
профілю без нового exhaustive witness.

## Реалізація

Rust API: `sens::frame3_micro::frame3_micro_profile(payload)`.

Селектор дивиться тільки на `payload.len()`; unit tests окремо доводять,
що зміна значень байтів не змінює вибраний профіль.
