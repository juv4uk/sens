# Аудит представлення точних чисел

Статус: **аудит виконано 2026-09-09 у межах issue #28**.

Цей документ описує представлення, а не створює другу числову семантику. Точне формулювання сильніше й чесніше за гасло «ми не використовуємо float»:

> **Точна арифметика ніколи не округлює мовчки.** Runtime може використовувати `f64` як компактне представлення лише для математично точних цілих у діапазоні точного цілого IEEE-754 binary64; більші або дробові точні значення зберігаються як довільно-точний `Rational`.

## Представлення runtime

| Представлення | Значення | Правило допуску | Спостережуваний наслідок |
|---|---|---|---|
| `Value::Number(f64, Exactness::Exact)` | точне ціле | знаменник дорівнює 1 і число лежить у `[-2^53, +2^53]` | може брати участь у точній арифметиці; тег exactness є семантичними даними |
| `Value::Rational(Rational)` | довільно-точне ціле або дріб | точне значення не можна без втрат стиснути до compact representation, або воно дробове | числова межа задається лише ресурсними обмеженнями/пам’яттю |
| `Value::Number(f64, Exactness::Inexact)` | свідомо неточне binary64-значення | явний inexact ingress або арифметика з неточним операндом | арифметика/порівняння переходять до binary64 semantics |
| `NumericBuffer::I32` | явні fixed-width цілі дані | точне ціле має вміститися у signed 32 bits | звуження поза діапазоном дає названий `NumericOverflow` |
| `NumericBuffer::F32` | явні binary32-дані | finite numeric input навмисно звужується | втрата точності є частиною запитаного `f32` boundary, а не маскується як exact scalar arithmetic |

`Rational::as_precise_i64()` є єдиним правилом compactness для звичайних точних scalar values. Попри назву методу, умова сильніша за «поміщається в i64»: `Some` повертається лише для цілого в exact-integer range binary64 ±2^53.

## Карта переходів

```text
source integer / decimal / exponent / n/d
                  |
                  v
          exact Rational parse
                  |
          +-------+--------+
          |                |
 integer, |n| <= 2^53      otherwise
          |                |
          v                v
 Number(f64, Exact)     Rational
          \                /
           \              /
            v            v
           exact arithmetic
              as Rational
                  |
        +---------+----------+
        |                    |
 result compactable      result not compactable
        |                    |
        v                    v
 Number(f64, Exact)       Rational
```

### Parser

`crates/my-lisp/src/parser.rs` спочатку будує **точний числовий сенс**. Integer, decimal та exponent spellings не проходять через проміжне binary floating-point approximation. Decimal/scientific text йде через `Rational::from_decimal_literal`, а великі integer literals — через arbitrary-precision `Rational::from_literal`.

Після точного parse `as_precise_i64()` вирішує лише питання компактного зберігання:

```text
9007199254740992   -> compact exact Number   (+2^53)
9007199254740993   -> Rational               (+2^53 + 1)
-9007199254740992  -> compact exact Number   (-2^53)
-9007199254740993  -> Rational               (-2^53 - 1)
0.1                -> Rational 1/10
1,25               -> Rational 5/4
```

Синтаксично коректний decimal/exponent literal, який перевищує reader resource cap, завершується `NumericOverflow`; він не має мовчки перетворюватися на symbol.

### Evaluator та арифметика

`crates/my-lisp/src/eval/arithmetic.rs` перед загальним exact-path нормалізує кожен точний scalar operand до `Rational`. Compact exact `Number` відновлюється як точне ціле Rational; `Value::Rational` уже є exact.

Усі точні `+`, `-`, `*`, `/` працюють через Rational operations. Результат стискається лише через `exact_value()`, який використовує ту саму межу ±2^53.

Для поширених exact integer `+`, `-`, `*` існує i64 fast-path. Саме тут аудит #28 знайшов реальне порушення інваріанта: після успішного checked-i64 обчислення старий код напряму повертав `Value::Number(result as f64, Exactness::Exact)`. `checked_*` доводить лише межі i64, **не** точність binary64. Мінімальний witness:

```text
(* 3000000001 3000000001)
= 9000000006000000001
```

Обидва операнди входять у fast-path, добуток ще поміщається в i64, але непарне значення вже більше за 2^53 і не може бути точно представлене як f64. Виправлення маршрутизує fast-path result через `exact_value()` так само, як загальний Rational-path. `crates/my-lisp/tests/exact_number_boundaries.rs` є falsification test, який зламається, якщо silent rounding повернеться.

Якщо хоча б один арифметичний operand є свідомо inexact, арифметика переходить до f64 і повертає `Exactness::Inexact`. Це явний semantic transition, а не exact-value compression.

### JSON numeric boundary

Другий falsification sweep #28 знайшов той самий клас помилки у `json-parse`: integer token спочатку парсився як `i64`, а потім напряму будував `Value::Number(n as f64, Exactness::Exact)`. Отже JSON integer `9007199254740993` міг округлитися, але залишитися позначеним `Exact`.

Виправлений шлях тепер такий:

```text
JSON integer token
      |
      v
arbitrary-precision Rational::from_literal
      |
      v
exact_value()
   /      \
<= 2^53   larger
  |         |
Number     Rational
 Exact      Exact
```

Тому integral JSON numbers тепер мають ту саму losslessness boundary, що й source literals та arithmetic results, включно з integers більшими за i64. Decimal/exponent JSON tokens (`0.1`, `1e3`) лишаються **явно inexact wire-format boundary** у поточному JSON decoder і повертають `Value::Number(..., Exactness::Inexact)`; аудит не маскує цю відмінність.

