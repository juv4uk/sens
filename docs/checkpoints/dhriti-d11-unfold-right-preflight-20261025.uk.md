# Dhṛti (धृति): D11 UNFOLD-RIGHT, структурний пріоритет

Дата 25.10.2026. Мета — SENS-семантика, не збільшення лічильника opcode.

## Першопричина
У `lib/d11-srfi1-unfold.lisp` праве розгортання мало перевірку
`перевірити-кінцевий-список-розгортання` лише на завершальній гілці.
Хоча `кінцевий-хвіст` є готовим SENS-значенням, попередній код
викликав `завершити?` і міг викликати `створити-елемент` та
`наступний-стан` раніше ніж упізнавав помилковий D1-хвіст.
Отже Type від callback міг маскувати структурний D3 CAR Type.

## SENS-виправлення
- Публічне `розгорнути-список-праворуч-зі-стану` підтверджує повний
  правильний скінченний D3 кінцевий хвіст рівно один раз, до callback.
- `розгорнути-список-праворуч-зі-стану-ядро` отримує вже підтверджений
  хвіст. Зворотний порядок та єдине обчислення генераторів збережені.
- UNFOLD (лівий) не змінено: його фінальний хвіст утворюється callback
  тільки у завершальному стані, тому неможливо перевірити раніше.
- Канонічне D3:() завершує список; D1:ні як елемент залишено допустимим.
- Машинних кодів, нової ратифікації D11, Zig/Rust-оракулів не додано.

## Мовні свідки
- Існуючі позитивні: `tests/semantic/d11-srfi1-unfold-positive.lisp`.
- Існуючий мутант: `tests/semantic/d11-srfi1-unfold-mutant.lisp`.
- Існуючі negative terminal: `tests/fixtures/d11-unfold-terminal-right-{atom,dotted}-must-error.lisp`.
- Нові: `tests/fixtures/d11-unfold-right-tail-before-stop-{atom,dotted}-negative.lisp`.
- Нові негативи вимагають `car expects a non-empty list`, не
  `cdr expects a non-empty list`, `unknown Text7 binding` або parser error.

## Докази та невизначеності
- SENS джерело та негативні форми структурно перевірені до коміту.
- `NATIVE_SENS_POSITIVE=NOT_VERIFIED`.
- `NATIVE_SENS_NEGATIVE=NOT_VERIFIED`.
- `ZIG_T5M_ROUNDTRIP=NOT_VERIFIED`.
- `COMMITTED_T5M_TRIPLET=STALE` до регенерації чинним SENS/Zig.
- `RELEASE=l0.42.0:NO-GO`.

## Наступний Swarm
1. На точному новому SHA виконати усі UNFOLD позитиви, мутант, обидва
   нові Type-негативи і старі terminal/stop негативи в реальному SENS.
2. Перевірити, що обидва poison callback не виконалися: конкретно D3 CAR
   Type, і негативи без раннього Type не проходять як false позитиви.
3. Оновити однойменні `.sens` та бітовий перегляд лише
   `scripts/refresh-executed-t5m-pair.sh` через Zig/T5M.
4. Записати exact SHA, команду, джерело, expected, actual, byte roundtrip.
5. Продовжити D5→D8 / D10 / числовий D12 незалежними native свідками.
Не створювати новий workflow, гілку чи машинну заглушку.
