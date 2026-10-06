# D9 surface harvest v1 — 57 публічних signatures

**Статус:** research / unratified  
**Issue:** #3977  
**Foundation:** #3960 / Contract 11.7

Джерело: `lib/surface/function-signatures.lisp`.

Старі 8-бітні registry-коди з цього файлу **не використовуються як D9 coordinates**. У harvest переноситься лише language-visible назва, doc і рішення semantic review.

## Результат

```text
public signatures                    57
SELECT-D9-CANDIDATE                  20
LOWER-DOMAIN-OR-SURFACE-PROJECTION   30
HOLD-SEMANTIC-REVIEW                  7
---------------------------------------
D9 selected total                   168/512
law-forced coordinates              128
unplaced selected                    40
remaining                           344
ratified D9 residents                 0
```

## Нові 20 meanings

```text
NUMERIC-EQUALITY

STRINGP
STRING-APPEND
STRING-LENGTH
STRING-EMPTY?
STRING-PREFIX?
STRING-CONTAINS?
STRING-FIRST
STRING-REST
STRING-SLICE

READ-ALL

NUMERIC-BUFFERP
I32-BUFFER
F32-BUFFER
NUMERIC-BUFFER-TYPE
NUMERIC-BUFFER-LENGTH
NUMERIC-BUFFER-REF
NUMERIC-BUFFER-MAP

JSON-PARSE
SHA256-HEX
```

Вони всі входять у D9 inventory **без координат**.

## 30 lower-domain / surface projections

Сюди потрапляють чинні D3/D4/D5/D6/D8 semantics та surface aliases/arity dispatch: `quote`, `atom?`, `eq?`, `cons`, `car`, `cdr`, `cond`, `lambda`, `define`, `def`, арифметичні `+ - * / < >`, `string<?`, reader/writer/vector surface та інші вже admitted meanings.

Важлива деталь: `-` і `/` — не нові residents лише через те, що одна surface форма dispatch-ить між кількома вже admitted lower semantics.

## HOLD 7

```text
defmacro
codepoint->string
string->codepoint
mono-ns
unix-time-now
ntp-query-raw
timezone-declarations-raw
```

Причини різні:
- `defmacro` потребує точного зіставлення з D5 MACRO + D4 DEFINE;
- codepoint pair може дублювати D8 CODE-CHAR / CHAR-CODE залежно від character representation;
- time/NTP/TZ — language-visible host observations, але потребують абстрактного semantic law незалежно від конкретного host mechanism.

## Принцип

```text
public API != automatic new resident
public API + distinct language-visible law -> D9 candidate
```

І навіть після SELECT:

```text
meaning selected != coordinate assigned
```
