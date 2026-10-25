# Sūtradhāra — D11 UNFOLD-RIGHT: доказ пріоритету D3 · 2026-10-25

## Повторне читання main
До цієї правки `main` мав SHA `6e2417d4c14ef5c73955e0a4a44de5b1ec90fa85`. У цьому SHA
**інший агент уже виправив SENS джерело** `lib/d11-srfi1-unfold.lisp`,
виніс рекурсію у `розгорнути-список-праворуч-зі-стану-ядро`,
а публічний вхід перевіряє `перевірити-кінцевий-список-розгортання`
до виклику `завершити?`. Ми НЕ переписували роботу колеги.

## Суть мовного закону
Заданий кінцевий хвіст UNFOLD-RIGHT є значенням, яке вже існує до
обчислення генератора. У SENS профілі це скінченний правильний
D3-список: тільки `()` завершує його; D1:ні як хвіст — Type.
Ніщо не повинно маскувати CAR Type помилкою користувацького callback.
Історичний алгоритм SRFI-1:
https://srfi.schemers.org/srfi-1/srfi-1.html

## Мій внесок у коміті
- `tests/fixtures/d11-unfold-right-priority-atomic-tail-must-error.lisp`: атомний D1:ні хвіст з отруйним `завершити?`.
- `tests/fixtures/d11-unfold-right-priority-deep-tail-must-error.lisp`: глибокий D1:ні хвіст із таким самим пріоритетом.
- `scripts/prove-lisp-semantic-t5m.sh`: два незалежні negative Type-свідки підключені до
  реального direct → Zig/T5M paired → standalone SENS, з хешами входів.
- Незмінені D1/D3/D4/D5 коди. Жодного нового D11 opcode, Rust чи Python
  семантичного виконавця.

## Незавершене
Статичне балансування SENS-форм перевірено, а от реальний нативний
SENS/Zig verdict тут ще не запущено. Не плутати коміт із PASS.
Перемінтити парний носій `lib/d11-srfi1-unfold.lisp` і виконати фізичні свідки
на одній версії без розходження source/carrier/view.
Реліз `l0.42.0`: NO-GO, рішення — тільки власника.

## Передача наступному агенту
1. На точному SHA запуск `bash -n scripts/prove-lisp-semantic-t5m.sh`
   і відповідних SENS Cargo інтеграцій.
2. `bash scripts/prove-lisp-semantic-t5m.sh target/debug/sens
   target/debug/sens-trit /tmp/sens-d11-unfold-priority`: зберегти
   direct/paired/standalone stderr та SHA-256, не змінювати RED на PASS.
3. Синхронізувати D11 SENS джерело і фізичний T5M carrier/view
   лише нативним mint; потім оглянути D11 group-by/juxt/alist.
4. Перейти до невизначених D12+ та F6 producer→consumer #5984.

**Deutsch:** Die SENS-Quellkorrektur stammt von einem anderen Agenten;
hier folgen zwei adversariale Typzeugen und der native Proof-Gate.
**English:** Another agent already fixed the SENS implementation.
This checkpoint contributes two adversarial native-test witnesses.
