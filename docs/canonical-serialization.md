# Canonical serialization · Канонічна серіалізація · Kanonische Serialisierung

> **Scope note (2026-10-03):** цей документ визначає канонічне представлення/ідентичність **серіалізованого data content** у своєму wire domain. Він не визначає глобальну SENS semantic identity. Поточна загальна онтологія: `binary object + exact semantic domain + admitted law` — див. [`CURRENT.md`](../CURRENT.md) і #2490.

## Українська

`write-to-string` визначає незалежний від реалізації machine data wire format СЕНС і навмисно відділений від людського представлення. Для кожного значення із серіалізованого домену `read(write-to-string(value))` структурно `equal?` до `value`, а рівні значення дають побайтово однаковий wire-текст. Виконуване джерело істини — Tier-2 блок “Canonical serialization law” у [`tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp), а не Rust `Display`.

Домен: `()`/`t`, читабельні символи, рядки, пари (proper і dotted lists), точні цілі та скорочені раціональні числа, скінченні неточні числа. Замикання, макроси, TCP handles та інші живі capabilities навмисно поза ним: діагностичні форми на кшталт `<lambda>` не є даними й не мають зберігатися чи передаватися.

- `()` і `t` представляють false/nil та true; символ використовує свій читабельний token.
- Рядок береться в лапки. Quote, backslash, newline і tab екрануються як `\"`, `\\`, `\n` і `\t`; інші Unicode scalar values лишаються буквальними.
- Proper list має дужки й один ASCII-пробіл між елементами: `(a b c)`. Неправильний хвіст має по одному пробілу навколо крапки: `(a b . c)`.
- Точні цілі та rational у machine wire мають теговану двійкову форму `#q2:<signed-numerator-bits>/<positive-denominator-bits>`. Дріб скорочений, нуль канонічно `0`, величини не мають початкових нулів. Приклади: 42 → `#q2:101010/1`, 1/2 → `#q2:1/10`, -5/4 → `#q2:-101/100`. Тег відділяє numeric wire від голих 8-бітних функцій СЕНС. Людське представлення лишається `42`, `1/2`, `-5/4`.
- Скінченне неточне число використовує найкоротшу сумісну з reader десяткову форму, що зберігає представлене значення. Ціле неточне значення зберігає одну дробову цифру (`3.0`), тому exactness не стирається.

Саме цей текст — не Rust layout і не digest-алгоритм — є канонічною **content identity у цьому serialization/data domain**. `knowledge-content-address` та `world-content-address` використовують його напряму. Це не замінює глобальне правило SENS `binary object + domain + law`. Software- чи FPGA-adapter може хешувати UTF-8 bytes для передачі, але спочатку має збігтися канонічний текст.

---

## English

`write-to-string` defines SENS's implementation-independent machine data wire format. It is deliberately distinct from human presentation. For every value in the serializable domain, `read(write-to-string(value))` is structurally `equal?` to `value`, and equal values produce byte-for-byte equal wire text. The executable authority is the Tier-2 “Canonical serialization law” block in [`tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp), not Rust's `Display` implementation.

The domain is `()`/`t`, readable symbols, strings, pairs (proper and dotted lists), exact integers and reduced rationals, and finite inexact numbers. Closures, macros, TCP handles, and other live capabilities are deliberately outside it: diagnostic forms such as `<lambda>` are not data and must not be persisted or exchanged.

- `()` and `t` represent false/nil and true; symbols use their readable token.
- Strings are quoted. Quote, backslash, newline, and tab are escaped as `\"`, `\\`, `\n`, and `\t`; other Unicode scalar values remain literal.
- Proper lists use parentheses and one ASCII space between items: `(a b c)`. An improper tail uses one space on each side of the dot: `(a b . c)`.
- Exact integers and rationals use a tagged base-2 machine form: `#q2:<signed-numerator-bits>/<positive-denominator-bits>`. The fraction is reduced, zero is canonical `0`, and magnitudes have no leading zeros. Examples: 42 → `#q2:101010/1`, 1/2 → `#q2:1/10`, -5/4 → `#q2:-101/100`. The tag keeps numeric wire values disjoint from bare eight-bit SENS function tokens. Human presentation remains `42`, `1/2`, `-5/4`.
- Finite inexact numbers use the shortest reader-compatible decimal form that preserves the represented value. A whole inexact value retains one fractional digit (`3.0`), so exactness is never erased.

This text—not a Rust layout or digest algorithm—is canonical **content identity inside this serialization/data domain**. `knowledge-content-address` and `world-content-address` use it directly. It does not replace the global SENS rule `binary object + domain + law`. Software or FPGA adapters may hash its UTF-8 bytes for transport, but canonical text must match before hashing.

---

## Deutsch

`write-to-string` definiert my-lisps implementierungsunabhängiges Datenformat. Für jeden Wert im serialisierbaren Bereich ist `read(write-to-string(value))` strukturell `equal?` zu `value`, und gleiche Werte erzeugen bytegleich denselben Text. Die ausführbare Autorität ist der Tier-2-Block „Canonical serialization law“ in [`tests/fixtures/conformance.lisp`](../tests/fixtures/conformance.lisp), nicht Rusts `Display`-Implementierung.

Der Bereich umfasst `()`/`t`, lesbare Symbole, Strings, Paare (echte und Dotted Lists), exakte Ganzzahlen und gekürzte rationale Zahlen sowie endliche inexakte Zahlen. Closures, Makros, TCP-Handles und andere lebende Capabilities liegen bewusst außerhalb: Diagnoseformen wie `<lambda>` sind keine Daten und dürfen weder gespeichert noch ausgetauscht werden.

- `()` und `t` stehen für falsch/NIL und wahr; Symbole verwenden ihr lesbares Token.
- Strings stehen in Anführungszeichen. Quote, Backslash, Zeilenumbruch und Tabulator werden als `\"`, `\\`, `\n` und `\t` escaped; andere Unicode-Skalarwerte bleiben wörtlich.
- Echte Listen verwenden Klammern und genau ein ASCII-Leerzeichen zwischen Elementen: `(a b c)`. Ein unechter Schwanz verwendet je ein Leerzeichen um den Punkt: `(a b . c)`.
- Exakte Ganzzahlen und rationale Zahlen verwenden im Machine-Wire eine markierte Binärform: `#q2:<signed-numerator-bits>/<positive-denominator-bits>`. Der Bruch ist gekürzt, Null ist kanonisch `0`, und Beträge haben keine führenden Nullen. Beispiele: 42 → `#q2:101010/1`, 1/2 → `#q2:1/10`, -5/4 → `#q2:-101/100`. Das Tag trennt numerische Wire-Werte von nackten acht-Bit-SENS-Funktionstokens. Die menschliche Darstellung bleibt `42`, `1/2`, `-5/4`.
- Endliche inexakte Zahlen verwenden die kürzeste reader-kompatible Dezimalform, welche den dargestellten Wert erhält. Ein ganzzahliger inexakter Wert behält eine Nachkommastelle (`3.0`), sodass Exaktheit nie verloren geht.

Dieser Text—nicht ein Rust-Layout oder Digest-Algorithmus—ist die kanonische **Inhaltsidentität innerhalb dieses Serialisierungs-/Datendomänenkontexts**. `knowledge-content-address` und `world-content-address` verwenden ihn direkt. Er ersetzt nicht die globale SENS-Regel `binary object + domain + law`. Software- oder FPGA-Adapter dürfen seine UTF-8-Bytes für den Transport hashen; zuerst muss jedoch der kanonische Text übereinstimmen.
