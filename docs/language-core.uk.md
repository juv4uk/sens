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
D1  точні однобітні predicate answers — RATIFIED
D2  точна двобітна структура — RATIFIED
D3  точна трибітна foundation — RATIFIED
D4  точна чотирибітна bootstrap — RATIFIED
D5  exact five-bit carrier — UNRATIFIED / RESEARCH (#3278/#3279)
D6  exact six-bit carrier — UNRATIFIED / RESEARCH (#3278/#3280)
D7  sound/text provenance domain — RATIFIED
D8  exact eight-bit carrier — UNRATIFIED / RESEARCH (#3278/#3281)
```

D5/D6/D8 carrier existence не дає residency, semantic membership або
callability. Їхні попередні full-map/occupancy твердження — donor/provenance
після owner reset #3278.

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

### Predicate/control law

- `ATOM` — total predicate: результат тільки D1 `0|1`.
- `EQ` — typed partial predicate: admitted atoms дають D1 `0|1`; поза atom-domain — D3 `000 ()` як EMPTY/no-witness.
- `COND` має рівно `(test expression)` clauses і приймає як test тільки D1 `1`, D1 `0` або D3 `()`.
- D1 `1` вибирає; D1 `0` продовжує як explicit NO; D3 `()` продовжує як EMPTY/no-witness.
- інші test values — type/contract failure; exhaustion повертає D3 `()`.
- D1 `0` і D3 `()` мають однакову control-action «continue», але різну semantic identity.

## D4 — bootstrap

D4 — owner-ratified full compact domain (#3272), усі 16/16 координат зайняті.
Його координати не реконструюються з історичних восьмибітних Function8.

```text
0000 APPLY    0001 EVAL
0010 LAMBDA   0011 DEFINE
0100 NOT      0101 NULL
0110 CDAR     0111 CDDR
1000 CAAR     1001 CADR
1010 LOOKUP   1011 BIND
1100 EVCON    1101 EVLIS
1110 LIST     1111 APPEND
```

`NOT` і `NULL` різні, бо D1:0 ≠ D3:000 (). Старі D4/SID8 coordinates не мають placement authority. D5+ selector continuation fail-closed (#3209), а #3278 окремо відкликав semantic admission D5/D6/D8.

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
