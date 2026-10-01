# #2106 — Foundation−1: binary substrate до meaning

Статус: лише research. Жодного production або contract authority transfer.

## Результат

Поточні layer-0 assumptions розкладаються на слабший neutral carrier і додаткові semantic orientations.

### Neutral carrier candidate

```text
alphabet cardinality = 2
word = finite ordered bit sequence
word boundary = explicit relation outside payload bits
meaning = absent until separately admitted
```

Проєкт може й далі писати два carrier symbols як `0` і `1`, але сам carrier не прикріплює до цих labels NO/YES або structural meaning.

## 1. Global bit-flip symmetry

Для всіх words widths 0..5 witness перевіряє 3969 пар.

Під global complement `0 <-> 1` зберігаються:
- width;
- equality/non-equality;
- prefix relation;
- concatenation.

Отже bare carrier не має внутрішньої орієнтації між двома symbols.

### Наслідок для D1

`0=NO, 1=YES` може лишатися admitted PredicateBit law, але це **додаткова semantic orientation**, а не theorem binary storage.

## 2. Exact codes racanā2 не виводяться лише з role inventory

Abstract roles:

```text
sep, open, close, dot
```

2-bit codewords:

```text
00, 01, 10, 11
```

Усі `4! = 24` bijections однаково правильно encode/decode abstract role sequences.

Тому current mapping:

```text
00 -> sep
10 -> open
01 -> close
11 -> dot
```

не випливає лише з four-role grammar.

Це не спростовує racanā2. Це означає, що exact code assignment потребує незалежного law/evidence, якщо ми хочемо підняти його вище premise.

## 3. Неможливість raw in-band delimiter

Для кожного non-empty delimiter width 1..8 — всього `510` кандидатів — сам delimiter є допустимим binary payload і може траплятися всередині більшого payload.

Тому за умови arbitrary finite binary words:

> жоден fixed unescaped bit pattern не може бути універсальним word delimiter.

Boundary потребує framing, escaping, out-of-band structure, length information або іншого mechanism поза raw substring scanning.

Повне structural word `00` тому не тотожне substring `00` усередині довшого слова.

## 4. Epsilon лишається open

Обидві carrier models внутрішньо послідовні:

```text
{0,1}*   містить epsilon і має concatenation identity
{0,1}+   виключає epsilon
```

Обидві зберігають positive-word laws, потрібні Foundation-0.

Отже `epsilon forbidden` не виводиться з neutral carrier.

#2077 уже послаблено: epsilon механічно round-trip-иться, але semantic admission лишається unresolved.

## Proposed epistemic split для #2018

```text
binary alphabet cardinality=2          premise / owner design choice
carrier 0<->1 symmetry                 witness
PredicateBit 0=NO,1=YES                semantic premise/witness, не carrier law
explicit boundary vs payload           theorem за arbitrary-word + no-escape assumptions
racanā2 abstract role inventory        premise
racanā2 exact code assignment          premise; не derived role grammar
epsilon semantic admission             unknown
```

## Новий фундаментальний stack

```text
Foundation−1: neutral binary carrier + explicit boundaries
Foundation 0: exact bounded word identity
Foundation 1: semantic admission / evidence
Foundation 2: proof / relation laws
Foundation 3: execution mechanisms
```

## Принцип

**Carrier дає розрізнення й порядок; semantics дає орієнтацію та meaning.**