# F3M-5λ: nameless LAMBDA через de-Bruijn references

Дата: 12.10.2026.

## Мета

Перевірити, чи можна в рівно **5 фізичних байтів / 40 біт** мати замкнений
canonical micro-space, який зберігає весь чинний D1–D3 basis і додає справжню
одноаргументну `LAMBDA`, не вводячи прихованого текстового параметра на кшталт
`x`.

## Представлення

Binder не має імені. Тіло використовує lexical reference:

- `BOUND(0)` — найближчий binder;
- `BOUND(1)` — наступний зовнішній binder;
- `BOUND(n)` допустимий лише коли `n < lexical_depth`.

Тому α-equivalent терми

`λx.x`, `λy.y`, `λfoo.foo`

мають одну канонічну форму:

`λ.BOUND(0)`.

Це відповідає стандартному nameless/de-Bruijn представленню lambda-термів і
природно підходить для combinatorial counting/ranking closed terms.

## Canonical 5-byte witnesses

| Терм | De-Bruijn форма | payload |
|---|---|---|
| I | `λ.0` | `00 00 00 00 00` |
| K | `λ.λ.1` | `00 00 00 00 10` |
| KI | `λ.λ.0` | `00 00 00 00 0F` |

Beta-перевірки:

- `I a = a`;
- `K a b = a`;
- `KI a b = b`.

Усі три пройшли на власному nameless evaluator кандидата.

## Ємність і rank/unrank

Кандидат enumerates лише **closed** terms і відрізняє legacy-state від
extension-state. F3M-1..4 не перенумеровуються.

- capacity: `2^40 = 1 099 511 627 776`;
- cumulative closed extension space through 12 nodes:
  `298 460 447 325`;
- through 13 nodes: `3 706 360 960 907`.

Отже повне 40-бітне вікно заповнюється всередині 13-node layer.

Proof run **38242173136 — SUCCESS** перевірив boundary values та **65 536
deterministic stratified** payloads по всьому 40-бітному інтервалу.
Це не exhaustive sweep усіх `2^40` термів.

## All-basis witness

Payload:

`05 61 69 CB 4A`

декодується у:

`IF-ATOM(EQ(ATOM(λ.BOUND(0)),ATOM(QUOTE(1))),CAR(CONS(QUOTE(0),CDR(CONS(QUOTE(1),QUOTE(NIL))))),QUOTE(NIL))`

Він має **11 micro-nodes** і містить усі capability-класи:

`QUOTE + ATOM + CONS + CAR + CDR + EQ + COND + LAMBDA`.

## Семантична межа

Це **research candidate**, не друге трактування production F3M-5.

Причина: `BOUND(n)` уже має математично точну lexical семантику в кандидатові,
але ще не має окремо ратифікованої exact SENS-domain identity. F3M є carrier,
а не окремою мовою, тому production codec не повинен породжувати semantic
constructor, якого немає в canonical SENS.

Наступний контрактний крок — визначити **lexical-reference law**:

`BOUND(n) = посилання на n-й binder назовні, 0 = найближчий`.

Тільки після цього кандидат можна розглядати як заміну/наступника чинного
F3M-5 mapping.

## Дослідницькі донори

- Grygiel, Lescanne, *Counting and generating lambda terms* — closed lambda
  enumeration через de-Bruijn indices.
- Tarau, *A Logic Programming Playground for Lambda Terms, Combinators,
  Types and Tree-based Arithmetic Computations* — compressed de-Bruijn
  representations та ranking/unranking.
- Bodini, Gittenberger, Gołębiewski, *Enumerating Lambda Terms by Weighted
  Length of Their De Bruijn Representation* — combinatorics binary/de-Bruijn
  lambda encodings.
