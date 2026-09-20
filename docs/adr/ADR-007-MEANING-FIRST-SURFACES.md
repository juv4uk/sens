# ADR-007 — Значення первинне: людські поверхні

**Статус:** Accepted  
**Дата:** 2026-09-08  
**Міграція authority:** завершена ADR-008

## Рішення

У **машинному семантичному шарі** `my-lisp` жодна людська мова не є мостом до
значення для іншої людської мови.

Semantic identity первинна. Людські написання є surface names цієї identity.
Жодна surface не може реалізовуватися через lookup іншої людської surface.

Це не суперечить мовній політиці репозиторію, де українська є першою мовою
проєкту. Українська може бути головною мовою документації, дизайну та розвитку,
але machine semantic identity не повинна бути словом українською, англійською,
санскритом чи будь-якою іншою людською мовою.

```text
                         meaning
                            │
              ┌─────────────┼─────────────┐
              │             │             │
             UK            EN            SA
```

Та сама топологія застосовується до канон()+7, ordinary builtins,
Lisp-визначених public functions, macros і майбутніх public semantic identities.

Для Canon значення незмінне. Для ordinary public API значення може еволюціонувати
через звичайний language-contract process, але surface topology лишається тією
самою.

## Фундаментальний інваріант

Заборонено:

```text
UK -> EN -> meaning
SA -> EN -> meaning
EN -> UK -> meaning
```

Потрібно:

```text
UK --\
EN ----> meaning
SA --/
```

Surface spelling не є alias іншого surface spelling. Це пряме ім'я тієї самої
semantic identity.

## Числові semantic identities

Semantic identity handles містять лише цифри. Це правило нейтральності, а не
форматування. Навіть нібито загальний буквений префікс може непомітно занести
слово однієї людської мови в machine identity layer.

Допустимо:

```text
0001
0101
0104
```

Заборонено:

```text
m0104
id0104
meaning0104
```

Цифри є непрозорими handles. Вони не називають операцію.

## Форма реєстру

```lisp
(sr/1
  (0001
    (uk як-є stable)
    (en quote stable)
    (sa svarūpa stable)
    (sym ' stable))

  (0101
    (uk відобразити stable)
    (en map stable)
    (sa āvartana candidate)))
```

Порядок surface rows не має семантичного значення. Майбутня мова додається ще
одним peer row; redesign схеми не потрібний.

`+`, `-`, `<` та інша пунктуація не є людськими мовними написаннями. ADR-008
робить її явною спільною немовною surface `sym`.

## Завершена людська surface

Людську surface можна назвати complete лише коли для кожної вибраної public
semantic identity вона має:

- stable spelling;
- direct resolution до identity, а не через іншу людську surface;
- executable semantic-equivalence evidence;
- acceptance program цією surface;
- human presentation і diagnostics, придатні для цієї surface.

Нова або неповна surface може чесно мати `candidate` чи `missing`; вона не має
права мовчки fallback-итися через EN, UK, SA або іншу людську мову.

## Стан міграції

Перша редакція цього ADR тимчасово дозволяла
`lib/surface/uk-sa-coverage.lisp` залишатися authority, доки numeric registry був
лише seed. **Цей перехід завершено.** ADR-008 встановлює
`lib/surface/semantic-registry.lisp` як єдину machine authority і переводить
стару EN-shaped таблицю в історичний аудит.

Це закриває neutrality борг authority/schema. Це **не** означає, що кожне
public runtime value уже має один shared `Rc`/closure для всіх людських
spellings. Runtime peer-binding parity лишається окремою executable роботою.

## Відношення до ADR-005

ADR-005 встановив, що core не є English і що людські surface names не повинні
мати різної семантичної влади над одним meaning. Цей ADR узагальнює інваріант
на всі теперішні та майбутні людські поверхні. ADR-008 supersede-ить тимчасову
legacy-registry інтерпретацію ADR-005, але зберігає meaning-first topology.

Короткий закон machine layer:

> **Значення первинне. Жодна людська мова не є мостом до значення для іншої.**

Короткий закон project layer лишається окремим:

> **Українська — перша мова проєкту.**
