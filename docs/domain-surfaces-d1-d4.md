# Українська і санскритська поверхні D1–D4

Цей зріз задає **людські проєкції**, а не семантичні ідентичності.

```text
людське слово
    ↓
точний domain + точні bits
    ↓
чинний закон домену
```

Джерело машинної проєкції: `lib/surface/domain-surfaces-d1-d4.lisp`.
Guard: `python3 scripts/check-domain-surfaces-d1-d4.py`.
Перекладач: `scripts/translate-domain-program.py`.

Стара плоска 8-бітна surface-таблиця не є джерелом адрес. Із неї дозволено
брати лише вже перевірені слова як лексичний донор.

## Використання перекладача

```bash
python3 scripts/translate-domain-program.py --from en --to uk program.lisp
python3 scripts/translate-domain-program.py --from uk --to sa program.lisp
python3 scripts/translate-domain-program.py --from sa --to en program.lisp
python3 scripts/translate-domain-program.py --self-test
```

Перекладач змінює лише зареєстровані D1/D3/D4 source-слова. Коментарі,
рядки, користувацькі імена та D2 display-labels не перекладаються як код.

## D1

| bits | значення | українська | sa (IAST) |
|---|---|---|---|
| 0 | NO | `ні` | `na` |
| 1 | YES | `так` | `ām` |

## D2

D2 є структурою. Слова нижче — **display labels**, а не новий текстовий синтаксис:
людські дужки/крапка/пропуск і далі знижуються у точні D2 bits.

| bits | роль | українська | sa (IAST) |
|---|---|---|---|
| 00 | separator | `пропуск` | `antarāla` |
| 01 | close | `закрити` | `samāpana` |
| 10 | open | `відкрити` | `udghāṭana` |
| 11 | dot | `крапка` | `bindu` |

## D3

| bits | resident | українська | sa (IAST) |
|---|---|---|---|
| 000 | EMPTY | `порожнє` | `śūnya` |
| 001 | QUOTE | `як-є` | `svarūpa` |
| 010 | ATOM | `атом?` | `aṇu?` |
| 011 | CDR | `решта` | `śeṣa` |
| 100 | CAR | `перше` | `ādi` |
| 101 | EQ | `тотожне?` | `abheda?` |
| 110 | COND | `за-умовою` | `krama` |
| 111 | CONS | `сполучити` | `saṃyuj` |

## D4

| bits | resident | українська | sa (IAST) |
|---|---|---|---|
| 0000 | APPLY | `застосувати` | `prayoga` |
| 0001 | EVAL | `обчислити` | `vicāraṇa` |
| 0010 | LAMBDA | `функція` | `phalana` |
| 0011 | DEFINE | `визначити` | `nirvacana` |
| 0100 | NOT | `не` | `niṣedha` |
| 0101 | NULL | `порожнє?` | `śūnya?` |
| 0110 | CDAR | `решта-від-першого` | `śeṣa-ādi` |
| 0111 | CDDR | `решта-від-решти` | `śeṣa-śeṣa` |
| 1000 | CAAR | `перше-від-першого` | `ādi-ādi` |
| 1001 | CADR | `перше-від-решти` | `ādi-śeṣa` |
| 1010 | LOOKUP | `знайти` | `anveṣaṇa` |
| 1011 | BIND | `зв'язати` | `bandha` |
| 1100 | EVCON | `обчислити-умови` | `krama-vicāraṇa` |
| 1101 | EVLIS | `обчислити-список` | `śreṇī-vicāraṇa` |
| 1110 | LIST | `список` | `śreṇī` |
| 1111 | APPEND | `приєднати` | `saṅkalana` |

## Один зміст трьома поверхнями

Англійська:

```lisp
(define f (lambda (x) (car x)))
```

Українська:

```lisp
(визначити f (функція (x) (перше x)))
```

Санскритська IAST:

```lisp
(nirvacana f (phalana (x) (ādi x)))
```

У всіх трьох випадках зареєстровані слова мають знизитися до однакової
послідовності semantic heads:

```text
D4:0011 DEFINE
D4:0010 LAMBDA
D3:100  CAR
```

Користувацькі символи `f` та `x` не перекладаються.

## Статус санскриту

Стабільні історично перевірені донори D3 (`svarūpa`, `aṇu`, `śeṣa`,
`ādi`, `abheda`, `krama`, `saṃyuj`) перенесені тільки як surface-слова.
Нові D4 назви позначені у machine table як `candidate` або `generated`:
це дозволяє лексичне рецензування без зміни жодного біта чи семантичного закону.
