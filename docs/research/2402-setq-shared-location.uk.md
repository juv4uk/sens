# #2402 — нижня межа shared-location для SET/SETQ

Статус: лише research. Жодної адреси чи production mutation operator не додаємо.

## Жива межа D4

#2392 уже довів, що DEFINE не є просто immutable-конструкцією:

- повторне визначення в тому самому frame змінює його slot;
- top-level redefinition бачить уже створене closure;
- DEFINE успадкованого імені в child-frame створює child shadow;
- runtime-computed target для DEFINE відхиляється.

Тому питання після D4 вужче, ніж «чи може значення змінитися?»

## Спостереження, яке лишилось

> Із child-frame знайти найближчу вже існуючу lexical location і змінити саме її, не створюючи нового child binding.

```text
parent X = OLD
observer-before захопив parent X
child успадковує X

D4 child DEFINE X = NEW
  child отримує shadow
  observer-before -> OLD

nearest-existing update X := NEW
  child X не створюється
  observer-before -> NEW
  child lookup     -> NEW
  observer-after   -> NEW
```

Також фіксуємо shadowing:

```text
root X
  middle X
    leaf робить update X

міняється тільки middle X
root X лишається старим
```

Відсутнє ім'я fail-closed, а не створюється мовчки.

## Чого модель не стверджує

Test-only Rc<RefCell<_>> — це лише representation для спостереження identity location, а не семантична authority SENS.

Evidence не призначає historical surface name, D4/D5 address, parent word чи production storage mechanism.

## Попередній семантичний висновок

Поточний D4 не експонує nearest-existing outer-location update. Child DEFINE замість цього створює shadow.

Отже перший Phase-D mutation candidate — не просто «переприв'язати ім'я», а:

```text
shared-location update
```

Саме цю мінімальну delta мають далі класифікувати #2314/#2236.

## Принцип

**Mutation нова лише тоді, коли старий observer доводить: змінилася та сама location, а не з'явився новий shadow.**