### Порівняння та identity

Magnitude predicates `<`, `=`, `>` порівнюють усі exact inputs як Rational values і повертають exact `D1 PredicateBit`. Якщо бере участь inexact operand, поточна exact-comparison операція завершується названою `Type` помилкою: вона не виробляє numeric 0/1, `()`, host Bool чи наближену f64-істину. Окрему approximate-comparison операцію можна ратифікувати пізніше, але вона не підміняє exact predicate.

`eq` лишається відношенням equality/identity, визначеним `Value::PartialEq`, і не є заміною numeric magnitude `=`. Не можна зливати ці дві операції лише для спрощення представлення.

### Людський друк і machine read-back

Людське представлення не є machine wire:

- compact exact Number для людини друкується як ціле;
- integer Rational для людини друкує numerator без `/1`;
- fractional Rational для людини друкується як `numerator/denominator`;
- цей human-facing exact-rational view зберігається незалежно від внутрішньої binary-first граматики.

Canonical `write-to-string` для exact integer/rational використовує окремий reader-safe тегований binary wire `#q2:<signed-numerator-bits>/<positive-denominator-bits>`. Тому machine round-trip не залежить від human decimal/rational spelling і не може зіткнутися з голими 8-бітними функціями СЕНС.

Boundary corpus доводить, що велике exact integer проходить `write-to-string -> read -> eval` без втрати magnitude.

### FASL

`crates/my-lisp/src/syntax.rs` має різні FASL tags для `ExprKind::Number` і `ExprKind::Rational`. Number snapshot зберігає всі f64 bits разом із `Exactness`; Rational snapshot зберігає arbitrary-precision numerator і denominator limbs. Чинний `fasl_round_trip_is_byte_identical_and_hash_bound` структурно перевіряє Number і Rational source forms та вимагає byte-identical re-encoding після decode.

Отже FASL зберігає вже прийняте parser-ом числове представлення і не переобчислює exactness через float conversion.

### Typed numeric buffers

Typed buffers — це явна межа narrowing, а не scalar exact arithmetic model:

- `#i32(...)` приймає exact integers і дає `NumericOverflow` поза signed 32-bit range;
- `#f32(...)` навмисно звужує finite numeric values до IEEE-754 binary32. Якщо exact `1/10` стає найближчим f32, це дозволено саме тому, що користувач явно попросив representation `f32`; таке значення не повинно повертатися у scalar arithmetic з тегом `Exact` без окремого semantic conversion.

`crates/my-lisp/tests/exact_number_boundaries.rs` фіксує обидві поведінки.

## Відомі inexact ingress

Поточний code search знаходить створення звичайного `Value::Number(..., Exactness::Inexact)` у вузько визначених місцях:

1. арифметика, де input уже містить inexact value;
2. **decimal/exponent** JSON numeric tokens, які поточний wire-format decoder свідомо інтерпретує через f64; integral JSON tokens відтепер ідуть arbitrary-precision exact path;
3. higher-order bridge для f32-buffer, де buffer elements свідомо подаються callback-у як inexact f64 values.

Source-language decimal literals самі по собі точні: `0.1` означає `1/10`, а не binary64 approximation. JSON `0.1` є окремою boundary policy і наразі inexact.

## Executable evidence

Основний regression/boundary corpus #28: `crates/my-lisp/tests/exact_number_boundaries.rs`.

Він доводить:

- compact exact boundary точно на ±2^53;
- one-past-boundary values залишаються Rational;
- fast-path multiplication не може назвати округлений f64 точним;
- арифметика через Number/Rational representation boundary зберігає magnitude;
- decimal/comma/exponent source literals залишаються exact;
- exact division зберігає reduced fraction і великі integers;
- write/read/eval round-trip зберігає велике exact integer;
- integral JSON numbers використовують ту саму exact compression boundary, включно з arbitrary-precision integers;
- decimal JSON number лишається explicit inexact boundary;
- parser resource limits лишаються названим `NumericOverflow`;
- i32/f32 buffers лишаються явними narrowing boundaries.

Додаткове чинне evidence: parser decimal/resource-limit tests, arbitrary-precision arithmetic tests у `mccarthy.rs`, FASL structural round-trip tests у `syntax.rs`, typed-buffer coverage у `numeric_buffers.rs` та `decimal_comma.rs`.

## Дозволена лексика claim-ів

Рекомендоване формулювання:

> **Точна арифметика ніколи не округлює мовчки. Runtime може використовувати `f64` як компактне представлення лише для математично точних цілих у його exact range; більші або дробові exact values використовують arbitrary-precision `Rational`.**

Також коректно:

- «my-lisp має arbitrary-precision exact integers і rationals»;
- «source decimal literals є точними»;
- «integral JSON numbers зберігаються точно, незалежно від i64/f64 range»;
- «inexact arithmetic стає явною після входження inexact value у computation».

Не варто стверджувати без зміни implementation:

- «усі числа — Rational»;
- «my-lisp не використовує floats»;
- «кожна numeric boundary є exact» — typed f32 buffers та decimal/exponent JSON numbers навмисно мають inexact boundaries.

## Stop condition

Будь-який майбутній шлях, що створює `Value::Number(_, Exactness::Exact)` з integer без доказу належності до binary64 exact-integer range, є semantic regression навіть тоді, коли Rust integer calculation сам по собі не overflow-нув.
