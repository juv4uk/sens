# Таблиця Core1: наш SID проти функцій Маккартні (1960) та Lisp 1.5 (1962)

**Це людино-читний переклад, не нова влада.** Єдине джерело істини —
`contracts/core1-historical-sid-map.lisp`, механічно звірене CI
(`.github/workflows/core1-historical-sid-map.yml`) проти закріпленого
коміту `juv4uk/mccarthy-eval` (`1ae9745b66a1439c1929b0d9038c680567118a58`).
Якщо цей файл і `.lisp`-контракт колись розійдуться — вірити `.lisp`.

Статус: **source-confirmed** (прочитано напряму з контракту й CI-скрипту,
не виконувалось у цій сесії).

## Напрямок відповідності — лише в один бік

```
наш SID (my-lisp) + Core1-профіль закону  ->  визнаний історичний механізм
```

**Ніколи навпаки**: історична назва чи реалізація нічого не диктує нашій
семантиці. Історична назва не може "видати" новий SID
(`historical-name-may-mint-sid: no`).

## Що означають колонки

- **fit** (тип відповідності):
  - `direct` — історичний механізм і є природним для Core1;
  - `value-adapter` — лише адаптація представлення/поверхні, закон Core1 не змінюється;
  - `closure-adapter` — історичний FUNCTION/FUNARG дає механізм замикання для Core1;
  - `surface-adapter` — відрізняється лише поверхневий синтаксис/угода виклику;
  - `profile-support` — історичний допоміжний механізм евалюатора, підтримує Core1, але не є публічною ідентичністю.
- **статус у Core1**:
  - `admitted` — реально використовується в поточному бутстрапі Core1;
  - `support` — внутрішній механізм, що стоїть за admitted-поведінкою;
  - `available-not-admitted` — історично існує, але поточний бутстрап його не вимагає.

## Таблиця відповідності

| SID | наша назва | історична назва | джерело | fit | статус у Core1 |
|---|---|---|---|---|---|
| `00000000` | `empty-list` | `NIL` | mccarthy-1960 | direct | admitted |
| `00000001` | `quote` | `QUOTE` | mccarthy-1960 | direct | admitted |
| `00000010` | `atom` | `ATOM` | mccarthy-1960 | direct | admitted |
| `00000011` | `eq` | `EQ` | mccarthy-1960 | direct | admitted |
| `00000100` | `cons` | `CONS` | mccarthy-1960 | direct | admitted |
| `00000101` | `car` | `CAR` | mccarthy-1960 | direct | admitted |
| `00000110` | `cdr` | `CDR` | mccarthy-1960 | direct | admitted |
| `00000111` | `cond` | `COND` | mccarthy-1960 | direct | admitted |
| `00001000` | `lambda` | `LAMBDA` | mccarthy-1960 | closure-adapter | admitted |
| `00001001` | `define` | `DEFINE` | lisp-i-1960 | surface-adapter | admitted |
| `00001011` | `def` | `DEFINE` | lisp-i-1960 | surface-adapter | admitted |
| `10101010` | `label` | `LABEL` | mccarthy-1960 | direct | admitted |
| `00001100` | `+` | `PLUS` | lisp15-1962 | direct | available-not-admitted |
| `00001101` | `-` | `DIFFERENCE` | lisp15-1962 | surface-adapter | available-not-admitted |
| `00001110` | `*` | `TIMES` | lisp15-1962 | direct | available-not-admitted |
| `00010001` | `min` | `MIN` | lisp15-1962 | direct | available-not-admitted |
| `00010010` | `max` | `MAX` | lisp15-1962 | direct | available-not-admitted |
| `00010011` | `mod` | `REMAINDER` | lisp15-1962 | surface-adapter | available-not-admitted |
| `00010100` | `quotient` | `QUOTIENT` | lisp15-1962 | direct | available-not-admitted |
| `00011010` | `<` | `LESSP` | lisp15-1962 | direct | available-not-admitted |
| `00011011` | `>` | `GREATERP` | lisp15-1962 | direct | available-not-admitted |
| `00100001` | `not` | `NOT` | lisp15-1962 | direct | admitted |
| `00100010` | `equal?` | `EQUAL` | lisp15-1962 | direct | available-not-admitted |
| `00100111` | `list` | `LIST` | lisp15-1962 | direct | admitted |
| `00101000` | `length` | `LENGTH` | lisp15-1962 | direct | available-not-admitted |
| `00101001` | `append` | `APPEND` | mccarthy-1960 | direct | support |
| `00101010` | `reverse` | `REVERSE` | lisp15-1962 | direct | available-not-admitted |
| `00101100` | `member?` | `MEMBER` | lisp15-1962 | direct | available-not-admitted |
| `00101101` | `assoc` | `assoc` | mccarthy-1960 | profile-support | support |
| `00101110` | `pair` | `PAIR` | mccarthy-1960 | profile-support | support |
| `01001101` | `eval` | `eval` | mccarthy-1960 | profile-support | support |
| `10011010` | `and` | `AND` | lisp15-1962 | direct | available-not-admitted |
| `10011011` | `or` | `OR` | lisp15-1962 | direct | available-not-admitted |

