# my-lisp semantic authority map

Status: CURRENT. Ця карта не створює семантику; вона показує, де перевіряти чинне твердження.

## Єдина функціональна онтологія

```text
00000000
...
11111111
```

Рівно 256 функцій. Самі 8 бітів є функціональною тотожністю. Жодне слово, symbol/string, enum label, historical label, opcode або backend name не є другою функцією і не стоїть між 8 бітами та законом Core.

```text
8 bits
  ↓
Core profile
  ↓
Lisp-owned law
  ↓
selected mechanism
  ↓
observation / result
```

## Authority order

1. `language-contract.lisp` Contract 9.
2. Standing invariant #1325 та executable SID8-only guard #1331.
3. Lisp-owned Core contracts / laws, що описують поведінку конкретних 8 бітів.
4. Executable conformance evidence.
5. Reference runtime `crates/my-lisp` як механізм і conformance witness.
6. Independent substrates/backends.
7. Generated reference та human prose.
8. Historical/process material.

Нижчий рівень не може переписати вищий.

## Core profiles

Core1–Core4 — не чотири набори названих функцій. Це профілі законів над тим самим закритим простором 256 восьмибітних функцій. Профіль може змінити закон, result domain або механізм для конкретних 8 бітів, але не їхню тотожність.

## UI/source routing

Людські підказки можуть існувати лише поза функціональною онтологією як механічний UI/source routing. Вони не створюють function identity, не володіють meaning і не можуть бути проміжною semantic authority.

Заборонена модель:

```text
word/name → meaning → 8 bits
```

Допустима лише механічна допомога вводу, після якої в семантичному шляху залишаються самі 8 бітів.

## Runtime / host boundary

Host/runtime/compiler/backend можуть мати локальні таблиці, enum-и, fallback-и, оптимізації та власну implementation semantics. Це не порушення саме по собі. Жорстка межа асиметрична (#1347):

```text
my-lisp → host/runtime    allowed
host/runtime → Lisp semantic authority    forbidden
```

Lisp-owned law не повинен ставати похідним від Rust types/tables/files.

## Історія

Старі документи можуть описувати попередні моделі як археологію. Вони не є поточною мовою. Якщо історичний термін знову з'являється у чинному contract/authority/prose як функціональна сутність, це regression.

## Documentation rule

Поточне пояснення повинно посилатися на Contract 9 / #1325 і називати функцію її точними 8 бітами. Не створювати нових словесних function identities заради зручності документації.
