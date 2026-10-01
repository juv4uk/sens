# #1962 — semantic spacing vs raw-wire framing

**Статус:** research-only. Не змінює reader/runtime/contract.

## Чому це окреме питання

Поточна графова модель власника має:

```text
uttara1
  0  NO
  1  YES

racanā2
  00  separator / space
  01  )
  10  (
  11  .

bīja3
  000  ()
  001  QUOTE
  010  ATOM
  011  EQ
  100  CONS
  101  CAR
  110  CDR
  111  COND
```

Приклад source-проєкції:

```text
10 0001 01
```

Пробіли тут задають **межі binary words**. Саме тому слово `0001` не
конфліктує з коротшими `00`, `0`, `01` тощо.

Але це ще не означає, що raw concatenated wire можна отримати простим
видаленням пробілів.

## Три різні шари

```text
semantic identity
    ↓
token/source grammar
    ↓
wire framing
```

Не можна вимагати, щоб один і той самий механізм одночасно виконував усі
три ролі.

### 1. Semantic identity

`00` означає структурний separator. `11` означає dot. Це закон мови.

### 2. Source/token grammar

У людській/текстовій binary projection реальний whitespace є межею слова:

```text
10 0001 01
```

Лексер уже знає три слова `10`, `0001`, `01`. Внутрішні `00` у `0001`
не є separator-ами.

Тобто `racanā2/00` можна розуміти як **семантичну тотожність relation
"word boundary"**, а ASCII/Unicode blank є лише surface-проєкцією цієї
межі. Немає вимоги друкувати додаткове literal `00` між кожною парою слів.

### 3. Raw binary wire

У raw bitstream зовнішнього whitespace немає. Отже межу слова треба
перевезти **transport metadata**, не крадучи один із кодів `racanā2`.

Це особливо важливо, бо current main має інший Control2:

```text
00 space
01 close
10 open
11 escape
```

а owner model тепер використовує:

```text
11 dot
```

Тому старий `11 = escape` не можна просто залишити мовним законом: він
конфліктує з повним `racanā2`.

## Candidate transport: Width3 + escape

Для research пропонується найпростіший зовнішній frame, який не змінює
semantic word:

```text
header  meaning
000     next word has 1 bit
001     next word has 2 bits
010     next word has 3 bits
011     next word has 4 bits
100     next word has 5 bits
101     next word has 6 bits
110     next word has 7 bits
111     extended width (>=8)
```

Для `>=8` після `111` іде Elias-gamma для `width-7`.

Це **не новий domain** і не частина ontology. Це лише transport frame.

Для width 8:

```text
111 1 <8 payload bits>
```

тобто 12 wire bits — рівно стільки, скільки current
`11 + function-type-00 + Function8`.

Для width 3:

```text
010 <3 payload bits>
```

= 6 wire bits.

Для width 4:

```text
011 <4 payload bits>
```

= 7 wire bits.

## Separator на wire

Коли кожен semantic word має зовнішню length frame, окремий wire-space
між словами не потрібний: boundary already exists physically.

Тобто:

```text
source:  10 0001 01
tokens:  [10] [0001] [01]
wire:    [001 10][011 0001][001 01]
```

Raw wire:

```text
00110011000100101
```

декодується однозначно назад у:

```text
10 | 0001 | 01
```

а source renderer знову показує:

```text
10 0001 01
```

Таким чином `00 = separator` лишається **мовною структурою**, але raw
transport не шукає substring `00` усередині payload.

## Важливий наслідок

Graph/prefix compression і wire framing стають ортогональними:

```text
semantic prefix:
101 -> 1010 / 1011
CAR -> CAAR / CADR

transport:
word length -> payload boundary
```

Transport не має права вирішувати, що означає prefix. Prefix graph не
має права покладатися на in-band wire delimiter.

## Falsification / acceptance

До production migration:

- [ ] source parser round-trips arbitrary words containing `00/01/10/11`;
- [ ] raw-wire decoder round-trips arbitrary word sequences without whitespace;
- [ ] `racanā2 11 = dot` не конфліктує з transport escape;
- [ ] full wire cost рахується окремо від semantic identifier width;
- [ ] existing Control2 framing лишається historical/current donor, а не
      автоматично переноситься в нову ontology.

## Поточний висновок

Review-заперечення про raw `00` delimiter правильне **для голого
concatenated bitstream**, але воно не руйнує variable-width language.

Воно показує точну межу:

> **space is a language/token boundary; raw-wire framing is an external
> transport problem.**

Цю межу треба зберегти так само строго, як semantic/runtime boundary.
