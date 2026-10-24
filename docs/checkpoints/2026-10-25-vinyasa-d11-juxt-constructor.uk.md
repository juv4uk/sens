# Vinyāsa — D11 JUXT: перевірка структури при створенні замикання · 2026-10-25

## Призначення

Vinyāsa (विन्यास) — узгодження порядку SENS-обчислень. Дякую Sūtradhāra
за раніше встановлений зв'язок source → T5M → виконуваний свідок та
діагностику відставання фізичного вигляду D11. Це наступний вузький
виправний крок, не повторення правки PARTITION-BY.

**SENS_SOURCE:** `lib/d11-clojure-juxt.lisp`.
**Виконувана семантика:** тільки SENS; нових opcode, координат D11,
та семантики в Rust/Zig не додано.
**Коміт зміни:** `bc7b34a105432a604d205abc04a0d5bdb090a6af`.
**Blob після зміни:** `daf170a4771f9adc7c8a1e0815888363b02ff40c`.

## Точний дефект

До виправлення `побудувати-зіставлення-функцій` просто повертала
вкладену `функція`, а `застосувати-набір-одномісних-функцій`
перевіряла D3-структуру тільки при майбутньому виклику.
Це суперечить чинному негативному SENS-закону
`tests/semantic/d11-clojure-juxt-constructor-improper-tail-negative.lisp`:
неправильний D1:ні хвіст треба відхилити при створенні замикання
як точну D3 CAR Type, а не відкладати помилку.

У SENS додано іменоване
`побудувати-зіставлення-функцій-із-перевірених`, яке захоплює тільки
структурно підтверджений список. Публічний конструктор виконує
`підтвердити-правильний-набір-функцій` перед його викликом.
Подальший виклик замикання проходить через чинне
`застосувати-набір-одномісних-функцій-ядро`: порядок і кратність
функцій не змінено; повторної перевірки списку при кожному виклику немає.

Цей профіль JUXT є одномісним і повертає SENS-список; історичний
Clojure JUXT з варіативною арністю та вектором не є заявленим контрактом.

## Докази, які вже існують як джерела

- Позитиви й контрприклади: `tests/semantic/d11-clojure-juxt-laws.lisp`,
  `tests/semantic/d11-clojure-juxt-mutant.lisp`.
- Помилка створення замикання: `tests/semantic/d11-clojure-juxt-constructor-improper-tail-negative.lisp`.
- Пріоритет структури перед аварійним callback:
  `tests/semantic/d11-clojure-juxt-poison-improper-tail-negative.lisp`.
- Чинний proof-runner уже збирає ці джерела з `lib/d11-clojure-juxt.lisp`
  у `scripts/prove-lisp-semantic-t5m.sh`; НЕ додавати дублі workflow.

## Атестація

- Статично перевірено: збалансованість дужок, заміна лише однієї
  визначеної форми, віддалений Git blob після commit/push.
- Стан `host-debt0 + language-stays` на SHA `bc7b34a1`:
  **SUCCESS**.
- Стан короткого SENS CI на цьому SHA під час звіту:
  **QUEUED**, run `40143822434`. Це не PASS виконуваної семантики.
- `NATIVE_SENS_POSITIVE=NOT_VERIFIED`
- `NATIVE_SENS_NEGATIVE=NOT_VERIFIED`
- Фізична відповідність `.lisp ↔ .sens ↔ безрозширеневий бітовий вигляд`:
  **NOT_VERIFIED**. Перемайнити канонічним Zig/T5M, не редагувати
  фізичний blob як текст.

## Наступний агент: точне завдання

1. На поточному `main` прочитати commit і blob `lib/d11-clojure-juxt.lisp`;
   не перезаписувати паралельну працю.
2. Запустити чинний SENS/Zig proof-runner:
   `bash scripts/prove-lisp-semantic-t5m.sh target/debug/sens target/debug/sens-trit /tmp/d11-juxt-evidence`,
   на справжніх виконуваних бінарниках. Не називати Python-макет PASS.
3. Перевірити позитивні JUXT-закони та негативне відхилення
   constructor-improper-tail саме при побудові функції; записати
   SHA, фактичний Type, команду, очікуваний/фактичний результат.
4. Відновити фізичну трійку source → Zig/T5M → SENS для `lib/d11-clojure-juxt.lisp`
   чинним `scripts/refresh-executed-t5m-pair.sh` лише після
   повного нативного PASS; не видавати старий вигляд за новий.
5. Запустити `scripts/guard-domain-function-reuse.py --file lib/d11-clojure-juxt.lisp --register`;
   нова іменована бібліотечна композиція має бути кандидатом D11
   без винайденої координати. Перед записом переглянути результат
   охоронця й не створювати дубль у реєстрі.
6. Продовжити звірку фізичних функцій D5–D8, окремо D10/D11
   із доказом кожного виклику; для D12+ перевірити числові значення,
   а не трактувати їх як викличні функції.
7. Реліз: **NO-GO**, поки немає повного native evidence на
   окремо визначеному candidate SHA і рішення власника.

Причини невизначеності називати поіменно:
`ВІДСУТНЯ_ФІЗИЧНА_ПРОЄКЦІЯ`, `НЕПЕРЕВІРЕНО` або фактичний
`ПОМИЛКА_ВИКОНАННЯ`, якщо відтворена. Це не синоніми.

---
Deutsch: D11 JUXT validiert die D3-Funktionsliste jetzt beim Erzeugen der
Closure. Native SENS-Tests und T5M-Parität sind noch nicht bestätigt.

English: D11 JUXT now checks the entire D3 function list at closure
construction. Native execution and physical T5M parity remain unverified.
