# #2071 — bīja3 epistemic kernel, перший синтез

Статус: лише research. Це не ратифікує bīja3 minimality або production authority.

## Порядок фундаменту

Kernel стоїть над Foundation-0 #2077:

    exact bounded word
        -> intrinsic bits/width/boundary facts
        -> semantic evidence kernel
        -> self-description / execution / compiler

Bits і width не дублюються як semantic facts.

## Вісім рядків kernel

Кожна D3 address лишається `address_status = premise`.

| word | abstract capability | current evidence strength |
|---|---|---|
| 000 | ground role | exact `()` representative = premise; necessity open |
| 001 | evaluation suppression | capability supported; packaging as seed open |
| 010 | atom/pair classification | bounded lower-bound support; still open |
| 011 | atomic identity observer | bounded support; active alternative-basis attack |
| 100 | pair constructor | bounded fresh-structure lower-bound support |
| 101 | left projection | strongest current structural support |
| 110 | right projection | strongest current structural support |
| 111 | conditional evaluation control | capability supported; packaging/minimality open |

Заборонений висновок: same width -> same semantic kind -> same proof strength.

## Intrinsic vs semantic

Checker механічно виводить exact bits, width=3, distinctness і padded form. Це не semantic meaning.

Kernel зберігає тільки evidence-bearing capability claims та epistemic state.

## Remove-one discipline

Для кожного seed видаляємо semantic-evidence row:

    explain(removed-word) -> UNKNOWN

Заборонені fallbacks: human name, numeric order, Hamming neighborhood, zero-padded legacy function, width-based role, prefix geometry.

Усі 8 checks PASS. Це fail-closed discipline, не global mathematical irreducibility.

## Критичний виняток 000

Current Contract 10 каже, що `()` є structural data поза function space, а function `00000000` не є `()`.

Тому `000 -> 00000000` не може бути meaning-preserving legacy projection для candidate D3 ground word.

Kernel фіксує:
- exact `()` representative = premise;
- `00000000` = лише mechanical padded form;
- semantic compatibility projection = forbidden.

Для `001..111` zero-padded legacy forms можна тестувати як compatibility mechanism candidates, але вони лишаються distinct exact identities.

## Наслідок для #2081

D3 shadow adapter не може бути однаковим:

    001..111 -> checked legacy mechanism projection може бути придатною
    000      -> structural-ground oracle, ніколи current function 00000000 як ()

## Принцип

**Зберігати claim тільки в тій силі, яку реально заробило evidence; решту виводити, а unknown лишати unknown.**