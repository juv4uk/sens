# Ядро мови SENS — exact-domain identity

Цей документ описує поточну модель ідентичності Contract 11.

Історичні flat SENS8 / SID8 / Function8 описи лишаються корисними як
provenance та compatibility-докази, але не є поточною семантичною владою.

## Канонічна семантична identity

Канонічний семантичний об'єкт SENS:

```text
точний двійковий об'єкт
+ точний домен
+ доведений / ратифікований закон
```

Біти самі по собі не несуть значення. Ширина сама по собі не дає residency,
callability або semantic membership.

Однакові packed payload у різних доменах — різні identity.

```text
D3 001 != D4 0001 != D5 00001 != D6 000001
```

Zero-padding, truncation, low-bit extraction чи integer equality не можуть
створити або відновити domain identity.

## Поточні Core-домени

```text
D1  точні однобітні predicate answers
D2  точна двобітна структура
D3  точна трибітна foundation
D4  точна чотирибітна bootstrap
D5  точний п'ятибітний typed domain
D6  точний шестибітний typed domain
```

Для D5/D6 існування носія, residency, derivability, callability та runtime
implementation — різні факти. Вільна координата не має значення, доки її не
допустить закон домену.

D7 sound/text — окремий напрям і не є callable лише через двійковість.

## D1 — PredicateBit

```text
0 = NO
1 = YES
```

PredicateBit — не Number, не host Bool, не T/NIL і не structural empty.

## D2 — структура

```text
00  separator
01  close
10  open
11  dot
```

Це об'єкти структурного домену, не function identities.

## D3 — foundation

```text
000  structural empty ()
001  QUOTE
010  ATOM
011  CDR
100  CAR
101  EQ
110  COND
111  CONS
```

Назви ролей — лише документаційні проєкції. Канонічна identity — exact D3
coordinate під D3 law.

## D4 — bootstrap

D4 — точний чотирибітний bootstrap domain, ратифікований своїм законом.
Його координати не реконструюються з історичних восьмибітних Function8.

LAMBDA і DEFINE — поточні D4 bootstrap identity. Нерозміщені координати
лишаються нерозміщеними.

## Reader

Канонічне двійкове джерело зберігає точну ширину слова до semantic routing.

```text
10 001 01
```

це D2 open, одне exact W3 слово і D2 close. Source-domain bridge може підняти
допущені W3/W4/W5/W6 слова прямо у відповідні Core domains.

Reader не має права відновлювати домен через zero-extension старого 8-bit коду.

Історичний exact-eight-bit source лишається обмеженим compatibility path на
час міграції.

На початку виразу apostrophe — reader sugar для вже допущеної D3 QUOTE identity;
він не створює проміжної human-name або Sens8 identity.

## Surfaces

Людські та symbolic spellings — опціональні проєкції.

```text
surface/UI input
      ↓ mechanical registry projection
exact domain identity
```

де domain mapping уже допущений.

Немігрувані історичні registry rows можуть явно проєктуватися в legacy
eight-bit compatibility identity. Цей шлях має бути позначений як legacy і не
має права виводити домен з байта.

Заборонені моделі:

```text
name -> meaning
legacy byte -> guessed domain
width -> semantic role
```

## Одне активне ядро мови

SENS повертається до одного активного ядра: `lib/core.lisp`.

Core1 — bootstrap/provenance witness. Core2 — retired compatibility history.
Core3 — mechanism laboratory. Колишня назва Core4 згортається в одне активне
ядро.

Execution/research profile та backend можуть вибирати механізми, але не можуть
створювати або перевизначати semantic domain law.

## Execution mechanisms

Rust, C, Common Lisp, Prolog, Datalog, CLIPS, WASM, FPGA та інші substrates —
свідки механізму.

Backend отримує вже вибраний domain-qualified semantic object або явно
позначену compatibility projection. Opcodes, host enums, packed bytes та native
types не створюють SENS meaning.

## Compiler / IR rule

Канонічні compiler та IR identities зберігають exact domain і exact bits.

Історичний eight-bit ABI або fast path може лишатися лише як явно названий
compatibility/backend projection. Reverse byte-to-domain inference заборонений.

## Structural empty — не нуль іншого домену

```text
D3 000 structural empty
!= D1 0 PredicateBit NO
!= Number 0
!= historical exact8 00000000
```

Однаковий packed numeric zero не зливає домени.

## Historical Sens8 / Sid8 / Function8

Історична exact-eight-bit machinery може лишатися тільки в обмежених ролях:

- compatibility;
- transport;
- backend mechanism;
- archived provenance;
- explicit legacy external ABI.

Вона більше не є універсальною semantic identity.

Новий канонічний код не повинен додавати Sens8/Sid8 dependency, якщо boundary
не позначений явно як одна з цих ролей.

## Межа проєкту

Reference Rust implementation — evidence і mechanism, не semantic authority.
Поточна authority — Contract 11, ратифіковані domain laws і language-owned
executable evidence.

Канонічне розширення джерела лишається **`.lisp`**. File suffix не створює
identity; її визначають exact source words і domain law.

Пріоритет authority описано в
[`semantic-authority-map.md`](semantic-authority-map.md).
