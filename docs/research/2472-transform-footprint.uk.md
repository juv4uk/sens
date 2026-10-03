# #2472 — аудит transformation footprint для Phase D

Статус: лише research.

Аудит порівнює вже merged D1-D4 countermodels не за тим, чи вони "можуть
порахувати те саме", а за тим, **наскільки далеко треба переписати інтерфейс
програми**.

Сам по собі аудит не вирішує DERIVED-vs-NEW.

## Результат

| Операція | Countermodel | Footprint |
|---|---|---|
| GO | finite state + tail recursion | локальний rewrite PROG-регіону |
| RETURN | explicit exit continuation | rewrite протоколу call chain |
| SETQ | explicit immutable store | rewrite observer/store graph |

## GO

Синтетичний driver несе:

```text
(state remaining acc)
```

а переходи між labels стають tail-calls до цього driver.

Control-state може залишатися всередині трансформованого PROG-регіону.

Тому це найсильніший кандидат на справді **локальний desugaring**.

## RETURN

Non-local witness працює через новий helper protocol:

```text
(mode continue-k exit-k payload)
```

і `exit-k` передається крізь вкладені виклики.

Це доводить D4 expressibility, але footprint сильніший, ніж у GO.

Щоб окремо скомпільований незмінений helper міг виконати historical RETURN,
еквівалентний exit context мусить бути доступний без переписування call chain.
Поточний countermodel цього ще не доводить.

## SETQ

Explicit-state witness прямо каже, що pre-existing observers стають
**трансформованими closures**, які приймають current store:

```text
observer : store -> value
```

і викликаються як:

```text
(observer store)
```

Отже модель доводить D4 expressibility shared-location behavior, але міняє
observer protocol.

## Тиск на рішення #2472

Evidence дає три різні класи:

```text
LOCAL-REGION-REWRITE
CALLCHAIN-PROTOCOL-REWRITE
OBSERVER-PROTOCOL-REWRITE
```

Проєкт ще має визначити, які з них рахуються semantic derivation, а які лише
compilation/expressibility.

Консервативний кандидат закону:

> Локальний rewrite, що зберігає зовнішні callable/observer protocols, може
> рахуватися DERIVED. Transform, який змушує сторонні чи pre-existing values
> прийняти новий protocol, спершу доводить лише expressibility і потребує
> окремої equivalence theorem перед DERIVED.

Це кандидат закону, не ратифікація.

## Відтворення

```sh
python3 scripts/research-2472-transform-footprint.py
```

## Принцип

**Міряй межу переписування, а не лише те, чи D4 достатньо потужний, щоб
закодувати поведінку.**