## Історичні механізми без нашого SID

`LABEL` раніше був у цьому списку. 2026-09-26 власник вирішив дати йому
SID `10101010` (іменована рекурсія Маккартні 1960): ядро `mccarthy-eval`
`6031f926` розпізнає LABEL за цим кодом, а Core1 записаний ним. Тепер це
рядок таблиці вище, `direct` / `admitted`.

Ці механізми існують у `mccarthy-eval`, але **свідомо не отримали** свого
SID у my-lisp — вони лишаються суто механізмом евалюатора, не публічною
ідентичністю мови:

| механізм | джерело | роль |
|---|---|---|
| `apply` | mccarthy-1960 | внутрішня підтримка евалюатора |
| `appq` | mccarthy-1960 | внутрішня підтримка евалюатора |
| `evcon` | mccarthy-1960 | внутрішня підтримка евалюатора |
| `evlis` | mccarthy-1960 | внутрішня підтримка евалюатора |
| `FUNCTION` | lisp15-1962 | конструктор замикання |
| `FUNARG` | lisp15-1962 | застосування із захопленим середовищем |
| `T` | mccarthy-1960 | історичне контрольне значення |

CI (`Verify mechanism-only names did not acquire SIDs`) окремо перевіряє,
що жоден з цих механізмів не отримав власної англійської назви в
`lib/surface/semantic-registry.lisp` — це не забуте, а навмисне рішення.

## Ключове правило (звідки Core1 бере закон "T/NIL")

`(profile-selects-law . core1)` + `(core1-result-domain . historical-t-nil)`:
Core1 навмисно використовує саме історичний T/NIL-орієнтований закон
Маккартні 1960-х там, де це застосовно. Пізніші результат-записи Core4
(`identity-relation`, `structural-kind` тощо) до цього профілю не
проєктуються (`core4-result-records-in-core1: forbidden`) — це і є той
самий принцип, через який тричастинний `cond` (Contract 7/8-стиль)
Core1-у не потрібен: Core1 навмисно сумісний із класичною семантикою
Маккартні 1960-х, а не з пізнішим Contract 8/Canon.

## Провенанс

- Контракт: `contracts/core1-historical-sid-map.lisp`
- CI-звірка: `.github/workflows/core1-historical-sid-map.yml`
- Закріплений історичний репозиторій: `juv4uk/mccarthy-eval`
  @ `1ae9745b66a1439c1929b0d9038c680567118a58`
- Цей файл: `docs/core1-historical-sid-map.uk.md`, лише переклад —
  за розбіжності відповідає `.lisp`-контракт.
